#!/usr/bin/env python3
"""Command line for the optical line.

    sudo main.py start [--attach]   build the line and hold it (blocks)
    main.py configure [--channel N] program (or retune) the lightpath
    main.py monitor                 per-node OSNR/gOSNR and the worst margin
    main.py status                  is the line up, and what is on it
    main.py spec                    the pinned topology and link budget
    sudo main.py clean              remove leftover emulator state

Only `start` and `clean` need root and the emulator installed. The others talk
to a running line over HTTP.

Typical order: deploy the packet topology first, then `sudo main.py start
--attach` in its own terminal, then `configure` from another.
"""

from __future__ import annotations

import argparse
import json
import sys

from client import OpticalClient, OpticalError, collect_monitors, worst_gosnr
from spec import (
    BOOST_GAIN_DB,
    CHANNELS,
    CLIENT_EDGE,
    DEFAULT_CHANNEL,
    LAUNCH_POWER_DBM,
    MONITORED_NODES,
    REST_HOST,
    REST_PORT,
    ROADMS,
    SERVER_EDGE,
    SPAN_AMP_GAIN_DB,
    SPAN_KM,
    roadm_rules,
)


def emit(value) -> None:
    print(json.dumps(value, indent=2, default=str))


def cmd_start(args) -> int:
    # Imported here so the other subcommands stay usable without the emulator.
    from topology import OpticalNetwork

    network = OpticalNetwork()
    try:
        network.start(attach_packet_network=args.attach)
    except KeyboardInterrupt:
        network.stop()
    return 0


def cmd_clean(args) -> int:
    from mininet.clean import cleanup

    cleanup()
    print("emulator state cleaned")
    return 0


def cmd_configure(args) -> int:
    client = OpticalClient()
    previous = client.carried_channels()
    client.configure_line(args.channel)
    carried = client.carried_channels()
    if carried != [args.channel]:
        print(
            f"requested channel {args.channel} but the line reports {carried}",
            file=sys.stderr,
        )
        return 1
    margin, _per_node = worst_gosnr(collect_monitors(client))
    verb = "retuned from " + str(previous[0]) if previous and previous != carried else "configured"
    print(f"channel {args.channel} {verb} across {len(ROADMS)} ROADMs")
    if margin is not None:
        print(f"worst modelled gOSNR: {margin:.2f} dB")
    return 0


def cmd_monitor(args) -> int:
    readings = collect_monitors()
    margin, per_node = worst_gosnr(readings)
    emit(
        {
            "worst_gosnr_db": margin,
            "per_node_gosnr_db": per_node,
            "readings": readings,
        }
    )
    return 0


def cmd_status(args) -> int:
    client = OpticalClient()
    if not client.reachable():
        print(f"no optical line answering on {client.base_url}", file=sys.stderr)
        return 1
    margin, _per_node = worst_gosnr(collect_monitors(client))
    carried = client.carried_channels()
    emit(
        {
            "control_api": client.base_url,
            "nodes": client.nodes().get("nodes", {}),
            "monitored": list(MONITORED_NODES),
            "supported_channels": list(CHANNELS),
            "carrying_channels": carried,
            "worst_gosnr_db": margin,
            "configured": bool(carried),
        }
    )
    return 0


def cmd_spec(args) -> int:
    emit(
        {
            "path": f"{CLIENT_EDGE} - t-client = {' = '.join(ROADMS)} = t-server - {SERVER_EDGE}",
            "supported_channels": list(CHANNELS),
            "default_channel": DEFAULT_CHANNEL,
            "control_api": f"http://{REST_HOST}:{REST_PORT}",
            "link_budget": {
                "span_km": SPAN_KM,
                "span_amplifier_gain_db": SPAN_AMP_GAIN_DB,
                "boost_gain_db": BOOST_GAIN_DB,
                "launch_power_dbm": LAUNCH_POWER_DBM,
            },
            "cross_connects": {
                str(channel): [
                    {
                        "node": rule.node,
                        "in": rule.port_in,
                        "out": rule.port_out,
                        "channels": rule.channels,
                    }
                    for rule in roadm_rules(channel)
                ]
                for channel in CHANNELS
            },
            # Every channel rides the same fibre chain, so a wavelength is a
            # choice of carrier, not a protection path.
            "alternate_route": None,
        }
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="build the line and hold it (blocks)")
    start.add_argument(
        "--attach",
        action="store_true",
        help="also bridge the edges into the packet attachment containers",
    )
    start.set_defaults(run=cmd_start)

    sub.add_parser("clean", help="remove leftover emulator state").set_defaults(
        run=cmd_clean
    )
    configure = sub.add_parser("configure", help="program or retune the lightpath")
    configure.add_argument(
        "--channel", type=int, default=DEFAULT_CHANNEL, choices=CHANNELS,
        help="which wavelength carries the service",
    )
    configure.set_defaults(run=cmd_configure)
    sub.add_parser("monitor", help="per-node OSNR/gOSNR").set_defaults(run=cmd_monitor)
    sub.add_parser("status", help="is the line up").set_defaults(run=cmd_status)
    sub.add_parser("spec", help="the pinned topology and link budget").set_defaults(
        run=cmd_spec
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.run(args)
    except OpticalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
