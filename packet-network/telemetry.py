"""Interface counter telemetry for the packet domains.

Counters are cumulative, so a single read cannot establish a rate. The
collector keeps the previous observation per interface and only reports a rate
once it has two, which is why it is a stateful object rather than a function.
A counter that moves backwards (node restart, counter clear) yields ``None``
rather than a fabricated negative rate.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from gnmi import Session, Target, password, username
from inventory import GNMI_PORT, assert_owned, router

# SR Linux releases and models spell these slightly differently; accept the
# known spellings rather than failing on an unexpected one.
COUNTERS = {
    "in_octets": ("in-octets", "in_octets", "in-bytes"),
    "out_octets": ("out-octets", "out_octets", "out-bytes"),
    "in_packets": ("in-packets", "in-unicast-packets", "in_pkts"),
    "out_packets": ("out-packets", "out-unicast-packets", "out_pkts"),
    "in_discards": ("in-discarded-packets", "in-discards", "in_discards"),
    "out_discards": ("out-discarded-packets", "out-discards", "out_discards"),
}


@dataclass(frozen=True)
class InterfaceCounters:
    name: str
    in_octets: int | None = None
    out_octets: int | None = None
    in_packets: int | None = None
    out_packets: int | None = None
    in_discards: int | None = None
    out_discards: int | None = None
    in_bps: float | None = None
    out_bps: float | None = None
    in_discards_per_second: float | None = None
    out_discards_per_second: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RouterCounters:
    router: str
    domain: str
    observed_at: str
    interfaces: tuple[InterfaceCounters, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "router": self.router,
            "domain": self.domain,
            "observed_at": self.observed_at,
            "interfaces": [item.to_dict() for item in self.interfaces],
        }


class Collector:
    """Polls interface counters and derives rates across consecutive reads."""

    def __init__(
        self,
        domain: str,
        gnmi_username: str | None = None,
        gnmi_password: str | None = None,
        port: int = GNMI_PORT,
    ) -> None:
        self.domain = domain
        self.username = username(gnmi_username)
        self.password = password(gnmi_password)
        self.port = port
        self._previous: dict[tuple[str, str], tuple[float, InterfaceCounters]] = {}

    def collect(self, router_name: str) -> RouterCounters:
        """Read one router this collector's domain owns."""

        assert_owned(self.domain, [router_name])
        specification = router(router_name)
        target = Target(
            host=specification.management_ip,
            port=self.port,
            username=self.username,
            password=self.password,
        )
        with Session(target) as session:
            raw = session.interface_statistics()

        read_at = time.monotonic()
        return RouterCounters(
            router=router_name,
            domain=specification.domain,
            observed_at=datetime.now(timezone.utc).isoformat(),
            interfaces=tuple(
                self._with_rates(router_name, item, read_at)
                for item in extract(raw)
            ),
        )

    def _with_rates(
        self, router_name: str, current: InterfaceCounters, read_at: float
    ) -> InterfaceCounters:
        key = (router_name, current.name)
        previous = self._previous.get(key)
        self._previous[key] = (read_at, current)
        if previous is None:
            return current

        previous_at, earlier = previous
        elapsed = read_at - previous_at
        if elapsed <= 0:
            return current
        return InterfaceCounters(
            name=current.name,
            in_octets=current.in_octets,
            out_octets=current.out_octets,
            in_packets=current.in_packets,
            out_packets=current.out_packets,
            in_discards=current.in_discards,
            out_discards=current.out_discards,
            in_bps=_rate(current.in_octets, earlier.in_octets, elapsed, 8),
            out_bps=_rate(current.out_octets, earlier.out_octets, elapsed, 8),
            in_discards_per_second=_rate(
                current.in_discards, earlier.in_discards, elapsed
            ),
            out_discards_per_second=_rate(
                current.out_discards, earlier.out_discards, elapsed
            ),
        )


def extract(response: dict[str, Any]) -> tuple[InterfaceCounters, ...]:
    """Pull interface counters out of a gNMI statistics response.

    The response nests differently depending on the path that was asked for, so
    this walks the structure and keys on whichever ``name`` is in scope rather
    than assuming one shape.
    """

    found: dict[str, InterfaceCounters] = {}

    def visit(value: Any, inherited: str = "") -> None:
        if isinstance(value, list):
            for item in value:
                visit(item, inherited)
            return
        if not isinstance(value, dict):
            return

        name = str(value.get("name") or inherited or "")
        statistics = value.get("statistics")
        if isinstance(statistics, dict) and name and _has_counter(statistics):
            found[name] = InterfaceCounters(name=name, **_read_counters(statistics))
        for key, nested in value.items():
            if key != "statistics":
                visit(nested, name)

    visit(response)
    return tuple(found[name] for name in sorted(found))


def _has_counter(statistics: dict[str, Any]) -> bool:
    return any(key in statistics for names in COUNTERS.values() for key in names)


def _read_counters(statistics: dict[str, Any]) -> dict[str, int | None]:
    return {field: _counter(statistics, names) for field, names in COUNTERS.items()}


def _counter(statistics: dict[str, Any], names: tuple[str, ...]) -> int | None:
    for name in names:
        if name in statistics:
            try:
                return int(statistics[name])
            except (TypeError, ValueError):
                return None
    return None


def _rate(
    current: int | None, previous: int | None, elapsed: float, multiplier: float = 1.0
) -> float | None:
    if current is None or previous is None or current < previous:
        return None
    return (current - previous) * multiplier / elapsed
