"""Unit coverage for the parts that do not need a device.

The gNMI and Docker calls are replaced with recorders, so the checks below are
about the logic each module applies rather than about a live lab.
"""

from __future__ import annotations

import pytest

import backup_path
import telemetry
import traffic
from backup_path import BackupPath, BackupPathError
from inventory import DomainViolation, next_hop_group


# --------------------------------------------------------------------- traffic


class TestReceiverParsing:
    LOG = """
[  5] local 10.20.0.2 port 5201 connected to 10.10.0.2 port 40001
[  5]   0.00-1.00   sec   122 KBytes  1.00 Mbits/sec  0.181 ms  0/89 (0%)
[  5]   1.00-2.00   sec   120 KBytes  0.98 Mbits/sec  0.204 ms  2/89 (2.2%)
"""

    def test_parses_each_completed_interval(self):
        samples = traffic.parse_intervals(self.LOG)
        assert len(samples) == 2
        assert samples[0].throughput_mbps == 1.0
        assert samples[0].lost == 0 and samples[0].total == 89
        assert samples[1].loss_percent == 2.2
        assert samples[1].jitter_ms == 0.204

    def test_interval_identity_distinguishes_consecutive_samples(self):
        samples = traffic.parse_intervals(self.LOG)
        assert samples[0].identity != samples[1].identity

    def test_scales_other_bitrate_units(self):
        line = "[  5]   0.00-1.00 sec  1.00 GBytes  1.05 Gbits/sec  0.10 ms  0/10 (0%)"
        assert traffic.parse_intervals(line)[0].throughput_mbps == 1050.0

    def test_no_completed_interval_yields_nothing(self):
        assert traffic.parse_intervals("") == []
        assert traffic.parse_intervals("Server listening on 5201") == []

    def test_sender_and_receiver_own_different_hosts(self):
        assert traffic.Sender.host != traffic.Receiver.host
        assert traffic.Sender.log != traffic.Receiver.log

    def test_payload_fits_the_smallest_link_on_the_path(self):
        assert traffic.PAYLOAD_BYTES <= 1500 - 20 - 8


# ------------------------------------------------------------------- telemetry


