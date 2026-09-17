"""Attach the optical edges to the packet domains' bridge containers.

The optical line terminates on two plain Linux hosts, ``clientEdge`` and
``serverEdge``. Each packet domain terminates its border gateway on a container
running a Linux bridge. This module joins the two with a veth pair, so a frame
leaving ``gw-a`` crosses the ROADM chain and arrives at ``gw-b``.

Both ends are ordinary network namespaces, so a veth can be added to them at
runtime. That is why the attachment is a separate container rather than a
direct link into a router: the router image expects all of its interfaces to
exist when it boots.

The edge keeps whatever address the emulator gave it only until this runs; the
address is flushed, because after bridging the interface is an L2 port carrying
the packet domains' own addressing, not an endpoint of its own.

This must run in the process that owns the optical network -- the edge
namespaces exist only for that process's lifetime -- and it needs root plus
access to the container runtime.
"""

from __future__ import annotations

import subprocess

from spec import (
    CLIENT_ATTACHMENT,
    CLIENT_EDGE,
    SERVER_ATTACHMENT,
    SERVER_EDGE,
    attachment_container,
)

# Name of the port added inside each attachment container.
CONTAINER_PORT = "eth2"
# Bridge created inside each optical edge namespace.
EDGE_BRIDGE = "br-opt"


class BridgeError(RuntimeError):
    """Raised when an attachment cannot be completed."""


def _run(command: list[str]) -> str:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise BridgeError(f"{' '.join(command)} failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def container_pid(name: str) -> int:
    """Return the host PID of a running container's main process."""

    output = _run(["docker", "inspect", "-f", "{{.State.Pid}}", name])
    try:
        pid = int(output)
    except ValueError as exc:
        raise BridgeError(f"unexpected PID for {name}: {output!r}") from exc
    if pid <= 0:
        raise BridgeError(f"container {name} is not running")
    return pid


def _in_netns(pid: int, *arguments: str) -> str:
    return _run(["nsenter", "-t", str(pid), "-n", "ip", *arguments])


def attach_edge(edge, container: str, veth: str) -> None:
    """Bridge one optical edge host into one attachment container.

    ``edge`` is the live edge node object, already linked to its terminal by
    the topology. That link is left alone; it simply gains a bridge partner.
    """

    # Imported lazily so the rest of this module stays importable, and
    # testable, without the emulator present.
    from mininet.util import makeIntfPair

    optical_port = edge.intfNames()[0]
    edge_port = f"{edge.name}-eth1"

    # The far end is born inside the edge's namespace, the same way the
    # topology's own links are made.
    makeIntfPair(veth, edge_port, node2=edge)

    edge.cmd(f"ip addr flush dev {optical_port}")
    edge.cmd(f"ip link add name {EDGE_BRIDGE} type bridge")
    edge.cmd(f"ip link set {EDGE_BRIDGE} up")
    for port in (optical_port, edge_port):
        edge.cmd(f"ip link set {port} master {EDGE_BRIDGE}")
        edge.cmd(f"ip link set {port} up")

    pid = container_pid(container)
    _run(["ip", "link", "set", veth, "netns", str(pid)])
    _in_netns(pid, "link", "set", veth, "name", CONTAINER_PORT)
    _in_netns(pid, "link", "set", CONTAINER_PORT, "master", "br0")
    _in_netns(pid, "link", "set", CONTAINER_PORT, "up")


def attach(net, client_container: str | None = None, server_container: str | None = None) -> None:
    """Bridge both optical edges into their packet attachment containers."""

    client_container = client_container or attachment_container(CLIENT_ATTACHMENT)
    server_container = server_container or attachment_container(SERVER_ATTACHMENT)

    attach_edge(net[CLIENT_EDGE], client_container, "veth-opt-a")
    attach_edge(net[SERVER_EDGE], server_container, "veth-opt-b")
