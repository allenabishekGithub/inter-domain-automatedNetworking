"""The client-a -> server-b UDP service flow.

The service under test is one iperf3 UDP stream. Ownership is split the way the
domains are: Packet A owns the sender on ``client-a``, Packet B owns the
receiver on ``server-b``. ``Sender`` and ``Receiver`` are therefore separate
classes with separate hosts, and neither reaches into the other's container.

Only the receiver can establish delivery. Sender-side throughput proves that
packets left ``client-a``, not that any of them arrived, so
``Receiver.report()`` is what a health check should read.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Sequence

from inventory import (
    CLIENT_HOST,
    SERVER_ADDRESS,
    SERVER_HOST,
    container_name,
)

PORT = 5201
CLIENT_LOG = "/tmp/packet-qos-client.log"
SERVER_LOG = "/tmp/packet-qos-server.log"

# The endpoint veths come up with a large MTU while every routed SR Linux
# subinterface along the path uses the default 1500. iperf3 sizes its datagram
# from the local interface unless told otherwise, so an unset length produces
# ~9000-byte datagrams that die at the first router. Pin a payload that fits
# the smallest link on the path.
PAYLOAD_BYTES = 1400

# ~24h. `stop` ends the stream; this is just a bound so a forgotten stream
# cannot outlive the lab.
CONTINUOUS_SECONDS = 86_400


class TrafficError(RuntimeError):
    """Raised when a traffic command cannot be completed."""


@dataclass(frozen=True)
class Sample:
    """One completed receiver interval.

    ``identity`` is what distinguishes a fresh measurement from a stale log
    line that happens to be read twice.
    """

    start_seconds: float
    end_seconds: float
    throughput_mbps: float
    jitter_ms: float
    lost: int
    total: int
    loss_percent: float

    @property
    def identity(self) -> str:
        return f"{self.start_seconds:.2f}-{self.end_seconds:.2f}"


# e.g. [  5]   4.00-5.00   sec   122 KBytes  1.00 Mbits/sec  0.181 ms  0/89 (0%)
_INTERVAL = re.compile(
    r"\[\s*\d+\]\s+([\d.]+)-([\d.]+)\s+sec\s+"
    r"[\d.]+\s+[KMG]?Bytes\s+"
    r"([\d.]+)\s+([KMG]?)bits/sec\s+"
    r"([\d.]+)\s+ms\s+"
    r"(\d+)/(\d+)\s+\(([\d.]+)%\)"
)

_SCALE = {"": 1e-6, "K": 1e-3, "M": 1.0, "G": 1e3}


def parse_intervals(log_text: str) -> list[Sample]:
    """Parse every completed interval line out of an iperf3 UDP log."""

    samples = []
    for match in _INTERVAL.finditer(log_text or ""):
        start, end, rate, unit, jitter, lost, total, loss = match.groups()
        samples.append(
            Sample(
                start_seconds=float(start),
                end_seconds=float(end),
                throughput_mbps=round(float(rate) * _SCALE.get(unit, 1.0), 4),
                jitter_ms=float(jitter),
                lost=int(lost),
                total=int(total),
                loss_percent=float(loss),
            )
        )
    return samples


def _run(command: Sequence[str], allow_failure: bool = False) -> subprocess.CompletedProcess:
    if shutil.which(command[0]) is None:
        raise TrafficError(f"{command[0]!r} is not on PATH")
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0 and not allow_failure:
        raise TrafficError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stderr.strip()}"
        )
    return completed


class Receiver:
    """The iperf3 server on server-b, owned by Packet B."""

    host = SERVER_HOST
    log = SERVER_LOG

    def start(self) -> None:
        """(Re)start the receiver on a truncated log."""

        self.stop()
        _run(("docker", "exec", container_name(self.host), "truncate", "-s", "0", self.log))
        _run(
            (
                "docker", "exec", "-d", container_name(self.host),
                "iperf3", "-s", "-p", str(PORT), "-i", "1",
                "--forceflush", "--logfile", self.log,
            )
        )

    def stop(self) -> None:
        _run(
            ("docker", "exec", container_name(self.host), "pkill", "-f", "iperf3 -s"),
            allow_failure=True,
        )

    def running(self) -> bool:
        return _run(
            ("docker", "exec", container_name(self.host), "pgrep", "-f", "iperf3 -s"),
            allow_failure=True,
        ).returncode == 0

    def log_text(self, lines: int = 20) -> str:
        return _run(
            ("docker", "exec", container_name(self.host), "tail", "-n", str(lines), self.log),
            allow_failure=True,
        ).stdout

    def log_modified_at(self) -> int | None:
        """Receiver log mtime, in whole seconds.

        The endpoint image ships a stat that has no sub-second format, so this
        cannot order a sample against an event in the same second. Use it as a
        liveness hint -- "the receiver is still writing" -- and use
        ``Sample.identity`` to decide whether a reading is one you have not
        already counted. A consumer that must prove a sample came after some
        event should record that event's time itself and then wait for an
        interval identity it has never seen, rather than trusting this value.
        """

        completed = _run(
            ("docker", "exec", container_name(self.host), "stat", "-c", "%Y", self.log),
            allow_failure=True,
        )
        try:
            return int(completed.stdout.strip())
        except ValueError:
            return None

    def report(self, lines: int = 20) -> dict:
        """Current receiver-side view of the service."""

        samples = parse_intervals(self.log_text(lines))
        latest = samples[-1] if samples else None
        return {
            "running": self.running(),
            "log_modified_at": self.log_modified_at(),
            "log_modified_resolution_seconds": 1,
            "samples": len(samples),
            "latest": latest.__dict__ if latest else None,
            "latest_identity": latest.identity if latest else None,
        }


class Sender:
    """The iperf3 client on client-a, owned by Packet A."""

    host = CLIENT_HOST
    log = CLIENT_LOG

    def start(self, bandwidth: str = "1M", duration: int = 0) -> None:
        """Offer a UDP stream toward the receiver.

        ``bandwidth`` is an offered load, not a reservation: nothing along the
        path polices or guarantees it. ``duration=0`` streams until stopped.
        """

        self.stop()
        _run(("docker", "exec", container_name(self.host), "truncate", "-s", "0", self.log))
        _run(
            (
                "docker", "exec", "-d", container_name(self.host),
                "iperf3", "-u", "-c", SERVER_ADDRESS, "-p", str(PORT),
                "-b", bandwidth,
                "-t", str(duration if duration > 0 else CONTINUOUS_SECONDS),
                "-l", str(PAYLOAD_BYTES),
                "-i", "1",
                "--forceflush", "--logfile", self.log,
            )
        )

    def stop(self) -> None:
        _run(
            ("docker", "exec", container_name(self.host), "pkill", "-f", "iperf3 -u -c"),
            allow_failure=True,
        )

    def running(self) -> bool:
        return _run(
            ("docker", "exec", container_name(self.host), "pgrep", "-f", "iperf3 -u -c"),
            allow_failure=True,
        ).returncode == 0

    def log_text(self, lines: int = 20) -> str:
        return _run(
            ("docker", "exec", container_name(self.host), "tail", "-n", str(lines), self.log),
            allow_failure=True,
        ).stdout

    def report(self, lines: int = 20) -> dict:
        return {"running": self.running(), "log_tail": self.log_text(lines)}
