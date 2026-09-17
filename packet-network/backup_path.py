"""The named backup-path action each packet domain can perform locally.

Every packet domain carries the service over a primary core router and keeps a
second, already-cabled core router in reserve. The only forwarding change a
domain can make is to move its two service routes from the primary next hop to
the backup one, and back again. There is no generic "configure a route" verb
here on purpose: a domain's action space is a short list of named procedures,
so a caller can only ask for something the owner has already declared.

Each domain switches both directions of the service, using the two routers that
sit at the edges of its own core:

    Packet A   pe-a1 / 10.20.0.0/24   client -> server
               gw-a  / 10.10.0.0/24   server -> client
    Packet B   gw-b  / 10.20.0.0/24   client -> server
               pe-b1 / 10.10.0.0/24   server -> client

The optical attachment is untouched by either action. A domain on its backup
path is still reachable over exactly the same lightpath.

Nothing in this module is atomic across devices. It reads state, checks it,
writes one leaf per router, and reads the result back; if the second write
fails the first has still happened, and ``state()`` will report ``mixed``.
Callers that need a transaction must build one above this layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gnmi import Session, Target, password, username
from inventory import (
    GNMI_PORT,
    PACKET_A,
    PACKET_B,
    assert_domain,
    next_hop_group,
    router,
)

PRIMARY = "primary"
BACKUP = "backup"
MIXED = "mixed"


@dataclass(frozen=True)
class RouteTarget:
    """One route a domain repoints when it changes path."""

    router: str
    prefix: str
    primary_next_hop: str
    backup_next_hop: str

    def next_hop(self, path: str) -> str:
        return self.primary_next_hop if path == PRIMARY else self.backup_next_hop


# What each domain is allowed to change, and nothing else.
TARGETS: dict[str, tuple[RouteTarget, ...]] = {
    PACKET_A: (
        RouteTarget("pe-a1", "10.20.0.0/24", "10.10.1.2", "10.10.1.6"),
        RouteTarget("gw-a", "10.10.0.0/24", "10.10.2.1", "10.10.3.1"),
    ),
    PACKET_B: (
        RouteTarget("gw-b", "10.20.0.0/24", "10.20.2.2", "10.20.3.2"),
        RouteTarget("pe-b1", "10.10.0.0/24", "10.20.1.1", "10.20.1.5"),
    ),
}


@dataclass(frozen=True)
class Readiness:
    """The core routers whose interface state decides whether a switch is sane."""

    primary_router: str
    backup_router: str
    interfaces: tuple[str, ...]


READINESS: dict[str, Readiness] = {
    PACKET_A: Readiness("p-a1", "p-a2", ("ethernet-1/1", "ethernet-1/2")),
    PACKET_B: Readiness("p-b1", "p-b2", ("ethernet-1/1", "ethernet-1/2")),
}


# Lab experiment control, not a domain action. Disabling a gateway-facing port
# takes the far end's carrier down, so the primary core router reports a
# degraded link it did not administer itself. Reading a propagated oper-state is
# a real observation; reading back an admin-state you just set is not.
IMPAIRMENT: dict[str, tuple[str, str]] = {
    PACKET_A: ("gw-a", "ethernet-1/1"),
    PACKET_B: ("gw-b", "ethernet-1/2"),
}


class BackupPathError(RuntimeError):
    """Raised when a path change is refused or cannot be completed."""


class BackupPath:
    """Reads and changes one domain's service path."""

    def __init__(
        self,
        domain: str,
        gnmi_username: str | None = None,
        gnmi_password: str | None = None,
        port: int = GNMI_PORT,
    ) -> None:
        assert_domain(domain)
        self.domain = domain
        self.username = username(gnmi_username)
        self.password = password(gnmi_password)
        self.port = port

    @property
    def targets(self) -> tuple[RouteTarget, ...]:
        return TARGETS[self.domain]

    def _session(self, name: str) -> Session:
        specification = router(name)
        return Session(
            Target(
                host=specification.management_ip,
                port=self.port,
                username=self.username,
                password=self.password,
            )
        )

    # ------------------------------------------------------------- observation

    # The three methods below are the only ones that touch a device. Everything
    # else in this class decides what should happen; a test or a dry run can
    # substitute these without reimplementing any of that decision logic.

    def _route(self, target: RouteTarget) -> dict[str, Any]:
        with self._session(target.router) as session:
            return session.configured_route(target.prefix)

    def _interface_up(self, name: str, interface: str) -> bool:
        with self._session(name) as session:
            return session.interface_oper_state(interface) == "up"

    def _write_route(
        self, target: RouteTarget, group: str, next_hop: str
    ) -> dict[str, Any]:
        """Repoint one route and return what the device reports afterwards."""

        with self._session(target.router) as session:
            session.set_route_next_hop_group(target.prefix, group, next_hop=next_hop)
            return session.configured_route(target.prefix)

    def readiness(self) -> dict[str, Any]:
        """Whether the backup is usable and the primary is currently impaired."""

        spec = READINESS[self.domain]
        backup = [self._interface_up(spec.backup_router, i) for i in spec.interfaces]
        primary = [self._interface_up(spec.primary_router, i) for i in spec.interfaces]
        return {
            "backup_ready": all(backup),
            "primary_degraded": not all(primary),
            "basis": (
                f"observed interface state on {spec.primary_router} "
                f"and {spec.backup_router}"
            ),
        }

    def state(self) -> dict[str, Any]:
        """This domain's current path, routes and readiness."""

        routes = {target.router: self._route(target) for target in self.targets}
        on_primary = all(
            routes[t.router].get("next-hop-group") == next_hop_group(t.primary_next_hop)
            for t in self.targets
        )
        on_backup = all(
            routes[t.router].get("next-hop-group") == next_hop_group(t.backup_next_hop)
            for t in self.targets
        )
        return {
            "domain": self.domain,
            "path": PRIMARY if on_primary else BACKUP if on_backup else MIXED,
            "routes": routes,
            **self.readiness(),
        }

    # ------------------------------------------------------------------ actions

    def activate_backup(self, force: bool = False) -> dict[str, Any]:
        """Move this domain's service routes onto its backup core router.

        Refused unless the domain is wholly on its primary path and the backup
        is up. It is also refused while the primary looks healthy, because this
        is a repair action and not a general-purpose optimiser -- ``force``
        overrides that one check for a rehearsal on an undamaged lab.
        """

        return self._move_to(BACKUP, force=force)

    def restore_primary(self, force: bool = False) -> dict[str, Any]:
        """Move this domain's service routes back onto its primary core router.

        Refused while the primary is still impaired unless ``force`` is set,
        so a return does not put the service back onto a broken link.
        """

        return self._move_to(PRIMARY, force=force)

    def _move_to(self, path: str, force: bool) -> dict[str, Any]:
        before = self.state()
        origin = PRIMARY if path == BACKUP else BACKUP

        if before["path"] == path:
            return {**before, "changed": False, "detail": f"already on {path}"}
        if before["path"] != origin:
            raise BackupPathError(
                f"{self.domain} is on a {before['path']} path; "
                f"reconcile it before moving to {path}"
            )
        if path == BACKUP:
            if not before["backup_ready"]:
                raise BackupPathError(f"{self.domain} backup core router is not up")
            if not before["primary_degraded"] and not force:
                raise BackupPathError(
                    f"{self.domain} primary is not impaired; "
                    "pass force to switch anyway"
                )
        elif before["primary_degraded"] and not force:
            raise BackupPathError(
                f"{self.domain} primary is still impaired; "
                "pass force to return anyway"
            )

        changed = []
        for target in self.targets:
            next_hop = target.next_hop(path)
            group = next_hop_group(next_hop)
            readback = self._write_route(target, group, next_hop)
            if readback.get("next-hop-group") != group:
                raise BackupPathError(
                    f"readback on {target.router} still shows "
                    f"{readback.get('next-hop-group')!r}; applied: {changed}"
                )
            changed.append(target.router)

        after = self.state()
        if after["path"] != path:
            raise BackupPathError(
                f"{self.domain} ended on a {after['path']} path after moving to {path}"
            )
        return {**after, "changed": True, "routers": changed}

    # ------------------------------------------------------- lab fault control

    def impair_primary(self, impaired: bool = True) -> dict[str, Any]:
        """Take this domain's primary core link down, or bring it back up.

        This belongs to whoever is running the experiment, not to the service.
        It disables the gateway-side port so the far end observes a link that
        went away rather than one it disabled itself.
        """

        name, interface = IMPAIRMENT[self.domain]
        with self._session(name) as session:
            session.update(
                f"/interface[name={interface}]",
                {"admin-state": "disable" if impaired else "enable"},
            )
        return {
            "domain": self.domain,
            "router": name,
            "interface": interface,
            "admin_state": "disable" if impaired else "enable",
        }
