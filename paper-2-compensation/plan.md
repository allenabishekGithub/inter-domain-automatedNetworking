# Paper 2 — Research and validation plan

**Companion to** [`design.md`](design.md).
**Prerequisite:** [Paper 1](../paper-1-federated-evidence) Phases 0–4 complete.
Nothing here is a measured result.

---

## 1. The question

> When one domain's infrastructure degrades and it cannot repair itself, can
> another domain act to hold the end-to-end objective — and do independent
> assurance loops stay stable when the evidence they act on is late and partial?

## 2. What is new

**1. A proof that cooperative assurance needs a coupling mechanism.** Under the
provisioning action space the loss terms are separable, so no domain can help
another and greedy local behaviour is already optimal. Most multi-domain
assurance work assumes coupling exists; here it is shown not to, and then
constructed deliberately.

**2. A control action that does not exist without federation.** The sender is
owned by Packet A; the evidence it should slow down is owned by Packet B.
Stronger than "sharing improves things" — sharing is the precondition for the
action being possible at all.

**3. Stability of independent control under ownership.** Three loops, no global
tick, each acting on late and partial peer evidence. The question of whether
disclosure rate buys stability has a measurable answer here.

---

## 3. Claims

| # | Claim | Evidence |
| --- | --- | --- |
| **C9** | A domain can compensate for a peer's degradation, but only using evidence that peer holds | Rate adaptation restores the loss objective under downstream congestion; under S0 the control never fires |
| **C10** | Independent per-domain control loops remain stable on late, partial evidence | Changes per hour, reverted changes, time outside objective, across disclosure rates and hysteresis settings |

C9 is a clean binary demonstration. C10 is a parameter study and carries the
journal weight.

---

## 4. Experiments

**E3d — Compensation.** Inject downstream congestion that Packet A cannot repair
by switching its own path, and that neither Optical nor Packet B can repair at
all. The only remedy is Packet A reducing offered load, using evidence only
Packet B holds.

Report: the objective restored, **the throughput given up**, the disclosure
required to trigger it, and the latency from degradation to correction. Under S0
the control never fires because the signal never arrives — **that contrast is
the result.** *C9.*

**E3e — Loop stability.** Run the continuous loops across a grid of disclosure
rates × hysteresis settings × action-rate limits. Measure changes per hour per
domain, reverted changes, oscillation amplitude, and time outside the objective.

The question is whether independent control on late, partial evidence
oscillates, **and at what disclosure rate it stops**. A disclosure rate below
which the system is unstable is a concrete, useful finding. *C10.*

---

## 5. Baselines

| Condition | What changes |
| --- | --- |
| **B0** — no compensation | Rate fixed; the inherited Paper 1 behaviour. Floor |
| **B1** — compensation, no hysteresis | Isolates what the stability controls contribute |
| **B2** — centralised reference | One controller with all three domains' evidence and no disclosure delay. Upper bound, not achievable under independent ownership |
| **B3** — full system | Compensation with declared hysteresis and limits |

B0 vs B3 is the headline for C9. B1 vs B3 is the headline for C10. B2 bounds
both and quantifies **the price of ownership** — how much worse independent
control is than an omniscient central one.

---

## 6. Metrics

| Group | Measures |
| --- | --- |
| Objective | Time inside `min_delivered_ratio` and `max_loss_ratio`; time outside either |
| Compensation | Correction latency; throughput conceded; objective restored (y/n); disclosure required to trigger |
| Stability | Changes per hour per domain; reverted changes; oscillation amplitude and period |
| Attribution | Correct-action and correct-non-action rate under continuous operation |
| Disclosure | Records, fields, bytes **per unit time** — a rate, not a per-episode count |
| Cost | Transactions, disruption datagrams, A2A messages per hour |
| Reasoning | Escalation rate per hour (ticks that invoked the engine); whether escalated ticks produced better control than rule-only ticks; tokens and latency per escalation |

Per agent, always.

---

## 7. Build phase

**Phase 4b**, on top of Paper 1's Phases 0–4: loop scheduler, per-domain
hysteresis and action-rate limits, `set_offered_rate` in `packet-a-mcp`, and
periodic state summaries with disclosure rate as a run parameter.

Indicative effort: **four to six months** after Paper 1's system is running.

---

## 8. Threats to validity

