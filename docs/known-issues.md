# Known issues and follow-up work

**Status:** open findings from the repository assessment on 17 September 2026,
against commit `57755d478efb1984fc3438eca8d6342c31e441ca`. Recording a finding
here does not mean it has been fixed. Retain its ID when implementing a fix and
record the resolving commit and verification evidence before closing it.

The assessment reviewed source and documentation and ran all 86 existing tests
(46 packet, 40 optical), which passed. Additional synthetic inputs and mocked
device boundaries reproduced several gaps below. Docker, Containerlab, Open
vSwitch, Mininet and Mininet-Optical were unavailable on the assessment host;
live forwarding, recovery and optical performance were **not verified**.

**Workspace clarification, 22 September 2026:** the current VM is for planning,
design and optimization. Missing lab dependencies here are expected; the earlier
assessment's environment inventory records a limit on its evidence, not a
requirement to prepare this VM as a validation host. Follow the
[planning and design priorities](implementation-roadmap.md#planning-and-design-priorities)
to document each finding's intended behavior, alternatives, chosen approach,
implementation dependencies and acceptance criteria. Keep design resolution,
implementation status and validation evidence distinct. Execute the required
checks in the designated implementation/testbed environment before closing an
item that depends on those checks.

“Reproduced” below means local logic exercised with synthetic input or fake
devices, not a fault observed on a deployed network. “Source review” identifies
a code path and its consequences without exercising it against a live lab.
Priorities concern the next reliable research demonstration: **high** findings
can disrupt a lab or undermine recovery/measurement evidence; **medium** findings
need resolution before callers rely on stronger automation guarantees.

| ID | Priority | Finding | Status |
| --- | --- | --- | --- |
| F1 | High | Optical lifecycle operations are insufficiently scoped to this instance | Open |
| F2 | High | Backup activation depends on the impaired router answering gNMI | Open |
| F3 | High | Telemetry can silently discard response structures | Open |
| F4 | High | Receiver samples do not establish freshness or post-event delivery | Open |
| F5 | High | Startup and shutdown can report misleading outcomes | Open |
| F6 | Medium | Partial packet application has no durable reconciliation | Open |
| F7 | Medium | Repeated optical configuration repeats disruptive operations | Open |
| F8 | Medium | Optical configured status does not establish service health | Open |
| F9 | Medium | Attachment failures can leave resources behind or go unreported | Open |
| F10 | Medium | CLI output, error handling and rate sampling are inconsistent | Open |

**F1 — Scope optical lifecycle operations to their owning instance.**

Source review: `OpticalNetwork.start()` calls global Mininet `cleanup()` after
checking only whether port 8080 is occupied. An unrelated Mininet network
without that listener is not protected by the check. Shutdown signals PIDs from
a file without checking their identity and uses `pkill -f 'main\.py start
--attach'`, which can match another checkout. A stale PID may have been reused.

Track owned processes and resources, validate process identity before signalling,
and keep broad cleanup an explicit maintenance operation on an exclusive host.
**Close when:** starting/stopping one instance leaves an unrelated fixture
untouched, and a stale PID cannot cause an unrelated process to be signalled.
Use isolated test fixtures to verify these cases.

Sources: [optical lifecycle](../optical-network/topology.py),
[startup](../scripts/service-up.sh), [shutdown](../scripts/service-down.sh).

**F2 — Represent unavailable primary-router evidence explicitly.**

Reproduced: with readable edge routes and a healthy backup, a simulated gNMI
failure on `p-a1` made `activate_backup()` raise before any write. `readiness()`
requires both primary and backup core routers to answer. `--force` is evaluated
only after that read, so it cannot bypass the failure. The existing injected
gateway-port fault is a narrower supported case: the primary router still
answers management requests.

Distinguish up, down and unknown observations, and define whether corroborating
evidence from surviving peers can authorize repair. Do not equate a management
timeout with a failed forwarding path. **Close when:** link failure, primary
router unavailability and management-only failure each produce an explicit,
tested action or deferral according to policy.

Source: `readiness()`, `state()` and `_move_to()` in
[backup_path.py](../packet-network/backup_path.py).

**F3 — Normalize telemetry responses and report incomplete coverage.**

Reproduced: a response whose update has
`path: interface[name=ethernet-1/1]/statistics` and
`val: {"in-octets": "1000"}` yields no counters. A nested response using
`srl_nokia-interfaces:statistics` also yields none. `extract()` expects a literal
`name` and `statistics` object; it neither uses path keys for interface identity
nor strips module prefixes. The nested unprefixed fixture in the tests passes.
The exact response from the pinned live SR Linux image still needs capture.

Normalize paths and module prefixes, preserve missing-data reasons, and add
recorded device-response fixtures. **Close when:** the supported response
structures produce correctly attributed counters, while malformed or incomplete
responses cannot silently appear to be complete observations.

Sources: [telemetry parser](../packet-network/telemetry.py),
[gNMI adapter](../packet-network/gnmi.py).

**F4 — Make receiver evidence session-aware and time-bounded.**

Reproduced: a log ending with a whole-run `0.00-10.00 ... receiver` summary
returns that summary as `latest`, replacing the final `9.00-10.00` interval.
In the probe, this replaces 2.2% interval loss with 0.22% whole-run loss.
`Receiver.report()` also returns stored samples when the server process is
running but its traffic log is old. The interval identity contains only relative
start/end times and therefore repeats across sessions.

Separate interval and summary records; add session identity, observation times
and explicit freshness. An unseen interval alone does not prove post-event
delivery: it may have been missed by earlier polling or may straddle the event.
**Close when:** summaries cannot replace interval evidence, restarted sessions
have distinct identities, stale/no-traffic reports are explicit, and recovery
verification requires the specified observation window after the event.

Source: `parse_intervals()`, `Sample.identity` and `Receiver.report()` in
[traffic.py](../packet-network/traffic.py).

**F5 — Verify lifecycle completion and preserve failure status.**

Source review: startup deploys packet resources before checking the optical
port and has no cleanup trap for partial failure. It announces service success
after detached traffic launch without waiting for fresh receiver delivery; the
preceding ping establishes only earlier reachability. The optical process
publishes its API before attachment finishes, while the shell script treats API
availability as the signal to check attachment ports, creating a potential race.

Shutdown does not aggregate failures: a failed topology destroy can be followed
by a successful final `cat`, yielding exit status zero. Its listener check
matches only `127.0.0.1:8080`, unlike the broader startup check.

Add preflight checks, explicit attachment readiness, bounded receiver
verification, cleanup of owned partial resources and aggregated exit status.
Subprocess calls also need deadlines so hung commands cannot stall completion
indefinitely. **Close when:** failure at each startup/shutdown stage produces a
truthful result, delayed attachment is handled, and failed cleanup returns
nonzero with the remaining resources identified.

Sources: [startup](../scripts/service-up.sh),
[shutdown](../scripts/service-down.sh),
[optical lifecycle](../optical-network/topology.py),
[traffic processes](../packet-network/traffic.py).

**F6 — Add durable receipts and explicit packet reconciliation.**

Reproduced: failure on the second route write leaves the first applied and the
next readable path state is `mixed`. Both named moves then refuse further work.
There is no dedicated reconciliation operation, durable receipt, operation key
or compensation journal. A transport exception does not return a structured
record of previous successful writes. `state()` itself can fail if its readiness
queries cannot complete.

Non-atomic multi-router application is already a declared limitation. Add
durable progress and explicit recovery without claiming atomic hardware changes.
**Close when:** a second-write failure, lost response and adapter restart retain
enough evidence to reconcile or report unresolved state without blindly
repeating effects. Verify delivered traffic independently of configured route
references. This work belongs with the roadmap's controller transaction phase.

Sources: [backup path operations](../packet-network/backup_path.py),
[controller transaction roadmap](implementation-roadmap.md#phase-2--local-controller-mcp-server-and-transaction-safety).

**F7 — Avoid disruptive optical writes when retaining a verified channel.**

Reproduced: requesting channel 1 twice causes the second call to issue four
ROADM resets and 12 mutating HTTP requests. The test named
`test_is_safe_to_run_twice` checks repeated request sequences, not delivery
continuity or absence of duplicate effects. A failure partway through the
sequence can leave partial configuration without compensation.

Add a verified retain-current path and define reconciliation after uncertain
application. **Close when:** repeating a verified unchanged request avoids
resets, an actual retune is verified at the receiver, and failures at each step
produce explicit partial/unresolved outcomes. Do not describe final-state
convergence as disruption-free retry behavior.

Sources: `configure_line()` in [client.py](../optical-network/client.py),
[optical tests](../optical-network/tests/test_optical.py).

**F8 — Separate observed optical configuration from verified health.**

Reproduced: five failed monitors plus a receiving-terminal entry for channel 99
at −10 dB still produce `configured: true` and exit status zero. This synthetic
case establishes the flag's limited meaning, not an observed live failure.
`carried_channels()` reads numeric keys from the receiving terminal's monitor;
it does not read installed ROADM rules. The code explicitly avoids `/rules`
because of an upstream handler problem.

Health evaluation needs supported-channel checks, required monitor coverage,
freshness, a defined quality threshold and relevant directional/packet evidence.
**Close when:** missing or contradictory evidence yields explicit unknown or
degraded health, and service verification cannot infer success from `configured`
alone. Preserve valid partial monitor observations and their errors.

Sources: `carried_channels()` and `collect_monitors()` in
[client.py](../optical-network/client.py), `cmd_status()` in
[main.py](../optical-network/main.py).

**F9 — Check attachment commands and unwind partial setup.**

Source review: optical-edge `edge.cmd()` calls do not check command status.
Network startup has no `try/finally` covering topology creation, API startup and
attachment, so an exception before the signal-wait phase can skip teardown.
The one-shot attachment has no progress record for unwinding a partial attempt.

Check namespace operations and track each owned resource as it is created.
**Close when:** simulated failures at each attachment stage return a clear error
and either remove owned partial resources or identify what remains for cleanup,
without requiring an indiscriminate global reset.

Sources: `attach_edge()` in [packet_bridge.py](../optical-network/packet_bridge.py),
`start()` and `stop()` in [topology.py](../optical-network/topology.py).

**F10 — Define a consistent machine-readable CLI contract.**

Reproduced: packet `configure` prints JSON followed by a success sentence on
stdout, causing JSON decoding to fail with extra data. A simulated
`TrafficError` escapes `main()`'s error handler; gNMI runtime errors are also
outside its listed exception types. Source review: each telemetry invocation
creates a new collector and takes one sample, so repeatedly launching the CLI
never produces rates despite the library supporting deltas across reads.

Define structured results and errors, send diagnostics to stderr, and provide
a sampling mode or persistent collector. **Close when:** documented JSON
commands decode as a single result, expected operational failures have stable
exit/error behavior, and rate collection uses at least two observations while
preserving null for unavailable or reset counters.

Sources: [packet CLI](../packet-network/main.py),
[telemetry collector](../packet-network/telemetry.py),
[packet CLI documentation](../packet-network/README.md).

**Additional follow-up work**

These are declared capability gaps or evidence/documentation tasks rather than
additional reproduced runtime defects. They remain open.

- **C1 — Enforce domain authority below the caller.** Shared credentials,
  optional caller-side scoping, skipped gNMI certificate verification and host
  runtime privileges currently define a trusted lab, not operator isolation.
  The optical client uses unauthenticated HTTP; verify the actual API binding
  against the pinned upstream server. Introduce separate domain identities,
  credentials and enforced controller scopes before claiming sovereignty.
  Verify wrong-domain denial at the MCP, adapter and device boundaries, and
  exclude global bootstrap powers from runtime DSOs. See the
  [control boundary](data-plane.md#control-boundary).
- **C2 — Retain reproducible live evidence.** No tracked run bundle supports
  independent reproduction of the reported retune loss/gOSNR pilot. Archive
  raw receiver data, fault/action times, route and monitor observations, host
  details, dependency versions, image digests and upstream patches. Aggregate
  packet loss can estimate equivalent lost delivery time, but does not alone
  establish a contiguous 90–100 ms outage. Close this item with a reproducible
  deploy–traffic–retune–packet-repair–optical-cut–teardown run and independent
  outcome checks. This validates the fixture, not the still-unimplemented DSO
  federation. See the [artifact plan](experimental-validation.md#11-reproducibility-package-and-result-schemas).
- **C3 — Align documentation and experiment scope.** Update remaining fixed
  channel-1/four-candidate descriptions to match the two-channel/eight-candidate
  fixture; remove claims of an existing packet journal or installed optical-rule
  readback; update the optical test count from 25 to 40 at this snapshot. Resolve
  scope descriptions across the richer simulator, present single-flow emulation,
  and allocation-capable emulation to implement. The 23 September revision makes
  ACO, PSO, Nash bargaining, and continual predictor learning required; B0 uses
  learning, and B1 disables generative calls without disabling the numerical
  learner. Validate the revised node mapping, component ablations, actual
  continuous allocation, and chronological learning evidence. Define a policy-approved
  packet provisioning action for healthy-path selection rather than relying on
  a repair command's rehearsal `--force` flag. Close with consistent capability
  and study profiles across the [architecture](domain-agent-architecture.md),
  [node catalogue](langgraph-node-catalog.md), [data-plane specification](data-plane.md),
  [installation guide](installation.md), component READMEs and
  [validation plan](experimental-validation.md).

Resolve F1–F5 before treating fixture output as reliable automated experiment
evidence. Resolve F6–F10 and C1 alongside the scoped adapters and assurance
workflows. C2 and C3 are required before freezing the study's claims and run
manifests. A finding may instead be retained as an explicit unsupported
capability, provided affected experiments and claims exclude it; passing the
existing unit suite alone does not close these items.
