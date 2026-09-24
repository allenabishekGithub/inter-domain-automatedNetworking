# Paper 2 — System design

**Scope:** what Paper 2 adds to Paper 1's system.
**Canonical source:** [`paper-1-federated-evidence/design.md`](../paper-1-federated-evidence/design.md)
is the base system and is authoritative for everything inherited. This document
is authoritative for Paper 2's additions.

---

## 0. At a glance

| | |
| --- | --- |
| Adds to Paper 1 | A third, **timer-triggered** graph: 6 new nodes + 1 new gate |
| New action | `set_offered_rate(mbps)` on `packet-a-mcp` only |
| New tables | `tick`, `control_state` |
| Claims | **C9** compensation, **C10** stability |
| Gating premise | Rate reduction must actually reduce loss — additional check during Paper 1's Phase 1 (§10) |

**The argument in one line.** Under Paper 1's action space the loss terms are
separable, so no domain can help another; exactly one capability breaks that,
and it is unusable without the peer's evidence.

---

## 1. What is inherited, unchanged

Paper 1 delivers all of this and Paper 2 changes none of it:

| Inherited | Summary |
| --- | --- |
| Three agents, one per owner | Sovereign, no agent above them, any may refuse |
| Eight joint configurations | Packet A path × channel × Packet B path; enumerated exactly |
| A2A peer communication | Agent Cards, task per peer per episode, six exchanges |
| The three gates | `feasibility` (live observation), `policy` (declared rules), `agreement` (byte-identical unanimity) |
| SIMAP | Two-layer service–infrastructure map, federated by signed slices |
| Segment attribution | Four-segment exact decomposition from bracketing interface counters |
| RLS predictors, S0–S3 sharing | Online ridge regression with forgetting; four disclosure conditions |
| MCP servers | Three endpoints; device credentials held there, not in the agent |
| Security | mTLS, signed and bound exchanges, hash-chained journal |

Paper 2 adds a **control layer on top**, and one new named action.

---

## 2. The problem: the action space is separable

End-to-end loss decomposes as `1 − (1 − l_A)(1 − l_attach)(1 − l_B)`. Under the
inherited action space the terms are independent:

| Agent | Action | Affects |
| --- | --- | --- |
| Packet A | primary ↔ backup core | `l_A` only |
| Optical | channel 1 ↔ 2 | **nothing measurable** — gOSNR is decoupled from packet loss |
| Packet B | primary ↔ backup core | `l_B` only |

**No domain's action reduces another's term.** If Packet A degrades and cannot
repair itself, switching a wavelength or a far-end core router recovers nothing.
Each domain minimising its own term is already globally optimal, so there is
nothing to coordinate about.

This is provable from the fixture rather than observed, and stating it is part
of the paper's contribution: *cooperative assurance requires a coupling
mechanism, and most multi-domain topologies do not obviously have one.*

---

## 3. The coupling mechanism: sender rate adaptation

**One action breaks the separability.** Packet A owns the sender and therefore
the offered load. Where the impairment is **congestion** — a rate-limited link
with a queue, not random drop — reducing offered load reduces loss *downstream
as well as locally*. Packet A's action now moves `l_attach` and `l_B`.

> **The sender is owned by Packet A. The evidence that the rate should change is
> owned by Packet B.** The control action does not merely benefit from
> federation — it does not exist without it.

### 3.1 What it is not

`set_offered_rate` is a **closed-loop assurance control**: one variable, one
feedback signal, no optimiser. It is **not** a provisioning choice and **not** a
search dimension.

The negotiated candidate space stays at **eight configurations**. Rate is a
scalar regulated inside whichever configuration is in force. Nothing here
reintroduces a need for population-based optimisation.

### 3.2 Multi-objective QoS

Reducing rate trades delivered throughput against loss ratio. The intent already
carries `min_delivered_ratio` and `max_loss_ratio`, so a service can now fail in
**two directions** — which is what makes "maintain end-to-end QoS" a decision
rather than a lookup.

