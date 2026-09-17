#!/usr/bin/env python3
"""Command line for the packet domains.

    main.py deploy                     bring up the Containerlab topology
    main.py configure [--domain D]     push interfaces and routes over gNMI
    main.py status                     Containerlab node status
    main.py inventory [--domain D]     what each domain owns
    main.py ping [--count N]           probe client-a -> server-b
    main.py traffic start|stop|status  the UDP service flow
    main.py telemetry ROUTER           interface counters and rates
    main.py path show|backup|primary --domain D
    main.py impair up|down --domain D  lab fault control
    main.py destroy                    tear the topology down

Commands that touch a device need the lab running; `deploy` and `destroy`
additionally need Docker and Containerlab privileges.
"""

from __future__ import annotations

import argparse
import json
import sys

from backup_path import BackupPath, BackupPathError
from inventory import DOMAINS, routers_in
from lab import Lab, LabError
from telemetry import Collector
from traffic import Receiver, Sender


def emit(value) -> None:
    print(json.dumps(value, indent=2, default=str))


def cmd_deploy(args) -> int:
    result = Lab().deploy()
    print(result.stdout or "deployed")
    print("\nNext: start the optical network and bridge it in, then `configure`.")
    return 0


def cmd_destroy(args) -> int:
    result = Lab().destroy()
    print(result.stdout or "destroyed")
    return 0


def cmd_status(args) -> int:
    print(Lab().status().stdout)
    return 0


def cmd_inventory(args) -> int:
    emit(
        [
            {
                "router": item.name,
                "domain": item.domain,
                "role": item.role,
                "management_ip": item.management_ip,
                "interfaces": [
                    {"name": i.name, "address": i.ip_prefix, "description": i.description}
                    for i in item.interfaces
                ],
                "static_routes": [
                    {"prefix": r.prefix, "next_hop": r.next_hop} for r in item.static_routes
                ],
            }
            for item in routers_in(args.domain)
        ]
    )
    return 0


def cmd_configure(args) -> int:
    results = [item.to_dict() for item in Lab().configure(args.domain)]
    emit(results)
    failed = [item["router"] for item in results if not item["ok"]]
    if failed:
        print(f"\nfailed: {', '.join(failed)}", file=sys.stderr)
        return 1
    print(f"\nconfigured {len(results)} routers")
    return 0


def cmd_ping(args) -> int:
    result = Lab().ping_service(args.count)
    print(result.stdout or result.stderr)
    return 0 if result.ok else 1


def cmd_traffic(args) -> int:
    sender, receiver = Sender(), Receiver()
    if args.action == "start":
        receiver.start()
        sender.start(bandwidth=args.bandwidth, duration=args.duration)
        print(f"receiver up on server-b; offering {args.bandwidth} from client-a")
        return 0
    if args.action == "stop":
        sender.stop()
        receiver.stop()
        print("stopped")
        return 0
    emit({"sender": sender.report(), "receiver": receiver.report()})
    return 0


def cmd_telemetry(args) -> int:
    collector = Collector(args.domain)
    emit(collector.collect(args.router).to_dict())
    return 0


def cmd_path(args) -> int:
    path = BackupPath(args.domain)
    if args.action == "show":
        emit(path.state())
        return 0
    if args.action == "backup":
        emit(path.activate_backup(force=args.force))
        return 0
    emit(path.restore_primary(force=args.force))
    return 0


def cmd_impair(args) -> int:
    emit(BackupPath(args.domain).impair_primary(impaired=args.action == "down"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def with_domain(target, required: bool = False):
        target.add_argument(
            "--domain",
            choices=DOMAINS,
            required=required,
            help="restrict the operation to one packet domain",
        )
        return target

    sub.add_parser("deploy", help="bring up the Containerlab topology").set_defaults(
        run=cmd_deploy
    )
    sub.add_parser("destroy", help="tear the topology down").set_defaults(run=cmd_destroy)
    sub.add_parser("status", help="Containerlab node status").set_defaults(run=cmd_status)

    with_domain(sub.add_parser("inventory", help="what each domain owns")).set_defaults(
        run=cmd_inventory
    )
    with_domain(
        sub.add_parser("configure", help="push interfaces and routes over gNMI")
    ).set_defaults(run=cmd_configure)

    ping = sub.add_parser("ping", help="probe client-a -> server-b")
    ping.add_argument("--count", type=int, default=3)
    ping.set_defaults(run=cmd_ping)

    traffic = sub.add_parser("traffic", help="the UDP service flow")
    traffic.add_argument("action", choices=("start", "stop", "status"))
    traffic.add_argument("--bandwidth", default="1M", help="offered load, e.g. 1M")
    traffic.add_argument(
        "--duration", type=int, default=0, help="seconds; 0 streams until stopped"
    )
    traffic.set_defaults(run=cmd_traffic)

    telemetry = with_domain(
        sub.add_parser("telemetry", help="interface counters and rates"), required=True
    )
    telemetry.add_argument("router")
    telemetry.set_defaults(run=cmd_telemetry)

    path = with_domain(sub.add_parser("path", help="show or change the service path"), True)
    path.add_argument("action", choices=("show", "backup", "primary"))
    path.add_argument("--force", action="store_true", help="skip the impairment check")
    path.set_defaults(run=cmd_path)

    impair = with_domain(sub.add_parser("impair", help="lab fault control"), True)
    impair.add_argument("action", choices=("down", "up"))
    impair.set_defaults(run=cmd_impair)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.run(args)
    except (LabError, BackupPathError, PermissionError, LookupError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
