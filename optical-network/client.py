"""HTTP client for a running optical line.

Depends only on ``requests``, so configuration and monitoring work from any
environment as long as the line is running somewhere. The emulator's action
endpoints answer with a plain string rather than JSON, so responses are decoded
opportunistically instead of assuming one content type.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

from spec import (
    CHANNEL,
    CLIENT_TERMINAL,
    MONITORED_NODES,
    REST_HOST,
    REST_PORT,
    ROADMS,
    SERVER_TERMINAL,
    TERMINAL_ETH_PORT,
    TERMINAL_WDM_PORT,
    monitor_name,
    roadm_rules,
)


class OpticalError(RuntimeError):
    """Raised when the line is unreachable or rejects a request."""


@dataclass
class OpticalClient:
    host: str = REST_HOST
    port: int = REST_PORT
    timeout: float = 5.0

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def _get(self, path: str, **params):
        url = f"{self.base_url}{path}"
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            raise OpticalError(
                f"GET {url} {params} failed: {exc}. Is the line running?"
            ) from exc
        if response.status_code != 200:
            raise OpticalError(
                f"GET {url} {params} -> {response.status_code}: {response.text}"
            )
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            return response.text

    # ------------------------------------------------------------ observation

    def nodes(self) -> dict:
        return self._get("/nodes")

    def monitor(self, name: str) -> dict:
        return self._get("/monitor", monitor=name)

    def reachable(self) -> bool:
        try:
            self.nodes()
            return True
        except OpticalError:
            return False

    # ---------------------------------------------------------- configuration

    def reset(self, node: str):
        return self._get("/reset", node=node)

    def cross_connect(self, node: str, port_in: int, port_out: int, channels: str):
        return self._get(
            "/connect", node=node, port1=port_in, port2=port_out, channels=channels
        )

    def connect_terminal(
        self,
        node: str,
        eth_port: int,
        wdm_port: int,
        channel: int,
        power: float = 0.0,
    ):
        return self._get(
            "/connect",
            node=node,
            ethPort=eth_port,
            wdmPort=wdm_port,
            channel=channel,
            power=power,
        )

    def turn_on(self, node: str):
        return self._get("/turn_on", node=node)

    def configure_line(self) -> None:
        """Program the single end-to-end lightpath.

        Clearing the ROADMs first makes this safe to re-run: the line ends in
        the same state whether or not it was already configured.
        """

        for node in ROADMS:
            self.reset(node)
        for rule in roadm_rules():
            self.cross_connect(rule.node, rule.port_in, rule.port_out, rule.channels)
        for terminal in (CLIENT_TERMINAL, SERVER_TERMINAL):
            self.connect_terminal(
                terminal, TERMINAL_ETH_PORT, TERMINAL_WDM_PORT, CHANNEL
            )
        for terminal in (CLIENT_TERMINAL, SERVER_TERMINAL):
            self.turn_on(terminal)


def collect_monitors(client: OpticalClient | None = None) -> dict[str, dict]:
    """Read every monitor on the line, keeping errors per node.

    One unreadable monitor should not hide the readings that did come back, so
    a failure is recorded against its own node rather than raised.
    """

    client = client or OpticalClient()
    readings: dict[str, dict] = {}
    for node in MONITORED_NODES:
        try:
            readings[node] = client.monitor(monitor_name(node))
        except OpticalError as exc:
            readings[node] = {"error": str(exc)}
    return readings


def worst_gosnr(readings: dict[str, dict]) -> tuple[float | None, dict[str, float]]:
    """Reduce monitor readings to a per-node and overall minimum gOSNR.

    A modelled optical margin is not a packet measurement. Use this to see
    whether the line is carrying the channel with headroom, and the receiver's
    own counters to say whether packets arrived.
    """

    per_node: dict[str, float] = {}
    for node, data in (readings or {}).items():
        if not isinstance(data, dict):
            continue
        channels = data.get("osnr")
        if not isinstance(channels, dict):
            continue
        values = [
            float(entry["gosnr"])
            for entry in channels.values()
            if isinstance(entry, dict) and entry.get("gosnr") is not None
        ]
        if values:
            per_node[node] = min(values)
    return (min(per_node.values()) if per_node else None), per_node