---

## 4. Continuous operation

Provisioning is an episode. **Assurance is a loop that never stops.** Each agent
runs its own loop on its own period:

```text
every period:
    refresh local observations
    publish a state summary to peers          (content and rate are decisions)
    ingest peer summaries and outcomes
    attribute current quality to a segment
    act, inform, escalate, or hold
```

Three properties, each a measurement:

- **Nobody is in charge.** No global tick. Agents observe, decide and act on
  their own schedules, so evidence always arrives late and partial.
- **Disclosure becomes a rate**, not just a content choice. "What to disclose"
  gains "how often". Sharing everything every second and sharing a summary on
  threshold crossing have very different costs and possibly similar value.
- **Holding is an action.** An agent that observes degradation it did not cause
  and correctly does nothing has acted correctly, and the loop records it.

---

## 5. Stability controls

Three independent loops on delayed, partial evidence can oscillate: Packet A
lowers its rate, loss falls, Packet A raises it, loss returns.

Declared per domain in `policy.yaml`, versioned, published in the run bundle:

| Control | Purpose |
| --- | --- |
| **Hysteresis** | Separate thresholds for acting and for reverting, so a boundary condition does not flap |
| **Action-rate limit** | Maximum changes per unit time per domain |
| **Hold-down** | Settling window before the same domain acts again |
| **Attribution precondition** | Do not act on degradation attributed to another domain |

The research question these create: **does independent per-domain control remain
stable when the evidence each agent acts on is late and incomplete — and at what
disclosure rate does it settle?**

---

### 5.1 The control law

Deliberately the simplest thing that can work, because the paper is about
*federation enabling the control*, not about control design.

```text
on each tick, if compensation_gate passes and the fault is mine:
    if loss_ratio > act_threshold:        rate <- max(rate * (1 - step), floor)
    elif loss_ratio < revert_threshold:   rate <- min(rate * (1 + step), requested)
    else:                                 hold
```

Multiplicative decrease, multiplicative increase, both bounded. A fixed
`rate_step`, a `rate_floor_mbps` below which the service is declared failed
rather than degraded further, and a ceiling at the originally requested load.

**Why not AIMD or a PID controller.** Either would be defensible, and both are
tunable in ways that would let a reviewer ask whether the result is the
controller or the federation. A fixed multiplicative rule with two declared
thresholds keeps the variable of interest the **evidence**, not the control law.
If the simple law oscillates where a better one would not, that is reported —
and it is itself informative about how much delayed evidence costs.

**Stated limit.** This paper does not claim an optimal controller. It claims
that *any* controller here requires cross-owner evidence, and it measures what
delayed and partial evidence does to a simple one.

---

## 6. The assurance graph

Papers 1 and 3 have two graphs — initiator and participant — both triggered by a
request. Paper 2 adds a **third graph triggered by a timer**, and it is the
main structural addition.

**Seven new nodes** — three reasoning, one gate, three effectors. Two more
(`refresh_observations`, `verify_local`) are reused from Paper 1's library.

