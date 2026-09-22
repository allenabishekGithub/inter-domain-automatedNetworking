# Optical line

A four-ROADM optical network, emulated with Mininet-Optical, carrying one
channel between the two [packet domains](../packet-network). It is the only
path between them.

The planned [Mininet-Optical MCP server](../docs/mcp-server-design.md) wraps
this package's control API for the Optical DSO, separately from the Containerlab
Packet MCP servers. It is not implemented; the commands below remain the current
lab interface.

```text
opt-a --- clientEdge --- t-client ==== r1 ==== r2 ==== r3 ==== r4 ==== t-server --- serverEdge --- opt-b
                                         channel 1 or 2, west to east
```

`---` is Ethernet toward a packet attachment bridge, `====` is a WDM span.

## One route, two wavelengths

The terminals are tunable. The service rides **one** wavelength at a time, and
which one is a decision this domain owns: it can offer channel 1, offer channel
2, or refuse to carry the service at all.

What it cannot do is reroute. Both channels traverse the same fibre chain, so a
wavelength is a choice of carrier, not a protection path — a span failure takes
every channel with it. An optical cut has no automatic repair here and must
surface as a degraded or unresolved service.

That distinction is the point of the fixture: the domain has a real strategy
set for **provisioning** and none at all for **restoration**, so an experiment
can exercise negotiation and truthful refusal in the same topology.

| | |
|---|---|
| Channels | 1, 2 (one carried at a time) |
| Terminal ports | Ethernet 1, WDM 11 |
| ROADM ports | add/drop 1, west 111, east 222 |
| Cross-connects | `r1: 1→222`, `r2: 111→222`, `r3: 111→222`, `r4: 111→1`, matched to the carried channel |
| Spans | 50 m, unity-gain amplifiers (0.22 dB/km), 3 dB line boost |
| Launch power | 0 dBm |
| ROADM insertion loss | 0 dB (modelled) |

`main.py spec` prints all of it from `spec.py`, which is the single source of
truth and imports nothing heavier than the standard library.

Two of those values are simplifications worth stating plainly. The emulator
models a substantial internal switching loss per ROADM that nothing in a plain
chain compensates; four in series would sink the channel, so it is zeroed and
the span amplifiers define the budget. The spans are short for the same reason:
accumulated nonlinear interference over a long chain would put gOSNR below
threshold regardless of launch power. The result is a compact, reproducible
campus-scale model that closes with margin — around 28.4 dB gOSNR — not a
calibrated long-haul link. Read its gOSNR as a modelled value.

A modelled optical margin is also not a packet measurement. If you want to
claim an optical condition affected the service, show it at the receiver.

## Prerequisites

Mininet, Mininet-Optical (`mnoptical`) and Open vSwitch, installed
system-wide, plus root. The [installation guide](../docs/installation.md) walks
through building them on a fresh Ubuntu VM, including the edits they need on
24.04. `main.py start` and `main.py clean` need all of that; every other command
only needs `requests` and talks to a running line over HTTP:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Note which interpreter has the emulator. A virtual environment built for the
client tooling does not by itself make Mininet importable by `sudo python3`.

## Start the line

Deploy the packet topology first — the attachment containers have to exist.
Then, in a terminal of its own, because this blocks:

```bash
sudo python3 main.py start --attach
```

`--attach` bridges the optical edges into the packet attachment containers. It
refuses to start if something is already serving the control API on port 8080,
rather than resetting namespaces that belong to another line.

Then, from anywhere:

```bash
python3 main.py configure                 # light the default wavelength
python3 main.py configure --channel 2     # retune the service onto channel 2
python3 main.py status                    # which channel is actually carried
python3 main.py monitor                   # per-node OSNR/gOSNR
```

`configure` clears every ROADM before programming it and retunes the terminals
on their existing WDM port. Both matter for a retune: the reset removes the old
wavelength's cross-connects, and reusing the port is what makes the emulator
clear the previous channel's forwarding rules. Without either, the old channel
would linger. It is therefore safe to re-run and safe to retune, and it
verifies the result by reading the installed rules back rather than trusting
the request.

`status` reports `carrying_channels` from that same readback, so a
half-applied or externally changed line reports what it is really doing.

### What a retune costs

Retuning a live service is not free, and the cost is measured rather than
assumed. Over one 60-second run at 1 Mbit/s with two retunes, the receiver lost
packets in exactly two one-second intervals — the two retunes — and in no
others:

| Retune | Datagrams lost | Outage |
|---|---|---|
| channel 1 → 2 | 8 / 90 (8.9%) | ~90 ms |
| channel 2 → 1 | 9 / 89 (10%) | ~100 ms |

So roughly **90–100 ms of delivery**, with the stream fully recovered by the
next interval. That figure is what belongs in a cost or utility model as the
disruption term for this action; it is a measurement on this fixture, not a
property of wavelength switching in general.

Modelled gOSNR is 28.44 dB on either channel. They are symmetric here because
only one is lit at a time, so neither carries the other's nonlinear
interference — the choice between them is an allocation decision, not a quality
trade-off, until simultaneous operation is added.

## How the attachment works

Each packet domain terminates its border gateway on a container running a Linux
bridge. This line terminates on two plain hosts. `packet_bridge.py` joins them
with a veth pair: one end becomes a port on the optical edge's bridge, the
other is moved into the container's namespace, renamed `eth2` and enslaved to
its `br0`. The edge's own address is flushed first — after bridging it is an L2
port carrying the packet domains' addressing, not an endpoint.

Three consequences worth knowing:

- It runs inside the process that owns the line. The edge namespaces exist only
  for that process's lifetime, so stopping the line detaches the domains.
- It is not repeatable. The veth surgery happens once; `--attach` is refused a
  second time. If it fails partway, restart the line rather than retrying.
- The host-side veth names are fixed, so two lines on one host would collide.

## Commands

| Command | Root | Purpose |
|---|---|---|
| `start [--attach]` | yes | Build the line and hold it |
| `clean` | yes | Remove leftover emulator state |
| `configure` | no | Program the lightpath |
| `monitor` | no | Per-node OSNR/gOSNR and the worst margin |
| `status` | no | Is the line up and configured |
| `spec` | no | The pinned topology and link budget |

`monitor` keeps a failure against its own node rather than raising, so one
unreadable monitor does not hide the readings that did come back.

## Tests

```bash
.venv/bin/python -m pytest
```

25 checks that do not need the emulator: that the cross-connect chain is
continuous end to end, that edge names fit a Linux interface name, that
`configure` clears before programming and turns the terminals on last, that it
is idempotent, that the gOSNR reduction takes the worst channel and skips a
node that failed to read rather than scoring it zero, and that the two
attachments use distinct veth names.

## Stop

Stop the line with Ctrl+C, or by signalling the process, before destroying the
packet topology. `clean` is a broad reset of leftover emulator state on the
host — do not run it against a machine with another line running.
