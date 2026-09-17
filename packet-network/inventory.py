"""Static inventory for the two packet domains.

This module is the single source of truth for what each packet domain owns:
its routers, their management addresses, their service-plane interfaces, and
the static routes that carry the ``client-a`` -> ``server-b`` service. Every
other module in this package derives its behaviour from these tables rather
than hard-coding addresses of its own.

Ownership matters here. Packet A and Packet B are separately owned networks
that happen to share one emulation host, so every lookup in this module can be
scoped to a single domain. A tool that is authorised for Packet A must never be
able to name a Packet B router by accident, and ``routers_in`` /
``assert_owned`` exist to make that check cheap at every call site.

Topology (Containerlab links) and the optical attachment:

    client-a -- pe-a1 --+-- p-a1 --+-- gw-a -- opt-a ))) optical (((
                        |          |
                        +-- p-a2 --+

    ))) optical ((( opt-b -- gw-b --+-- p-b1 --+-- pe-b1 -- server-b
                                    |          |
                                    +-- p-b2 --+

``opt-a`` and ``opt-b`` are transparent L2 bridges. The gateway transit prefix
10.10.4.0/30 spans the optical line, so ``gw-a`` and ``gw-b`` believe they are
directly adjacent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Iterable

LAB_NAME: Final = "packet-qos"
GNMI_PORT: Final = 57400
MANAGEMENT_SUBNET: Final = "172.31.255.0/24"

PACKET_A: Final = "packet-a"
PACKET_B: Final = "packet-b"
DOMAINS: Final[tuple[str, ...]] = (PACKET_A, PACKET_B)

# Service endpoints. These are plain Linux hosts rather than SR Linux nodes, so
# they are not part of ROUTERS and their addresses are applied by the
# Containerlab exec blocks in topology.clab.yml.
CLIENT_HOST: Final = "client-a"
SERVER_HOST: Final = "server-b"
CLIENT_ADDRESS: Final = "10.10.0.2"
SERVER_ADDRESS: Final = "10.20.0.2"

# The L2 attachment containers the optical line plugs into.
ATTACHMENT_NODES: Final[dict[str, str]] = {PACKET_A: "opt-a", PACKET_B: "opt-b"}


class UnknownRouter(LookupError):
    """Raised when a router name is not part of this lab."""


class DomainViolation(PermissionError):
    """Raised when an operation names a router outside the scoped domain."""


@dataclass(frozen=True)
class Interface:
    """One routed subinterface 0 on an SR Linux node."""

    name: str
    address: str
    prefix_length: int
    description: str

    @property
    def ip_prefix(self) -> str:
        return f"{self.address}/{self.prefix_length}"


@dataclass(frozen=True)
class StaticRoute:
    """One IPv4 static route in the default network instance."""

    prefix: str
    next_hop: str
    metric: int = 10


@dataclass(frozen=True)
class Router:
    """An SR Linux node together with the domain that owns it."""

    name: str
    domain: str
    management_ip: str
    role: str
    interfaces: tuple[Interface, ...]
    static_routes: tuple[StaticRoute, ...]


ROUTERS: Final[dict[str, Router]] = {
    "pe-a1": Router(
        name="pe-a1",
        domain=PACKET_A,
        management_ip="172.31.255.11",
        role="ingress provider edge",
        interfaces=(
            Interface("ethernet-1/1", "10.10.0.1", 24, "client-a-lan"),
            Interface("ethernet-1/2", "10.10.1.1", 30, "to-p-a1-primary"),
            Interface("ethernet-1/3", "10.10.1.5", 30, "to-p-a2-backup"),
        ),
        static_routes=(StaticRoute("10.20.0.0/24", "10.10.1.2"),),
    ),
    "p-a1": Router(
        name="p-a1",
        domain=PACKET_A,
        management_ip="172.31.255.12",
        role="primary core",
        interfaces=(
            Interface("ethernet-1/1", "10.10.1.2", 30, "to-pe-a1"),
            Interface("ethernet-1/2", "10.10.2.1", 30, "to-gw-a"),
        ),
        static_routes=(
            StaticRoute("10.10.0.0/24", "10.10.1.1"),
            StaticRoute("10.20.0.0/24", "10.10.2.2"),
        ),
    ),
    "p-a2": Router(
        name="p-a2",
        domain=PACKET_A,
        management_ip="172.31.255.13",
        role="backup core",
        interfaces=(
            Interface("ethernet-1/1", "10.10.1.6", 30, "to-pe-a1"),
            Interface("ethernet-1/2", "10.10.3.1", 30, "to-gw-a"),
        ),
        static_routes=(
            StaticRoute("10.10.0.0/24", "10.10.1.5"),
            StaticRoute("10.20.0.0/24", "10.10.3.2"),
        ),
    ),
    "gw-a": Router(
        name="gw-a",
        domain=PACKET_A,
        management_ip="172.31.255.14",
        role="optical border gateway",
        interfaces=(
            Interface("ethernet-1/1", "10.10.2.2", 30, "to-p-a1-primary"),
            Interface("ethernet-1/2", "10.10.3.2", 30, "to-p-a2-backup"),
            Interface("ethernet-1/3", "10.10.4.1", 30, "optical-transit-to-gw-b"),
        ),
        static_routes=(
            StaticRoute("10.10.0.0/24", "10.10.2.1"),
            StaticRoute("10.20.0.0/24", "10.10.4.2"),
        ),
    ),
    "gw-b": Router(
        name="gw-b",
        domain=PACKET_B,
        management_ip="172.31.255.24",
        role="optical border gateway",
        interfaces=(
            Interface("ethernet-1/1", "10.10.4.2", 30, "optical-transit-to-gw-a"),
            Interface("ethernet-1/2", "10.20.2.1", 30, "to-p-b1-primary"),
            Interface("ethernet-1/3", "10.20.3.1", 30, "to-p-b2-backup"),
        ),
        static_routes=(
            StaticRoute("10.10.0.0/24", "10.10.4.1"),
            StaticRoute("10.20.0.0/24", "10.20.2.2"),
        ),
    ),
    "p-b1": Router(
        name="p-b1",
        domain=PACKET_B,
        management_ip="172.31.255.23",
        role="primary core",
        interfaces=(
            Interface("ethernet-1/1", "10.20.2.2", 30, "to-gw-b"),
            Interface("ethernet-1/2", "10.20.1.1", 30, "to-pe-b1"),
        ),
        static_routes=(
            StaticRoute("10.10.0.0/24", "10.20.2.1"),
            StaticRoute("10.20.0.0/24", "10.20.1.2"),
        ),
    ),
    "p-b2": Router(
        name="p-b2",
        domain=PACKET_B,
        management_ip="172.31.255.22",
        role="backup core",
        interfaces=(
            Interface("ethernet-1/1", "10.20.3.2", 30, "to-gw-b"),
            Interface("ethernet-1/2", "10.20.1.5", 30, "to-pe-b1"),
        ),
        static_routes=(
            StaticRoute("10.10.0.0/24", "10.20.3.1"),
            StaticRoute("10.20.0.0/24", "10.20.1.6"),
        ),
    ),
    "pe-b1": Router(
        name="pe-b1",
        domain=PACKET_B,
        management_ip="172.31.255.21",
        role="egress provider edge",
        interfaces=(
            Interface("ethernet-1/1", "10.20.1.2", 30, "to-p-b1-primary"),
            Interface("ethernet-1/2", "10.20.1.6", 30, "to-p-b2-backup"),
            Interface("ethernet-1/3", "10.20.0.1", 24, "server-b-lan"),
        ),
        static_routes=(StaticRoute("10.10.0.0/24", "10.20.1.1"),),
    ),
}


def router(name: str) -> Router:
    """Return one router, with a message that lists the valid names."""

    try:
        return ROUTERS[name]
    except KeyError as exc:
        raise UnknownRouter(
            f"unknown router {name!r}; this lab has: {', '.join(sorted(ROUTERS))}"
        ) from exc


def routers_in(domain: str | None = None) -> tuple[Router, ...]:
    """Return every router, or only the ones owned by ``domain``."""

    if domain is None:
        return tuple(ROUTERS.values())
    assert_domain(domain)
    return tuple(item for item in ROUTERS.values() if item.domain == domain)


def assert_domain(domain: str) -> None:
    if domain not in DOMAINS:
        raise DomainViolation(
            f"unknown packet domain {domain!r}; expected one of: {', '.join(DOMAINS)}"
        )


def assert_owned(domain: str, names: Iterable[str]) -> None:
    """Fail unless every named router belongs to ``domain``.

    Call this at the boundary of any operation that is scoped to one owner,
    before the operation touches a device.
    """

    assert_domain(domain)
    foreign = sorted(name for name in names if router(name).domain != domain)
    if foreign:
        raise DomainViolation(
            f"{domain} is not authorised for: {', '.join(foreign)}"
        )


def container_name(node: str) -> str:
    """Return the Docker container name Containerlab gives a lab node."""

    return f"clab-{LAB_NAME}-{node}"


def next_hop_group(next_hop: str) -> str:
    """Return the next-hop-group name this package uses for a next hop.

    One group per distinct next-hop address keeps the mapping between a route
    and its egress deterministic, which is what makes a path switch a
    single-leaf change instead of a route rewrite.
    """

    return "nhg-" + next_hop.replace(".", "-")
