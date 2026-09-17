"""Containerlab lifecycle and gNMI configuration for the packet domains.

``Lab`` covers the whole emulation environment: deploying and destroying the
Containerlab topology is shared-testbed work, not something either packet owner
does on its own. ``configure`` is scoped, so a caller can bring up only the
routers of the domain it is authorised for.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

from gnmi import Session, Target, password, username
from inventory import (
    GNMI_PORT,
    Router,
    assert_owned,
    container_name,
    router,
    routers_in,
)

HERE = Path(__file__).resolve().parent
TOPOLOGY_FILE = HERE / "topology.clab.yml"


class LabError(RuntimeError):
    """Raised when a Containerlab or Docker command cannot be completed."""


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass
class ConfigurationResult:
    """Per-router outcome, retained even when another router failed."""

    router: str
    domain: str
    ok: bool = False
    interfaces: int = 0
    routes: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Lab:
    """Deploys the topology and configures routers over gNMI."""

    def __init__(
        self,
        gnmi_username: str | None = None,
        gnmi_password: str | None = None,
        port: int = GNMI_PORT,
    ) -> None:
        self.username = username(gnmi_username)
        self.password = password(gnmi_password)
        self.port = port

    # ------------------------------------------------------ testbed lifecycle

    def deploy(self) -> CommandResult:
        return self._run(("containerlab", "deploy", "--topo", str(TOPOLOGY_FILE)))

    def destroy(self) -> CommandResult:
        return self._run(("containerlab", "destroy", "--topo", str(TOPOLOGY_FILE)))

    def status(self) -> CommandResult:
        return self._run(("containerlab", "inspect", "--topo", str(TOPOLOGY_FILE)))

    def ping_service(self, count: int = 3) -> CommandResult:
        """Probe the service path end to end from the client host.

        This is a reachability check across both packet domains and the optical
        line. It says nothing about throughput, jitter or loss under load; use
        the traffic module for that.
        """

        from inventory import CLIENT_HOST, SERVER_ADDRESS

        return self._run(
            (
                "docker",
                "exec",
                container_name(CLIENT_HOST),
                "ping",
                "-c",
                str(count),
                "-W",
                "2",
                SERVER_ADDRESS,
            ),
            allow_failure=True,
        )

    # ------------------------------------------------------- gNMI configuration

    def session(self, name: str) -> Session:
        """Open a session to one router by name."""

        specification = router(name)
        return Session(
            Target(
                host=specification.management_ip,
                port=self.port,
                username=self.username,
                password=self.password,
            )
        )

    def configure(self, domain: str | None = None) -> list[ConfigurationResult]:
        """Configure every router, or only those owned by ``domain``."""

        return [self.configure_router(item) for item in routers_in(domain)]

    def configure_named(self, domain: str, names: Iterable[str]) -> list[ConfigurationResult]:
        """Configure named routers after checking the domain owns them all."""

        names = list(names)
        assert_owned(domain, names)
        return [self.configure_router(router(name)) for name in names]

    def configure_router(self, specification: Router) -> ConfigurationResult:
        result = ConfigurationResult(
            router=specification.name, domain=specification.domain
        )
        try:
            with self.session(specification.name) as session:
                for interface in specification.interfaces:
                    try:
                        session.configure_interface(
                            interface=interface.name,
                            address=interface.address,
                            prefix_length=interface.prefix_length,
                            description=interface.description,
                        )
                        session.attach_to_default_instance(interface.name)
                        result.interfaces += 1
                    except Exception as exc:
                        result.errors.append(f"interface {interface.name}: {exc}")
                for route in specification.static_routes:
                    try:
                        session.configure_static_route(
                            prefix=route.prefix,
                            next_hop=route.next_hop,
                            metric=route.metric,
                        )
                        result.routes += 1
                    except Exception as exc:
                        result.errors.append(f"route {route.prefix}: {exc}")
        except Exception as exc:
            result.errors.append(str(exc))
            return result

        result.ok = not result.errors
        return result

    # ----------------------------------------------------------------- helpers

    @staticmethod
    def _run(command: Sequence[str], allow_failure: bool = False) -> CommandResult:
        executable = command[0]
        if shutil.which(executable) is None:
            raise LabError(f"{executable!r} is not on PATH")
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        result = CommandResult(
            tuple(command), completed.returncode, completed.stdout, completed.stderr
        )
        if not result.ok and not allow_failure:
            raise LabError(
                f"command failed ({result.returncode}): {' '.join(command)}\n"
                f"{result.stderr.strip()}"
            )
        return result
