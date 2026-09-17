"""Description of the optical line, free of any emulator imports.

Keeping the node names, ports, channel plan and link budget in a module that
imports nothing heavier than the standard library means the client, telemetry
and CLI can talk to a running line over HTTP without Mininet installed, while
the topology builder reads the same constants. The two can therefore never
disagree about which port carries what.

    clientEdge -- t-client == r1 == r2 == r3 == r4 == t-server -- serverEdge
                             (channel 1, west/east through the ROADM chain)

``--`` is Ethernet toward the packet attachment, ``==`` is a WDM span.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# The emulator's own control API. It binds the loopback interface only.
REST_HOST: Final[str] = "localhost"
REST_PORT: Final[int] = 8080

# Edge host names stay at or below ten characters: the emulator appends
# "-ethN" and Linux caps an interface name at fifteen.
CLIENT_EDGE: Final[str] = "clientEdge"
SERVER_EDGE: Final[str] = "serverEdge"

CLIENT_TERMINAL: Final[str] = "t-client"
SERVER_TERMINAL: Final[str] = "t-server"
ROADMS: Final[tuple[str, ...]] = ("r1", "r2", "r3", "r4")

# The wavelengths this line can carry. The terminals are tunable: the service
# rides exactly one of these at a time, and which one is a configuration choice
# the optical domain owns. Lighting several at once would need a transceiver and
# an add/drop port per channel, and is a separate extension.
CHANNELS: Final[tuple[int, ...]] = (1, 2)
DEFAULT_CHANNEL: Final[int] = CHANNELS[0]

TERMINAL_ETH_PORT: Final[int] = 1
TERMINAL_WDM_PORT: Final[int] = 11
ROADM_ADD_DROP_PORT: Final[int] = 1
ROADM_WEST_PORT: Final[int] = 111
ROADM_EAST_PORT: Final[int] = 222

MONITORED_NODES: Final[tuple[str, ...]] = (CLIENT_TERMINAL, *ROADMS, SERVER_TERMINAL)

# Link budget. Short spans with unity-gain amplifiers keep accumulated
# nonlinear interference low enough that the four-ROADM chain closes with
# margin. This is a compact campus-scale model chosen for reproducibility; it
# is not a calibrated long-haul link and its gOSNR figures should be read as
# modelled values rather than measured transmission performance.
SPAN_KM: Final[float] = 0.05
FIBRE_LOSS_DB_PER_KM: Final[float] = 0.22
SPAN_AMP_GAIN_DB: Final[float] = SPAN_KM * FIBRE_LOSS_DB_PER_KM
BOOST_GAIN_DB: Final[float] = 3.0
LAUNCH_POWER_DBM: Final[float] = 0.0

# Each ROADM in this emulator models a default internal switching loss that
# nothing in a plain chain compensates. Four of them in series would sink the
# channel on their own, so the model is zeroed and the span amplifiers are left
# to define the budget. That simplification is part of the pinned fixture.
ROADM_INSERTION_LOSS_DB: Final[float] = 0.0

# The packet-side attachment containers this line plugs into, and the
# Containerlab lab that owns them.
PACKET_LAB_NAME: Final[str] = "packet-qos"
CLIENT_ATTACHMENT: Final[str] = "opt-a"
SERVER_ATTACHMENT: Final[str] = "opt-b"


def attachment_container(node: str) -> str:
    """Return the Docker container name of a packet attachment bridge."""

    return f"clab-{PACKET_LAB_NAME}-{node}"


class UnknownChannel(ValueError):
    """Raised when a channel is not one this line can carry."""


def check_channel(channel: int) -> int:
    """Return the channel, or fail with the set this line actually supports."""

    if channel not in CHANNELS:
        raise UnknownChannel(
            f"channel {channel} is not carried by this line; "
            f"it supports: {', '.join(str(c) for c in CHANNELS)}"
        )
    return channel


@dataclass(frozen=True)
class RoadmRule:
    """One wavelength cross-connect inside a ROADM."""

    node: str
    port_in: int
    port_out: int
    channels: str


def roadm_rules(channel: int = DEFAULT_CHANNEL) -> list[RoadmRule]:
    """The cross-connects that carry one channel from t-client to t-server.

    The first ROADM takes the channel off its add/drop port and sends it east;
    the middle ROADMs pass it west to east; the last one drops it toward the
    receiving terminal. The shape is the same whichever wavelength is chosen --
    only the channel the rules match on changes.
    """

    check_channel(channel)
    first, *middle, last = ROADMS
    label = str(channel)
    rules = [RoadmRule(first, ROADM_ADD_DROP_PORT, ROADM_EAST_PORT, label)]
    rules += [RoadmRule(node, ROADM_WEST_PORT, ROADM_EAST_PORT, label) for node in middle]
    rules.append(RoadmRule(last, ROADM_WEST_PORT, ROADM_ADD_DROP_PORT, label))
    return rules


def monitor_name(node: str) -> str:
    """Return the name of the optical monitor attached to a node."""

    return f"{node}-monitor"
