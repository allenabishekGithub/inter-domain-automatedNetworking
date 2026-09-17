"""Checks for the optical line that do not need the emulator running.

The topology builder itself needs root and Mininet, so what is verified here is
the pinned specification, the cross-connect plan, the client's request shaping
and the monitor reduction.
"""

from __future__ import annotations

import pytest

import client as optical_client
import packet_bridge
import spec
from client import OpticalClient, OpticalError, collect_monitors, worst_gosnr


class TestSpec:
    def test_the_chain_has_four_roadms_and_two_terminals(self):
        assert len(spec.ROADMS) == 4
        assert spec.CLIENT_TERMINAL != spec.SERVER_TERMINAL
        assert spec.MONITORED_NODES == (
            spec.CLIENT_TERMINAL, *spec.ROADMS, spec.SERVER_TERMINAL
        )

    def test_edge_names_fit_a_linux_interface_name(self):
        # The emulator appends "-ethN"; Linux caps the result at 15 characters.
        for name in (spec.CLIENT_EDGE, spec.SERVER_EDGE):
            assert len(name) + len("-eth1") <= 15

    def test_span_amplifiers_are_unity_gain_for_the_span_loss(self):
        assert spec.SPAN_AMP_GAIN_DB == pytest.approx(
            spec.SPAN_KM * spec.FIBRE_LOSS_DB_PER_KM
        )

    def test_terminal_and_line_ports_are_distinct(self):
        assert spec.TERMINAL_ETH_PORT != spec.TERMINAL_WDM_PORT
        assert len({
            spec.ROADM_ADD_DROP_PORT, spec.ROADM_WEST_PORT, spec.ROADM_EAST_PORT
        }) == 3


class TestRoadmRules:
    def test_there_is_one_rule_per_roadm(self):
        rules = spec.roadm_rules()
        assert [rule.node for rule in rules] == list(spec.ROADMS)

    def test_the_first_roadm_adds_the_channel_and_sends_it_east(self):
        first = spec.roadm_rules()[0]
        assert first.port_in == spec.ROADM_ADD_DROP_PORT
        assert first.port_out == spec.ROADM_EAST_PORT

    def test_the_last_roadm_drops_the_channel_to_its_terminal(self):
        last = spec.roadm_rules()[-1]
        assert last.port_in == spec.ROADM_WEST_PORT
        assert last.port_out == spec.ROADM_ADD_DROP_PORT

    def test_the_middle_roadms_pass_through_west_to_east(self):
        for rule in spec.roadm_rules()[1:-1]:
            assert (rule.port_in, rule.port_out) == (
                spec.ROADM_WEST_PORT, spec.ROADM_EAST_PORT
            )

    def test_the_chain_is_continuous(self):
        """Whatever leaves one ROADM must be what the next one accepts."""

        rules = spec.roadm_rules()
        for west, east in zip(rules, rules[1:]):
            assert west.port_out == spec.ROADM_EAST_PORT
            assert east.port_in == spec.ROADM_WEST_PORT

    def test_every_rule_carries_the_one_configured_channel(self):
        for rule in spec.roadm_rules():
            assert rule.channels == str(spec.CHANNEL)


class RecordingClient(OpticalClient):
    """Captures the requests a real client would send."""

    def __init__(self):
        super().__init__()
        self.calls: list[tuple[str, dict]] = []

    def _get(self, path, **params):
        self.calls.append((path, params))
        return "OK"


class TestConfigureLine:
    def test_clears_every_roadm_before_programming_it(self):
        client = RecordingClient()
        client.configure_line()
        resets = [params["node"] for path, params in client.calls if path == "/reset"]
        assert resets == list(spec.ROADMS)

    def test_installs_the_cross_connects_then_the_terminals(self):
        client = RecordingClient()
        client.configure_line()
        connects = [params for path, params in client.calls if path == "/connect"]
        roadm_connects = [item for item in connects if "port1" in item]
        terminal_connects = [item for item in connects if "ethPort" in item]
        assert len(roadm_connects) == len(spec.ROADMS)
        assert len(terminal_connects) == 2
        assert connects.index(roadm_connects[-1]) < connects.index(terminal_connects[0])

    def test_turns_on_both_terminals_last(self):
        client = RecordingClient()
        client.configure_line()
        assert [path for path, _ in client.calls][-2:] == ["/turn_on", "/turn_on"]
        turned_on = {params["node"] for path, params in client.calls if path == "/turn_on"}
        assert turned_on == {spec.CLIENT_TERMINAL, spec.SERVER_TERMINAL}

    def test_is_safe_to_run_twice(self):
        client = RecordingClient()
        client.configure_line()
        first = list(client.calls)
        client.calls.clear()
        client.configure_line()
        assert client.calls == first