| Threat | Mitigation |
| --- | --- |
| **Compensation is an artefact of the netem profile** | Report the profile in full; show the same control does nothing under random-drop loss |
| **Rate changes create a stream gap read as loss** | Resolve the generator decision (design §8.3) before Phase 4b; whichever option is chosen, report the artefact and how it is excluded |
| **Instability is a tuning artefact** | Sweep hysteresis and rate limits rather than reporting one chosen setting |
| **Host limits mistaken for congestion** | Calibrate the bottleneck; confirm the host is not the limiting element |
| **Correlated loop ticks** | The independent unit is a complete run, not a tick |
| **Model latency inside the control path confounds stability** | The loop runs deterministic rules by default and escalates only on the conditions in design §6.3; escalation is recorded per tick |
| **Three loops do not establish general stability** | Scope the claim to three owners and this topology, explicitly |
| **Throughput concession framed as success** | Always report what was given up alongside what was restored |

---

## 9. Not tested in this paper

- **Whether sharing helps learning.** Paper 1.
- **Whether the reasoning layer helps.** Paper 3.
- **Bandwidth allocation or reservation.** Rate is offered load under closed-loop
  control, never a reserved allocation.
- **Optical compensation.** The optical domain has no coupling action; that is a
  finding, not a gap to fill.
- **Scale.** Three loops. No claim about many-domain stability.
- **Adversarial peers.** A peer that misreports to induce another's rate change
  is out of scope, and is the obvious follow-on.

---

## 10. Statistical design

**The independent unit is a complete run** — a continuous loop sequence over a
condition schedule — never a tick. Ticks are strongly autocorrelated: control
state, hold-down windows and evidence age all carry across them.

- Matched schedules and seeds across conditions; paired estimates.
- For C10, the covariate of interest is **`evidence_age_ms`**, recorded per tick.
  Stability is reverted-change rate as a function of evidence age, not a single
  summary number.
- Sweep hysteresis band, hold-down and disclosure rate on a declared grid rather
  than reporting one tuned setting — **an instability that disappears under
  tuning is a tuning result, not a stability result.**
- Report oscillation as amplitude **and** period, since a slow large swing and a
  fast small one are different failures.

---

## 11. Run bundle

Paper 1's bundle structure, plus:

```text
run-<id>/
  conditions/congestion.yaml   rate-limited bottleneck profiles, queue depths
  agents/agent-*/control.jsonl tick records: evidence age, attribution, decision, hold reason
  analysis/stability.parquet   one row per tick per agent
```

**Pinned per run:** loop period, act and revert thresholds, hold-down,
`max_changes_per_hour`, `rate_step`, `rate_floor_mbps`, disclosure rate, and
everything Paper 1 pins.

---

## 12. Figures and tables

| # | Figure | Shows |
| --- | --- | --- |
| **F1** | Delivered ratio and offered rate over time, S0 vs S1, through a congestion event | **The headline.** Under S0 the control never fires |
| F2 | Correction latency against disclosure rate | What timeliness of evidence buys |
| F3 | Reverted changes against `evidence_age_ms` | C10 — the stability boundary |
| F4 | Oscillation amplitude across the hysteresis × disclosure-rate grid | Where the system is stable |
| F5 | Throughput conceded against objective time restored | The trade being made |
| F6 | Escalation rate per hour and control quality, reasoned vs rule-only ticks | Whether the loop needs to think (design §6.3) |

| # | Table | Shows |
| --- | --- | --- |
| T1 | Objective time, per condition, per agent | C9 |
| T2 | Hold decisions by refusing gate check | Correct non-action, decomposed |
| T3 | Distance from the B2 centralised reference | **The price of ownership** |

---

## 13. Claim-to-evidence release criteria

| Claim | Release criterion |
| --- | --- |
| **C9** | Under S1 the loss objective is restored within a declared latency in the majority of congestion events, and under S0 the control fires zero times across all matched runs |
| **C10** | A disclosure rate exists above which reverted changes fall below a predeclared threshold, and it is reported with the hysteresis setting it assumes |

If C10's threshold does not exist within the swept grid, report that the system
did not stabilise under the conditions tested — **a negative stability result is
publishable and more useful than a tuned positive one.**

---

## 14. Open decisions

| Decision | Deadline | Default if unmade |
| --- | --- | --- |
| Loop period | Phase 4b start | 10 s |
| Control law: fixed multiplicative vs AIMD | Phase 4b start | Fixed multiplicative (design §5.1) |
| Does the loop escalate to the engine at all? | Phase 4b start | Rules only; escalation conditions per design §6.3 |
| **Traffic generator**: keep iperf3, shape at egress, or replace it | **Phase 4b start** | Replace it (design §8.3) — removes a measurement artefact and enables sequence-numbered attribution |
| Is B2 (centralised reference) built? | before evaluation | Yes — it is what quantifies the price of ownership |
