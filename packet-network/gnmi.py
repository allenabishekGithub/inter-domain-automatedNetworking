"""A narrow gNMI adapter for the SR Linux nodes in this lab.

This deliberately is not a general configuration shell. It exposes the handful
of operations the packet domains actually need -- address an interface, put it
in the default network instance, install a static route, read counters, read
oper-state, repoint a route's next-hop group -- and nothing else. Anything that
wants to change a router in a new way has to add a named, typed method here
first, which keeps the set of possible device writes reviewable.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Any, Iterable

from inventory import GNMI_PORT, next_hop_group


def _keep_library_logging_off_stdout() -> None:
    """Move the gNMI library's own log records to stderr.

    pygnmi attaches a stdout handler to its module logger when it is imported,
    so a lab with a self-signed certificate emits a warning per session onto
    stdout. Anything in this package that prints JSON would then produce output
    that cannot be piped. Diagnostics belong on stderr; move them there.
    """

    library_logger = logging.getLogger("pygnmi.client")
    for handler in list(library_logger.handlers):
        if isinstance(handler, logging.StreamHandler) and handler.stream is sys.stdout:
            library_logger.removeHandler(handler)
    if not library_logger.handlers:
        library_logger.addHandler(logging.StreamHandler(sys.stderr))

try:  # pygnmi is only needed when talking to a real device
    from pygnmi.client import gNMIclient
except ImportError:  # pragma: no cover - exercised when the extra is absent
    gNMIclient = None
else:
    _keep_library_logging_off_stdout()


# Credentials the SR Linux container image ships with. They are the vendor's
# published defaults for a throwaway lab rather than a secret, and this is the
# only place either literal appears -- set SRL_GNMI_USERNAME / SRL_GNMI_PASSWORD
# to point the whole package at different ones.
_IMAGE_USERNAME = "admin"
_IMAGE_PASSWORD = "NokiaSrl1!"


def username(explicit: str | None = None) -> str:
    return explicit or os.getenv("SRL_GNMI_USERNAME") or _IMAGE_USERNAME


def password(explicit: str | None = None) -> str:
    return explicit or os.getenv("SRL_GNMI_PASSWORD") or _IMAGE_PASSWORD


class GNMIUnavailable(RuntimeError):
    """Raised when the optional pygnmi dependency is not installed."""


class GNMIConnectionError(RuntimeError):
    """Raised when a session cannot be established within the retry budget."""


@dataclass(frozen=True)
class Target:
    """Everything needed to reach one router's gNMI endpoint."""

    host: str
    port: int = GNMI_PORT
    username: str = field(default_factory=username)
    password: str = field(default_factory=password)
    timeout: int = 30
    # The lab nodes present self-signed certificates. This is a lab-only
    # setting; a deployment with a real trust chain overrides it here.
    skip_verify: bool = True