class TestCounterExtraction:
    RESPONSE = {
        "notification": [
            {
                "update": [
                    {
                        "val": {
                            "interface": [
                                {
                                    "name": "ethernet-1/1",
                                    "statistics": {
                                        "in-octets": "1000",
                                        "out-octets": "2000",
                                        "in-discarded-packets": "0",
                                    },
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    def test_extracts_named_interfaces(self):
        found = telemetry.extract(self.RESPONSE)
        assert [item.name for item in found] == ["ethernet-1/1"]
        assert found[0].in_octets == 1000
        assert found[0].out_octets == 2000

    def test_absent_counters_stay_none_rather_than_zero(self):
        assert telemetry.extract(self.RESPONSE)[0].out_discards is None

    def test_first_observation_has_no_rate(self):
        collector = telemetry.Collector("packet-a")
        first = collector._with_rates("p-a1", telemetry.InterfaceCounters("e1", in_octets=100), 10.0)
        assert first.in_bps is None

    def test_rate_is_derived_from_two_observations(self):
        collector = telemetry.Collector("packet-a")
        collector._with_rates("p-a1", telemetry.InterfaceCounters("e1", in_octets=100), 10.0)
        second = collector._with_rates(
            "p-a1", telemetry.InterfaceCounters("e1", in_octets=1100), 11.0
        )
        assert second.in_bps == pytest.approx(8000.0)

    def test_a_counter_that_moved_backwards_yields_no_rate(self):
        collector = telemetry.Collector("packet-a")
        collector._with_rates("p-a1", telemetry.InterfaceCounters("e1", in_octets=5000), 10.0)
        second = collector._with_rates(
            "p-a1", telemetry.InterfaceCounters("e1", in_octets=10), 11.0
        )
        assert second.in_bps is None

    def test_collecting_another_domain_router_is_refused(self):
        with pytest.raises(DomainViolation):
            telemetry.Collector("packet-a").collect("gw-b")


# ----------------------------------------------------------------- backup path


class FakeDevices:
    """Stands in for the routers, so the real decision logic is under test.

    Only the three device-touching methods are replaced; ``state``,
    ``activate_backup``, ``restore_primary`` and ``_move_to`` are the shipped
    implementations.
    """

    def __init__(self, domain, path=backup_path.PRIMARY, backup_up=True, primary_up=False):
        self.domain = domain
        self.readiness = backup_path.READINESS[domain]
        self.routes = {
            target.router: {
                "prefix": target.prefix,
                "next-hop-group": next_hop_group(target.next_hop(path)),
                "metric": 10,
            }
            for target in backup_path.TARGETS[domain]
        }
        self.backup_up = backup_up
        self.primary_up = primary_up
        self.writes: list[tuple[str, str]] = []
        self.readback_group: str | None = None

    def install(self, path: BackupPath) -> BackupPath:
        path._route = self.route
        path._interface_up = self.interface_up
        path._write_route = self.write_route
        path._session = self.refuse_session
        return path

    def refuse_session(self, name):  # pragma: no cover - a real session is a bug here
        raise AssertionError(f"unexpected device session to {name}")

    def route(self, target):
        return dict(self.routes[target.router])

    def interface_up(self, name, _interface):
        if name == self.readiness.backup_router:
            return self.backup_up
        if name == self.readiness.primary_router:
            return self.primary_up
        raise AssertionError(f"readiness read an unexpected router: {name}")

    def write_route(self, target, group, next_hop):
        self.writes.append((target.router, group))
        self.routes[target.router]["next-hop-group"] = group
        # readback_group simulates a device that did not take the change.
        return {**self.routes[target.router],
                "next-hop-group": self.readback_group or group}


def build(domain="packet-a", **kwargs):
    """Return the real BackupPath wired to fake devices."""

    devices = FakeDevices(domain, **kwargs)
    return devices.install(BackupPath(domain)), devices


class TestBackupPathDecisions:
    def test_reports_the_primary_path_when_all_routes_agree(self):
        path, _ = build()
        assert path.state()["path"] == backup_path.PRIMARY

    def test_reports_a_mixed_path_when_routes_disagree(self):
        path, devices = build()
        first = path.targets[0]
        devices.routes[first.router]["next-hop-group"] = next_hop_group(
            first.backup_next_hop
        )
        assert path.state()["path"] == backup_path.MIXED

    def test_switch_moves_every_route_when_the_primary_is_impaired(self):
        path, devices = build(primary_up=False)
        result = path.activate_backup()
        assert result["changed"] is True
        assert result["path"] == backup_path.BACKUP
        assert len(devices.writes) == len(path.targets)

    def test_switch_is_refused_while_the_primary_looks_healthy(self):
        path, devices = build(primary_up=True)
        with pytest.raises(BackupPathError):
            path.activate_backup()
        assert devices.writes == []

    def test_switch_is_refused_when_the_backup_is_down(self):
        path, devices = build(backup_up=False)
        with pytest.raises(BackupPathError):
            path.activate_backup()
        assert devices.writes == []

    def test_force_overrides_only_the_health_check(self):
        path, devices = build(primary_up=True)
        assert path.activate_backup(force=True)["path"] == backup_path.BACKUP
        assert devices.writes

    def test_switching_twice_is_a_no_op(self):
        path, devices = build(primary_up=False)
        path.activate_backup()
        before = len(devices.writes)
        assert path.activate_backup()["changed"] is False
        assert len(devices.writes) == before

    def test_return_is_refused_while_the_primary_is_still_impaired(self):
        path, _ = build(path=backup_path.BACKUP, primary_up=False)
        with pytest.raises(BackupPathError):
            path.restore_primary()

    def test_return_is_allowed_once_the_primary_recovers(self):
        path, _ = build(path=backup_path.BACKUP, primary_up=True)
        assert path.restore_primary()["path"] == backup_path.PRIMARY

    def test_a_mixed_path_must_be_reconciled_before_either_move(self):
        path, devices = build(primary_up=False)
        first = path.targets[0]
        devices.routes[first.router]["next-hop-group"] = next_hop_group(
            first.backup_next_hop
        )
        with pytest.raises(BackupPathError):
            path.activate_backup()

    def test_an_unknown_domain_is_refused_at_construction(self):
        with pytest.raises(DomainViolation):
            BackupPath("packet-c")

    def test_a_readback_that_disagrees_with_the_write_fails_the_move(self):
        path, devices = build(primary_up=False)
        devices.readback_group = "nhg-somewhere-else"
        with pytest.raises(BackupPathError, match="readback"):
            path.activate_backup()

    @pytest.mark.parametrize("domain", ["packet-a", "packet-b"])
    def test_both_domains_switch_and_return_independently(self, domain):
        path, devices = build(domain, primary_up=False)
        assert path.activate_backup()["path"] == backup_path.BACKUP
        devices.primary_up = True
        assert path.restore_primary()["path"] == backup_path.PRIMARY
        assert [router for router, _ in devices.writes] == [
            target.router for target in path.targets
        ] * 2

    def test_readiness_never_reads_a_router_outside_the_domain(self):
        # FakeDevices.interface_up raises on any other router name.
        path, _ = build("packet-b", primary_up=False)
        assert path.state()["domain"] == "packet-b"