class TestMonitorReduction:
    READINGS = {
        "t-client": {"osnr": {"1": {"freq": 191.35e12, "osnr": 30.1, "gosnr": 28.4}}},
        "r1": {"osnr": {"1": {"osnr": 29.0, "gosnr": 27.2}}},
        "r2": {"osnr": {"1": {"osnr": 28.0, "gosnr": 24.9}}},
    }

    def test_reports_the_worst_node_and_the_overall_minimum(self):
        overall, per_node = worst_gosnr(self.READINGS)
        assert overall == pytest.approx(24.9)
        assert per_node["t-client"] == pytest.approx(28.4)
        assert min(per_node, key=per_node.get) == "r2"

    def test_takes_the_worst_channel_on_a_multi_channel_node(self):
        readings = {"r1": {"osnr": {"1": {"gosnr": 27.0}, "2": {"gosnr": 19.5}}}}
        overall, per_node = worst_gosnr(readings)
        assert overall == pytest.approx(19.5)

    def test_a_node_that_failed_to_read_is_skipped_not_counted_as_zero(self):
        readings = {**self.READINGS, "r3": {"error": "unreachable"}}
        overall, per_node = worst_gosnr(readings)
        assert "r3" not in per_node
        assert overall == pytest.approx(24.9)

    def test_no_readings_yields_no_margin_rather_than_a_number(self):
        assert worst_gosnr({}) == (None, {})
        assert worst_gosnr({"r1": {}})[0] is None

    def test_one_unreachable_monitor_does_not_hide_the_others(self):
        class Flaky(OpticalClient):
            def monitor(self, name):
                if name == spec.monitor_name("r2"):
                    raise OpticalError("boom")
                return {"osnr": {"1": {"gosnr": 26.0}}}

        readings = collect_monitors(Flaky())
        assert set(readings) == set(spec.MONITORED_NODES)
        assert "error" in readings["r2"]
        assert worst_gosnr(readings)[0] == pytest.approx(26.0)


class TestPacketAttachment:
    def test_attachment_container_names_match_the_packet_lab(self):
        assert packet_bridge.attachment_container("opt-a") == "clab-packet-qos-opt-a"

    def test_container_pid_rejects_a_stopped_container(self, monkeypatch):
        monkeypatch.setattr(packet_bridge, "_run", lambda command: "0")
        with pytest.raises(packet_bridge.BridgeError, match="not running"):
            packet_bridge.container_pid("clab-packet-qos-opt-a")

    def test_container_pid_rejects_unparseable_output(self, monkeypatch):
        monkeypatch.setattr(packet_bridge, "_run", lambda command: "<no value>")
        with pytest.raises(packet_bridge.BridgeError, match="unexpected PID"):
            packet_bridge.container_pid("clab-packet-qos-opt-a")

    def test_container_pid_returns_a_running_pid(self, monkeypatch):
        monkeypatch.setattr(packet_bridge, "_run", lambda command: "4242")
        assert packet_bridge.container_pid("clab-packet-qos-opt-a") == 4242

    def test_the_two_edges_use_different_veth_names(self, monkeypatch):
        """A shared veth name would make the second attachment clobber the first."""

        seen = []
        monkeypatch.setattr(
            packet_bridge,
            "attach_edge",
            lambda edge, container, veth: seen.append((edge, container, veth)),
        )
        packet_bridge.attach({spec.CLIENT_EDGE: "c", spec.SERVER_EDGE: "s"})
        assert len({veth for _edge, _container, veth in seen}) == 2
        assert len({container for _edge, container, _veth in seen}) == 2


class TestClientErrors:
    def test_an_unreachable_line_is_reported_not_swallowed(self):
        client = OpticalClient(host="127.0.0.1", port=1, timeout=0.2)
        assert client.reachable() is False
        with pytest.raises(OpticalError, match="Is the line running"):
            client.nodes()
