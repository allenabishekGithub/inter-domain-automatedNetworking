"""The inventory has to agree with the wiring and with itself.

These checks run without a lab: they catch an address typo or a mis-scoped
domain before anything is deployed onto eight routers.
"""

from __future__ import annotations

import ipaddress
from pathlib import Path

import pytest

import backup_path
from inventory import (
    DOMAINS,
    PACKET_A,
    PACKET_B,
    ROUTERS,
    DomainViolation,
    UnknownRouter,
    assert_owned,
    container_name,
    next_hop_group,
    router,
    routers_in,
)

TOPOLOGY = (Path(__file__).resolve().parents[1] / "topology.clab.yml").read_text()


def test_every_router_belongs_to_a_known_domain():
    for item in ROUTERS.values():
        assert item.domain in DOMAINS


def test_domains_partition_the_routers():
    a = {item.name for item in routers_in(PACKET_A)}
    b = {item.name for item in routers_in(PACKET_B)}
    assert a and b
    assert not a & b
    assert a | b == set(ROUTERS)


def test_management_addresses_are_unique_and_in_the_management_subnet():
    subnet = ipaddress.ip_network("172.31.255.0/24")
    seen = set()
    for item in ROUTERS.values():
        address = ipaddress.ip_address(item.management_ip)
        assert address in subnet
        assert address not in seen
        seen.add(address)


def test_service_addresses_are_unique():
    seen = set()
    for item in ROUTERS.values():
        for interface in item.interfaces:
            assert interface.address not in seen, interface.address
            seen.add(interface.address)


def test_every_next_hop_is_on_a_directly_connected_subnet():
    """A static route is only useful if its next hop is reachable on a link."""

    networks = {
        ipaddress.ip_interface(i.ip_prefix).network: name
        for name, item in ROUTERS.items()
        for i in item.interfaces
    }
    for name, item in ROUTERS.items():
        local = [ipaddress.ip_interface(i.ip_prefix).network for i in item.interfaces]
        for route in item.static_routes:
            hop = ipaddress.ip_address(route.next_hop)
            assert any(hop in network for network in local), (
                f"{name}: next hop {route.next_hop} for {route.prefix} "
                "is not on a connected subnet"
            )
            assert any(hop in network for network in networks), route.next_hop


def test_every_next_hop_belongs_to_another_router():
    owned = {i.address for item in ROUTERS.values() for i in item.interfaces}
    for item in ROUTERS.values():
        for route in item.static_routes:
            assert route.next_hop in owned


def test_each_point_to_point_subnet_has_exactly_two_ends():
    ends: dict[ipaddress.IPv4Network, list[str]] = {}
    for name, item in ROUTERS.items():
        for interface in item.interfaces:
            parsed = ipaddress.ip_interface(interface.ip_prefix)
            if parsed.network.prefixlen == 30:
                ends.setdefault(parsed.network, []).append(name)
    assert ends
    for network, members in ends.items():
        assert len(members) == 2, f"{network} has ends {members}"


def test_every_configured_interface_is_wired_in_the_topology_file():
    """An address on an interface the topology never cables is dead config."""

    for name, item in ROUTERS.items():
        for interface in item.interfaces:
            # ethernet-1/2 is cabled as e1-2 in the Containerlab file.
            wired = interface.name.replace("ethernet-1/", "e1-")
            assert f"{name}:{wired}" in TOPOLOGY, f"{name}:{interface.name}"


def test_router_lookup_rejects_an_unknown_name():
    with pytest.raises(UnknownRouter):
        router("p-c9")


def test_assert_owned_rejects_a_router_from_another_domain():
    assert_owned(PACKET_A, ["pe-a1", "gw-a"])
    with pytest.raises(DomainViolation):
        assert_owned(PACKET_A, ["pe-a1", "gw-b"])


def test_routers_in_rejects_an_unknown_domain():
    with pytest.raises(DomainViolation):
        routers_in("packet-c")


def test_container_and_group_naming():
    assert container_name("gw-a") == "clab-packet-qos-gw-a"
    assert next_hop_group("10.10.1.2") == "nhg-10-10-1-2"


class TestBackupPathTargets:
    def test_each_domain_only_touches_its_own_routers(self):
        for domain, targets in backup_path.TARGETS.items():
            assert_owned(domain, [target.router for target in targets])

    def test_each_domain_switches_both_directions(self):
        for domain, targets in backup_path.TARGETS.items():
            prefixes = {target.prefix for target in targets}
            assert prefixes == {"10.10.0.0/24", "10.20.0.0/24"}, domain

    def test_primary_next_hops_match_the_configured_routes(self):
        """The 'primary' side of a switch must be what configure() installs."""

        for targets in backup_path.TARGETS.values():
            for target in targets:
                installed = {
                    route.prefix: route.next_hop
                    for route in router(target.router).static_routes
                }
                assert installed[target.prefix] == target.primary_next_hop

    def test_backup_next_hops_belong_to_the_domain_backup_core_router(self):
        for domain, targets in backup_path.TARGETS.items():
            backup_router = router(backup_path.READINESS[domain].backup_router)
            addresses = {i.address for i in backup_router.interfaces}
            for target in targets:
                assert target.backup_next_hop in addresses

    def test_readiness_watches_this_domain_own_core_routers(self):
        for domain, readiness in backup_path.READINESS.items():
            assert_owned(domain, [readiness.primary_router, readiness.backup_router])

    def test_impairment_is_observed_on_a_different_router_than_it_is_applied(self):
        """The degradation signal must not just read back the injected change.

        The fault is applied to the gateway-side port; readiness is observed on
        the core router at the far end, which sees the link go away.
        """

        for domain, (faulted, _interface) in backup_path.IMPAIRMENT.items():
            assert_owned(domain, [faulted])
            assert faulted != backup_path.READINESS[domain].primary_router
            assert faulted != backup_path.READINESS[domain].backup_router

    def test_impaired_interface_faces_the_primary_core_router(self):
        for domain, (faulted, interface) in backup_path.IMPAIRMENT.items():
            primary = backup_path.READINESS[domain].primary_router
            addresses = {i.address for i in router(primary).interfaces}
            local = next(
                i for i in router(faulted).interfaces if i.name == interface
            )
            network = ipaddress.ip_interface(local.ip_prefix).network
            assert any(
                ipaddress.ip_address(address) in network for address in addresses
            ), f"{domain}: {faulted}/{interface} does not face {primary}"
