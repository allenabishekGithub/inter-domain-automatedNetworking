# Paper 2 — Cross-domain compensation and assurance-loop stability

**Status:** not started. Blocked on Paper 1's system.
**Target:** IEEE TNSM or JSAC.
**Depends on:** [Paper 1](../paper-1-federated-evidence) — Phases 0–4 complete.

---

## The problem

When one domain's infrastructure degrades and it cannot repair itself, can the
others adapt to hold the end-to-end objective?

**Under the provisioning action space alone, no — and that is provable rather
than observed.** End-to-end loss decomposes as
`1 − (1 − l_A)(1 − l_attach)(1 − l_B)`, and the terms are separable:

| Agent | Action | Affects |
| --- | --- | --- |
| Packet A | primary ↔ backup core | `l_A` only |
| Optical | channel 1 ↔ 2 | **nothing measurable** — gOSNR is decoupled from packet loss |
| Packet B | primary ↔ backup core | `l_B` only |

No domain's action reduces another's term. Each minimising its own is already
globally optimal, so there is nothing to coordinate about.

**Exactly one capability breaks the separability: sender rate adaptation.**
Where the impairment is congestion — a rate-limited link with a queue, not
random drop — reducing offered load reduces loss downstream as well as locally.
Packet A's action now moves `l_attach` and `l_B`.

And the structural point that makes this a paper rather than an engineering
note:

> **The sender is owned by Packet A. The evidence that the rate should change is
> owned by Packet B.** The control action does not merely benefit from
> federation — it does not exist without it.

The second half asks what happens when three such loops run continuously on
evidence that always arrives late and partial.

## Claims

| # | Claim | Evidence |
| --- | --- | --- |
| **C9** | A domain can compensate for a peer's degradation, but only using evidence that peer holds | Rate adaptation restoring the loss objective under downstream congestion; under S0 the control cannot fire at all |
| **C10** | Independent per-domain control loops remain stable on late, partial evidence | Changes per hour, reverted changes, time outside objective, across disclosure rates and hysteresis settings |

C9 is a clean binary demonstration. C10 is a parameter study and carries the
paper's weight for a journal.

## What it needs built

Everything Paper 1 builds, plus **Phase 4b**:

| Component | Detail |
| --- | --- |
| Loop scheduler | Per-domain period, independent — there is no global tick |
| `set_offered_rate(mbps)` | New named action on `packet-a-mcp` only, fully specified in [design §8](design.md#8-mcp-the-set_offered_rate-tool) — including the **generator decision**: iperf3 cannot change rate mid-run, and a naive restart puts a gap in the stream that is indistinguishable from loss |
| Congestion netem profiles | Rate-limited bottleneck **with a queue**. Random drop will not work |
| Hysteresis | Separate act and revert thresholds, declared in `policy.yaml` |
| Action-rate limit, hold-down | Per domain, published in the run bundle |
| Periodic state summaries | Disclosure **rate** becomes a run parameter, not just content |

## Architecture

| Section | Why it matters here |
| --- | --- |
| [§4](design.md#4-continuous-operation) | Continuous operation: no global tick, disclosure as a rate, holding as an action |
| [§2–§3](design.md#2-the-problem-the-action-space-is-separable) | The separability argument and why rate adaptation is the right capability |
| [§5](design.md#5-stability-controls) | Stability: hysteresis, action-rate limits, hold-down, attribution precondition |
| [§3.1](design.md#31-what-it-is-not) | Rate is **not** in the candidate space — it is a scalar control inside whichever of the eight configurations is in force |

This paper's [`design.md`](design.md) specifies the **assurance graph** — a
third, timer-triggered graph of **seven new nodes** including the new
`compensation_gate` (§6) — and the **`tick` / `control_state` tables** (§7).

**This is the only paper that changes the graph's shape:** 32 nodes across three
graphs, against Paper 1's 25 across two. The assurance graph is entered by a
**timer** rather than a request, which is what makes continuous operation
possible.

**Guard against scope creep.** `set_offered_rate` is closed-loop control: one
variable, one feedback signal, no optimiser. It is not a search dimension and
does not reintroduce a need for population-based optimisation.

## Experiments

| | Experiment | Establishes |
| --- | --- | --- |
| **E3d** | Compensation: inject downstream congestion that Packet A cannot fix by switching path and neither peer can fix at all. The only remedy is rate reduction, using evidence only Packet B holds | C9 |
| **E3e** | Loop stability: run continuous loops across several disclosure rates and hysteresis settings | C10 |

For E3d report the objective restored, the **throughput given up**, and the
disclosure required to trigger it. Under S0 the control never fires because the
signal never arrives — that contrast is the result.

For E3e the question is whether independent control on late, partial evidence
oscillates, **and at what disclosure rate it stops**.

## The premise that gates this paper

**Additional premise check during Paper 1's Phase 1: reducing offered load must
actually reduce loss under the netem profile.** With random-drop netem it will not — loss ratio stays flat and
the sender simply delivers less for nothing. The profile must be a rate-limited
bottleneck with a queue so the loss is congestion.

Ten minutes to test. **If it fails, C9 is impossible and this paper does not
exist in its current form.** Run it during Paper 1's Phase 1, long before
anything here is built.

## Documents in this folder

| File | Contents |
| --- | --- |
| [`design.md`](design.md) | System architecture as this paper builds and uses it |
| [`plan.md`](plan.md) | Claims, experiments, baselines, metrics, build phases, threats |

The [Paper 1 design](../paper-1-federated-evidence/design.md) is **canonical for
the shared system**. This folder's [`design.md`](design.md) is authoritative for
Paper 2's additions; inherited behavior follows Paper 1. This folder's
[`plan.md`](plan.md) defines the compensation and stability experiments.

## Working here

- **Code is shared**, at the repository root. Phase 4b components go into the
  shared `agent/` and `mcp/` trees, not into this folder.
- `experiments/` — condition schedules, disclosure rates, hysteresis grids.
- `results/` — run bundles and analysis.