class Session(AbstractContextManager["Session"]):
    """Context-managed gNMI session with a small typed operation set."""

    def __init__(self, target: Target) -> None:
        self.target = target
        self._client: Any | None = None

    def __enter__(self) -> "Session":
        self.connect()
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    @property
    def connected(self) -> bool:
        return self._client is not None

    def connect(self, attempts: int = 3, retry_delay: float = 5.0) -> None:
        """Open a session, retrying while the node's gNMI server warms up."""

        if gNMIclient is None:
            raise GNMIUnavailable(
                "pygnmi is not installed; run: pip install -r requirements.txt"
            )
        if self._client is not None:
            return

        last: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                client = gNMIclient(
                    target=(self.target.host, self.target.port),
                    username=self.target.username,
                    password=self.target.password,
                    timeout=self.target.timeout,
                    skip_verify=self.target.skip_verify,
                    override=self.target.host,
                )
                client.__enter__()
                self._client = client
                return
            except Exception as exc:  # pygnmi raises transport-specific types
                last = exc
                if attempt < attempts:
                    time.sleep(retry_delay)
        raise GNMIConnectionError(
            f"no gNMI session to {self.target.host}:{self.target.port} "
            f"after {attempts} attempts: {last}"
        )

    def close(self) -> None:
        if self._client is None:
            return
        try:
            self._client.__exit__(None, None, None)
        finally:
            self._client = None

    # ---------------------------------------------------------------- raw verbs

    def get(self, paths: Iterable[str], datatype: str = "all") -> dict[str, Any]:
        return self._client_or_fail().get(
            path=list(paths), datatype=datatype, encoding="json_ietf"
        )

    def update(self, path: str, value: dict[str, Any]) -> Any:
        return self._client_or_fail().set(update=[(path, value)], encoding="json_ietf")

    # ----------------------------------------------------------- configuration

    def configure_interface(
        self,
        interface: str,
        address: str,
        prefix_length: int,
        description: str = "",
        subinterface: int = 0,
    ) -> Any:
        """Enable a routed interface and give subinterface 0 an IPv4 address."""

        interface_config: dict[str, Any] = {"admin-state": "enable"}
        if description:
            interface_config["description"] = description
        return self._client_or_fail().set(
            update=[
                (f"/interface[name={interface}]", interface_config),
                (
                    f"/interface[name={interface}]/subinterface[index={subinterface}]",
                    {
                        "admin-state": "enable",
                        "ipv4": {
                            "admin-state": "enable",
                            "address": [{"ip-prefix": f"{address}/{prefix_length}"}],
                        },
                    },
                ),
            ],
            encoding="json_ietf",
        )

    def attach_to_default_instance(self, interface: str, subinterface: int = 0) -> Any:
        """Put a routed subinterface into the default network instance."""

        member = f"{interface}.{subinterface}"
        return self.update(
            f"/network-instance[name=default]/interface[name={member}]", {}
        )

    def configure_static_route(self, prefix: str, next_hop: str, metric: int = 10) -> Any:
        """Install a static route behind its own single-member next-hop group.

        Creating the group first and then pointing the route at it means a later
        path change only has to rewrite one leaf -- the route's group reference.
        """

        group = next_hop_group(next_hop)
        client = self._client_or_fail()
        client.set(
            update=[
                (
                    f"/network-instance[name=default]/next-hop-groups/group[name={group}]",
                    {"nexthop": [{"index": 1, "ip-address": next_hop}]},
                )
            ],
            encoding="json_ietf",
        )
        return client.set(
            update=[
                (
                    f"/network-instance[name=default]/static-routes/route[prefix={prefix}]",
                    {"admin-state": "enable", "next-hop-group": group, "metric": metric},
                )
            ],
            encoding="json_ietf",
        )

    def set_route_next_hop_group(
        self, prefix: str, group: str, next_hop: str | None = None
    ) -> Any:
        """Repoint an existing route at another next-hop group.

        ``next_hop`` recreates the group first, so the operation works even if
        the target group was never installed or has been removed.
        """

        client = self._client_or_fail()
        if next_hop is not None:
            client.set(
                update=[
                    (
                        f"/network-instance[name=default]/next-hop-groups/group[name={group}]",
                        {"nexthop": [{"index": 1, "ip-address": next_hop}]},
                    )
                ],
                encoding="json_ietf",
            )
        return self.update(
            f"/network-instance[name=default]/static-routes/route[prefix={prefix}]",
            {"next-hop-group": group},
        )

    # -------------------------------------------------------------- observation

    def interface_statistics(self) -> dict[str, Any]:
        return self.get(["/interface/statistics"])

    def interface_oper_state(self, interface: str) -> str:
        """Return the operational state string for one interface."""

        payload = self.get([f"/interface[name={interface}]/oper-state"])
        states = [value for value in values(payload) if isinstance(value, str)]
        if len(states) != 1:
            raise GNMIConnectionError(
                f"no single oper-state for {self.target.host} {interface}"
            )
        return states[0]

    def configured_route(self, prefix: str) -> dict[str, Any]:
        """Return the configured (not resolved) static route for a prefix."""

        payload = self.get(
            [f"/network-instance[name=default]/static-routes/route[prefix={prefix}]"],
            datatype="config",
        )
        for value in values(payload):
            cleaned = strip_modules(value)
            if isinstance(cleaned, dict) and "next-hop-group" in cleaned:
                return cleaned
        raise GNMIConnectionError(
            f"no configured route for {prefix} on {self.target.host}"
        )

    def _client_or_fail(self) -> Any:
        if self._client is None:
            raise GNMIConnectionError("gNMI session is not open")
        return self._client


def values(payload: dict[str, Any]) -> Iterable[Any]:
    """Yield every ``val`` in a gNMI GetResponse."""

    for notification in payload.get("notification", []):
        for update in notification.get("update", []):
            yield update.get("val")


def strip_modules(value: Any) -> Any:
    """Drop YANG module prefixes so keys compare by their local name."""

    if isinstance(value, dict):
        return {key.split(":")[-1]: strip_modules(item) for key, item in value.items()}
    if isinstance(value, list):
        return [strip_modules(item) for item in value]
    return value
