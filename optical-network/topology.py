"""The four-ROADM optical line and its process lifecycle.

This module needs Mininet and the optical emulator installed, and root, because
it builds real network namespaces. Everything else in this package talks to the
running line over HTTP instead, so ``configure``, ``monitor`` and ``status``
work from an ordinary environment.

The line is fixed: one channel, one direction of cross-connects, no alternate
lightpath. That is a deliberate property of the fixture, not an omission -- a
domain that owns this line can validate it, report on it, or refuse to carry a
service over it, but it cannot reroute around a cut.
"""

from __future__ import annotations

import signal
import socket
import threading
from typing import Callable

from mininet.clean import cleanup
from mininet.log import setLogLevel
from mininet.node import OVSBridge
from mininet.topo import Topo
from mnoptical.dataplane import (
    OpticalLink,
    OpticalNet,
    ROADM,
    Terminal,
    dB,
    dBm,
    km,
)
from mnoptical.rest import RestServer

import packet_bridge
from spec import (
    BOOST_GAIN_DB,
    CLIENT_EDGE,
    CLIENT_TERMINAL,
    LAUNCH_POWER_DBM,
    REST_HOST,
    REST_PORT,
    ROADMS,
    ROADM_ADD_DROP_PORT,
    ROADM_EAST_PORT,
    ROADM_INSERTION_LOSS_DB,
    ROADM_WEST_PORT,
    SERVER_EDGE,
    SERVER_TERMINAL,
    SPAN_AMP_GAIN_DB,
    SPAN_KM,
    TERMINAL_ETH_PORT,
    TERMINAL_WDM_PORT,
)

SPAN = SPAN_KM * km
AMP_GAIN = SPAN_AMP_GAIN_DB * dB
BOOST = BOOST_GAIN_DB * dB


class FourRoadmTopo(Topo):
    """clientEdge - t-client = r1 = r2 = r3 = r4 = t-server - serverEdge"""

    def build(self) -> None:
        client_edge = self.addHost(CLIENT_EDGE)
        server_edge = self.addHost(SERVER_EDGE)

        transceivers = [("tx1", LAUNCH_POWER_DBM * dBm, "C")]
        t_client = self.addSwitch(
            CLIENT_TERMINAL, cls=Terminal, transceivers=transceivers, monitor_mode="in"
        )
        t_server = self.addSwitch(
            SERVER_TERMINAL, cls=Terminal, transceivers=transceivers, monitor_mode="in"
        )
        roadms = [
            self.addSwitch(
                name,
                cls=ROADM,
                monitor_mode="out",
                insertion_loss_dB=ROADM_INSERTION_LOSS_DB,
            )
            for name in ROADMS
        ]

        # Ethernet toward the packet domains. These links exist from the start;
        # packet_bridge.attach() later adds a second port to each edge.
        self.addLink(client_edge, t_client, port1=0, port2=TERMINAL_ETH_PORT)
        self.addLink(server_edge, t_server, port1=0, port2=TERMINAL_ETH_PORT)

        spans = [
            SPAN,
            ("amp1", {"target_gain": AMP_GAIN}),
            SPAN,
            ("amp2", {"target_gain": AMP_GAIN}),
        ]
        boost = ("boost", {"target_gain": BOOST})

        # Terminal add/drop into the first and out of the last ROADM.
        self.addLink(
            t_client, roadms[0], cls=OpticalLink,
            port1=TERMINAL_WDM_PORT, port2=ROADM_ADD_DROP_PORT, spans=spans,
        )
        self.addLink(
            roadms[-1], t_server, cls=OpticalLink,
            port1=ROADM_ADD_DROP_PORT, port2=TERMINAL_WDM_PORT, spans=spans,
        )

        # The line system itself: r1 -> r2 -> r3 -> r4.
        for west, east in zip(roadms, roadms[1:]):
            self.addLink(
                west, east, cls=OpticalLink,
                port1=ROADM_EAST_PORT, port2=ROADM_WEST_PORT,
                boost1=boost, spans=spans,
            )


class OpticalNetwork:
    """Builds, runs and tears down the line plus its control API."""

    def __init__(self) -> None:
        self.net = None
        self.rest = None
        self._attached = False
        self._stop = threading.Event()

    @property
    def attached(self) -> bool:
        """Whether the packet attachment has already been made."""

        return self._attached

    def start(
        self,
        attach_packet_network: bool = False,
        on_ready: Callable[["OpticalNetwork"], None] | None = None,
    ) -> None:
        """Build the line, publish its API, and block until asked to stop."""

        self._refuse_occupied_api()
        cleanup()
        setLogLevel("info")

        self.net = OpticalNet(topo=FourRoadmTopo(), switch=OVSBridge, controller=None)
        self.net.start()

        self.rest = RestServer(self.net)
        self.rest.start()
        print(f"optical line up; control API on http://{REST_HOST}:{REST_PORT}")

        if attach_packet_network:
            self.attach_packet_network()

        if on_ready is not None:
            on_ready(self)

        self._wait_for_signal()

    def _refuse_occupied_api(self) -> None:
        """Do not clean up namespaces that belong to another running line."""

        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", REST_PORT)) == 0:
                raise RuntimeError(
                    f"port {REST_PORT} is already serving an optical line; "
                    "refusing to reset its state"
                )

    def _wait_for_signal(self) -> None:
        for received in (signal.SIGINT, signal.SIGTERM):
            signal.signal(received, lambda *_: self._stop.set())
        print("running headless; press Ctrl+C to stop")
        self._stop.wait()
        self.stop()

    def request_stop(self) -> None:
        """Ask a blocked ``start`` to return, from another thread."""

        self._stop.set()

    def attach_packet_network(self) -> None:
        """Bridge the optical edges into the packet attachment containers.

        The packet topology has to be up already, and this can only run once:
        the veth surgery is not repeatable.
        """

        if self._attached:
            raise RuntimeError("the packet network is already attached")
        packet_bridge.attach(self.net)
        self._attached = True
        print("attached clientEdge and serverEdge to the packet domains")

    def stop(self) -> None:
        if self.rest is not None:
            self.rest.stop()
            self.rest = None
        if self.net is not None:
            self.net.stop()
            self.net = None
