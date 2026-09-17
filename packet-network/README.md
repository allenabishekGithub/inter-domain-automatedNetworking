# Packet domains

Two independently owned packet networks, emulated with Containerlab and eight
Nokia SR Linux routers, either side of the [optical line](../optical-network).
Together with that line they carry one UDP service from `client-a` in Packet A
to `server-b` in Packet B.

```text
            Packet A                                        Packet B
 client-a --- pe-a1 ---+--- p-a1 ---+--- gw-a      gw-b ---+--- p-b1 ---+--- pe-b1 --- server-b
                       |            |                |       |          |
                       +--- p-a2 ---+              opt-a    +--- p-b2 --+
                          (backup)                   |         (backup)
                                                  optical
                                                     |
                                                   opt-b
```

`opt-a` and `opt-b` are transparent L2 bridges. `gw-a` (10.10.4.1/30) and
`gw-b` (10.10.4.2/30) sit on one /30 that spans the optical line, so the two
gateways are IP-adjacent while every packet between them crosses four ROADMs.
There is no shortcut between the bridges: without the optical line attached and
configured, the two packet domains cannot reach each other at all.

## What each domain owns

| | Packet A | Packet B |
|---|---|---|
| Edge | `pe-a1` | `pe-b1` |
| Primary core | `p-a1` | `p-b1` |
| Backup core | `p-a2` | `p-b2` |
| Border gateway | `gw-a` | `gw-b` |
| Endpoint | `client-a` 10.10.0.2/24 | `server-b` 10.20.0.2/24 |
| Attachment bridge | `opt-a` | `opt-b` |

`inventory.py` is the source of truth for all of it. Every router carries the
domain that owns it, and `assert_owned` is called at the boundary of any scoped
operation, so a tool authorised for one domain cannot name the other's routers:

```console
$ python main.py telemetry --domain packet-a gw-b
error: packet-a is not authorised for: gw-b
```

That check is a scoping guard inside this package, not an isolation boundary.
Both domains are emulated on one host by one process with access to the
container runtime, so anything that can reach the runtime can reach every node.
Treat the separation here as administrative.

## Forwarding

Routing is static, installed over gNMI from `inventory.py`. There is no IGP, no
BGP, no BFD and no fast reroute, which is deliberate: nothing in the data plane
reconverges on its own, so every path change is an explicit, observable
decision made above it.

Each route points at a single-member next-hop group named after its next hop
(`nhg-10-10-1-2`). Changing path therefore rewrites one leaf per router rather
than replacing a route.

There is no QoS mechanism here: no classifier, scheduler, policer or queue is
configured on any router. The offered rate of the UDP flow is an offered rate,
not a reservation, and nothing along the path treats one flow differently from
another.

## Prerequisites

Docker, Containerlab, and the two images
(`ghcr.io/nokia/srlinux:24.10.1`, `alpine:3.20`). Starting from a fresh Ubuntu
VM, the [installation guide](../docs/installation.md) covers all of it. Then,
from this directory:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`deploy`, `destroy` and the optical attachment need root; the rest only needs
the management network, which is reachable from the host.

## Bring up the service

```bash
sudo .venv/bin/python main.py deploy       # 1. the topology
# 2. start and attach the optical line -- see ../optical-network/README.md
.venv/bin/python main.py configure         # 3. interfaces and routes
.venv/bin/python main.py ping              # 4. reachability
.venv/bin/python main.py traffic start     # 5. the UDP service
```

Step 3 has to follow step 2: the routers come up fine without the optical line,
but nothing crosses between the domains until the bridges are joined.
`../scripts/service-up.sh` runs the whole sequence.

The first `ping` after the line is attached often loses a packet or two while
the bridges learn addresses. Probe again before treating that as a fault.

## Commands

| Command | Purpose |
|---|---|
| `deploy` / `destroy` / `status` | Containerlab lifecycle for the shared testbed |
| `inventory [--domain D]` | What a domain owns, with addresses and routes |
| `configure [--domain D]` | Push interfaces and routes over gNMI |
| `ping [--count N]` | Probe `client-a` -> `server-b` |
| `traffic start\|stop\|status` | The UDP service flow |
| `telemetry --domain D ROUTER` | Interface counters and derived rates |
| `path show\|backup\|primary --domain D` | Read or change a domain's service path |
| `impair down\|up --domain D` | Lab fault control |

Everything prints JSON on stdout and diagnostics on stderr, so output can be
piped.

## Changing path

Each domain has exactly one forwarding action: move its two service routes onto
its backup core router, and back. Both directions move together, and the
optical attachment is never touched — a domain on its backup path still uses
the same lightpath.

| Domain | Router / destination | Primary | Backup |
|---|---|---|---|
| Packet A | `pe-a1` / 10.20.0.0/24 | 10.10.1.2 | 10.10.1.6 |
| Packet A | `gw-a` / 10.10.0.0/24 | 10.10.2.1 | 10.10.3.1 |
| Packet B | `gw-b` / 10.20.0.0/24 | 10.20.2.2 | 10.20.3.2 |
| Packet B | `pe-b1` / 10.10.0.0/24 | 10.20.1.1 | 10.20.1.5 |

A switch is refused unless the domain is wholly on its primary path, its backup
core router is up, and its primary is actually impaired. A return is refused
while the primary is still impaired. `--force` overrides only the impairment
check, for rehearsing on an undamaged lab.

Each write is read back, and a domain that ends up with its two routes
disagreeing reports `mixed` and refuses to move again until that is reconciled.
Nothing here is atomic across routers: if the second write fails the first has
already happened. A caller that needs a transaction has to build one on top.

## Injecting a fault

`impair down --domain packet-a` disables `gw-a`'s primary-facing port. The far
end, `p-a1`, then reports a link that went away — which is what readiness reads.
The fault and the observation are on different routers on purpose: a check that
read back the admin state it had just set would prove nothing about the
network.

```console
$ python main.py impair down --domain packet-a
$ python main.py path show --domain packet-a   # primary_degraded: true, observed on p-a1
$ python main.py path backup --domain packet-a
$ python main.py impair up --domain packet-a
$ python main.py path primary --domain packet-a
```

## Measuring the service

`traffic status` reports both ends. Only the receiver establishes delivery —
sender throughput shows that packets left `client-a`, not that any arrived, so
health checks should read the receiver block.

Each receiver interval carries an `identity` (`"11.00-12.00"`). That is the
reliable freshness signal: the endpoint image's `stat` has no sub-second
format, so `log_modified_at` is whole seconds and cannot order a sample against
an event in the same second. To prove a sample is post-event, record the event
time yourself and wait for an identity you have not seen.

Counters from `telemetry` are cumulative. The collector holds the previous
reading per interface and only reports a rate once it has two; a single call
gives counters and `null` rates, which is correct rather than a gap.

## Tests

```bash
.venv/bin/python -m pytest
```

46 checks, none of which need a lab. They verify that the inventory agrees with
the wiring, that every next hop is on a connected subnet owned by another
router, that each /30 has exactly two ends, that no interface is addressed
without being cabled, that domain scoping holds, and that the path-change
decisions behave — including that the fault is injected on a different router
than the one readiness observes.

## Shut down

```bash
.venv/bin/python main.py traffic stop
sudo .venv/bin/python main.py destroy
```

Stop the optical line before destroying this topology, and use the topology
file rather than a global Containerlab cleanup so unrelated labs on the host
are left alone.