| Node | Kind | Does |
| --- | --- | --- |
| `loop_tick` | E | Timer entry. Open a tick record, stamp it, journal |
| `refresh_observations` | E | *reused* — execute the observation plan via MCP |
| `attribute_quality` | R | Current delivered quality → owning segment, by the strongest method available ([Paper 1 §10.2](../paper-1-federated-evidence/design.md#102-three-methods-strongest-first)) |
| `publish_state_summary` | E | Emit this domain's periodic summary; content **and rate** are the disclosure decision |
| `compensation_gate` | **G** | **New gate.** Hysteresis, action-rate limit, hold-down, attribution precondition |
| `select_control` | R | Given attribution and headroom: which control, and how much |
| `apply_control` | E | `set_offered_rate` or `path_set` through the MCP server |
| `verify_local` | R | *reused* — did the control take effect |
| `close_tick` | R | Journal the tick: observed, attributed, decided — **including a hold** |

**Totals with Paper 2 built:** **32 nodes across three graphs** — 17 reasoning,
7 gates, 8 effectors. Paper 1 contributes 25; this paper adds 7.

```text
loop_tick → refresh_observations → attribute_quality → publish_state_summary
                                          │
                                          ▼
                                  compensation_gate
                    ┌─────────────┬───────┴───────┬─────────────┐
                 act │         inform │      escalate │       hold │
                    ▼             ▼               ▼             ▼
            select_control    (a2a_dialogue)  (a2a_dialogue)  close_tick
                    ▼
             apply_control → verify_local → close_tick
```

### 6.1 `compensation_gate` — the new gate

It is a **gate**, never a model call, and it is what keeps three independent
loops from fighting. It refuses to act unless **all four** hold:

| Check | Refuses when |
| --- | --- |
| **Attribution precondition** | The degradation is attributed to another domain |
| **Hysteresis** | The measurement is between the act and revert thresholds |
| **Action-rate limit** | This domain has already made its allowed changes this window |
| **Hold-down** | The settling window since this domain's last change has not elapsed |

A refusal here routes to `hold`, which is journalled as a decision — **not as an
absence of one**. Correct non-action is measured.

### 6.2 The four gates in Paper 2

Paper 1's three gates still apply to any control that changes device state.
`compensation_gate` sits in front of them, so a control passes **four** gates:

```text
compensation_gate → feasibility_gate → policy_gate → apply_control
```

`agreement_gate` does **not** apply: a local rate change inside an agreed
configuration is not a renegotiation. If a control would change the joint
configuration, the agent opens an episode and the Paper 1 path runs instead.
That boundary is worth testing explicitly.

### 6.3 How often the loop thinks — and why it must not always

Four of the assurance graph's nodes are LLM-capable: `attribute_quality`,
`select_control`, `verify_local`, `close_tick`. A **hold** tick fires two
(`attribute_quality`, `close_tick`); an **acting** tick fires four.

Run naively that is a problem, and it is worth stating before building:

| At a 10 s loop period | Per hour |
| --- | --- |
| 3 agents × 360 ticks × 2 calls (hold) | **≈2,160 calls** |
| 3 agents × 360 ticks × 4 calls (acting) | **≈4,320 calls** |

Two consequences. **Cost** — a multi-hour stability sweep at thousands of calls
per hour is expensive enough to constrain the experiment grid. **Latency** —
four sequential model calls at one to three seconds each is four to twelve
seconds, which can exceed the loop period itself and make the loop lag the
network it is regulating.

**Design rule: the assurance loop runs its deterministic rules by default.** The
engine is invoked only on escalation:

| Escalate to the engine when | Otherwise use |
| --- | --- |
| Attribution is `unattributable`, or two methods disagree | Segment decomposition, taken as given |
| The control decision is non-obvious — near a threshold, or a previous correction failed | Fixed step toward the objective |
| `verify_local` finds a partial or contradictory result | Exact comparison |
| A peer's summary is stale, partial, or inconsistent with the SIMAP | Structured fields only |

This keeps the steady-state loop cheap and deterministic — which is also what a
stability study needs, since a fluctuating model latency inside the control path
would confound C10. Under this rule a typical hour is dominated by rule-only
ticks with a small number of escalations.

**And "how often does the loop need to think?" becomes a reported result** —
escalation rate per hour, and whether ticks that escalated produced better
control than ticks that did not. That is a more interesting number than the
LLM-capable node count.

---

## 7. Storage additions

Paper 1's `context.db` schema is reused unchanged. Paper 2 adds two tables and
extends `policy.yaml`.

```sql
-- one row per loop tick, per agent
CREATE TABLE tick (
    id TEXT PRIMARY KEY,
    observed_at     INT,
    delivered_ratio REAL,          -- from the latest peer OUTCOME, may be stale
    evidence_age_ms INT,           -- how late the evidence was: the key covariate
    attributed_to   TEXT,          -- segment id, or 'unattributable'
    method          TEXT,          -- exact | conditional | correlational
    decision        TEXT,          -- act | inform | escalate | hold
    reasoned        INTEGER,       -- did this tick escalate to the engine (§6.3)
    gate_refused_by TEXT,          -- which compensation_gate check, if held
    control         TEXT,          -- e.g. 'set_offered_rate:0.7'
    reverted_from   TEXT           -- set when this tick undoes an earlier one
);

-- current control state, for hysteresis and hold-down
CREATE TABLE control_state (
    domain        TEXT PRIMARY KEY,
    current_rate  REAL,
    last_change   INT,
    changes_in_window INT,
    direction     TEXT             -- rising | falling | steady
);
```

`evidence_age_ms` and `reverted_from` exist for C10 specifically: stability is
measured as reverted changes against the age of the evidence each decision was
made on. Without recording both, the stability result cannot be produced.

**`policy.yaml` gains:**

```yaml
assurance:
  loop_period_s: 10
  act_threshold:    {loss_ratio: 0.02}
  revert_threshold: {loss_ratio: 0.005}   # hysteresis band
  hold_down_s: 60
  max_changes_per_hour: 6
  rate_step: 0.1                          # fraction of current offered load
  rate_floor_mbps: 0.2
```

All of it is declared, versioned and published in the run bundle — the stability
sweep varies exactly these fields.

---

## 8. MCP: the `set_offered_rate` tool

Paper 1's three MCP servers and their contract are inherited unchanged. Paper 2
adds **one named action, on one server**.

### 8.1 Why only `packet-a-mcp`

Packet A owns `client-a` and therefore the offered load. Packet B owns the
receiver and cannot change what is sent; the optical domain has no rate control
at all. The tool exists on exactly one endpoint because exactly one owner holds
the capability — the same reason `get_service_evidence` returns delivery data
only from `packet-b-mcp`.

### 8.2 Tool specification

```json
{
  "name": "set_offered_rate",
  "description": "Set the offered load of this domain's service sender.",
  "inputSchema": {
    "type": "object",
    "required": ["service_id", "mbps"],
    "properties": {
      "service_id": {"type": "string"},
      "mbps": {"type": "number", "minimum": 0.2, "maximum": 1.0},
      "reason": {"type": "string"},
      "citations": {"type": "array", "items": {"type": "string"}}
    }
  }
}
```

Returns the applied rate, the previous rate, and a readback taken from the
sender itself — **never an echo of the request**.

| Property | Behaviour |
| --- | --- |
| **Bounds** | `rate_floor_mbps` ≤ mbps ≤ originally requested load. A request below the floor is **refused**, not clamped — the service is declared failed rather than silently degraded further |
| **Idempotency** | Setting the current rate is a no-op returning `changed: false`, and costs no `transactions` |
| **Verification** | Readback from the sender process, plus the next receiver interval. An acknowledgement is not verification (P1 §12.3) |
| **Failure** | If the sender is not running, return `failed` with the observed state. Never start a stopped sender as a side effect |
| **Cost** | One `transaction`; `disruption` measured from the receiver across the change window |
| **Provenance** | `reason` and `citations` are required and journalled, so every rate change is traceable to the peer evidence that triggered it |

### 8.3 The implementation problem, and three options

**`traffic.py` drives iperf3, and iperf3 cannot change `-b` mid-run.** A naive
implementation stops and restarts the sender, which puts a gap in the stream —
roughly 9 datagrams at 1 Mbps with a 1400-byte payload and a ~100 ms restart.
That gap is indistinguishable from network loss at the receiver, which would
**contaminate the very measurement this paper depends on**.

| Option | Cost | Consequence |
| --- | --- | --- |
| **A. Restart and account** | none | The gap is attributed explicitly and excluded from the loss window. Cheapest, but every rate change carries an artefact that must be argued away |
| **B. Shape at the sender's egress** (`tc tbf` on `client-a`) | small | No restart, no gap. But shaped-away packets never enter the network, so "loss" becomes sender-side and the delivered-ratio denominator needs redefining |
| **C. Replace the generator** with a small Python UDP sender reading its rate from a control socket | ~100 lines | Dynamic rate, no restart, no denominator ambiguity. It can also carry **sequence numbers**, making segment attribution exact rather than counter-differenced |

**Recommended: C.** It removes an artefact from the paper's central measurement,
and the sequence numbers are worth having independently — they would let
attribution (P1 §10.1) localise loss without relying on counter differencing at
all. The cost is replacing a working, well-understood generator, so the decision
belongs at the **start** of Phase 4b, not midway through it.

Whichever is chosen, **state it and show the artefact is controlled**: option A
needs the excluded window reported per change; option B needs the denominator
defined in the metrics section.

### 8.4 What does not change

`packet-b-mcp` and `optical-mcp` gain nothing. The read-only tool set is
unchanged on all three. No new gate tool: `compensation_gate` runs inside the
agent, not in the MCP server, because it reads the agent's own hysteresis and
attribution state.

---

## 9. Components to build

| Component | Where | Detail |
| --- | --- | --- |
| Assurance graph | `agent/graphs/assurance.py` | Seven new nodes (§6); per-domain period, no global tick |
| `set_offered_rate(mbps)` | `mcp/packet_server.py` | New named action, `packet-a-mcp` only (§8) |
| Congestion netem profiles | condition harness | Rate-limited bottleneck **with a queue** |
| `compensation_gate` | `agent/gates.py` | Four checks (§6.1); refusal routes to `hold` |
| `tick`, `control_state` tables | `agent/context/store.py` | §7; `evidence_age_ms` and `reverted_from` are required for C10 |
| Periodic state summaries | `agent/peers.py` | Disclosure **rate** as a run parameter |

### 9.1 Changes to inherited components

| Component | Change |
| --- | --- |
| `packet-a-mcp` tool list | Gains `set_offered_rate`; `packet-b-mcp` and `optical-mcp` unchanged |
| `policy.yaml` schema | Gains hysteresis thresholds, action-rate limit, hold-down window |
| Episode manager | Gains the timer-triggered assurance graph, running between episodes |
| Journal | Gains loop-tick records: what was observed, attributed, and decided including holds |

Everything else — gates, SIMAP, predictors, A2A, security — is used as inherited.

---

## 10. The premise that gates this paper

**Reducing offered load must actually reduce loss under the netem profile.**

With random-drop netem it will not: loss ratio stays flat and the sender simply
delivers less for nothing. The profile must be a rate-limited bottleneck with a
queue, so that the loss is congestion and responds to offered load.

Run this additional check during [Paper 1's Phase 1](../paper-1-federated-evidence/plan.md#8-build-phases),
alongside its three base-system premise checks and long before anything here is
built. **If it fails, the coupling mechanism does not exist and
this paper does not exist in its current form.**

---

### 10.1 Interaction with Paper 1's episode path

Three rules keep the continuous loop and the episodic negotiation from
interfering:

| Situation | Path taken |
| --- | --- |
| Rate change inside the agreed configuration | Assurance graph only. Not a renegotiation, no `agreement_gate` |
| A control that would change the joint configuration | Open an episode; Paper 1's initiator path runs |
| An episode is already open | The assurance loop **holds** — one active episode per agent (P1 §7.5) |

The second row matters: a domain that exhausts its rate headroom and still
cannot meet the objective must escalate to renegotiation rather than silently
doing nothing. That transition is a tested behaviour.

---

## 11. Build status

| Component | Status |
| --- | --- |
| Everything in Paper 1's Phases 0–4 | prerequisite, not started |
| Assurance graph: 6 new nodes and `compensation_gate` | to build |
| `tick` and `control_state` tables | to build |
| `set_offered_rate` tool and its generator decision (§8.3) | to build |
| Congestion netem profiles | to build |
| Periodic state summaries with rate as a parameter | to build |
