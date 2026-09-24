# Paper 1 — Research and validation plan

**Companion to** [`design.md`](design.md).
**Programme context:** [the root README](../README.md#three-papers--choose-one).
**Target:** IEEE TNSM (Q1). Conference version first at CNSM or NOMS.
Nothing here is a measured result.

---

## 1. The question

> In a service crossing separately owned networks, the party that can measure
> the outcome is not the party that chose the configuration. What does sharing
> that outcome across an ownership boundary buy each owner, what does it cost in
> disclosure, and can agents attribute degradation to the owner who caused it?

## 2. What is new

**1. Ownership separates features from labels.** Standard federated learning
partitions a dataset — every party holds features *and* labels. Here one party
holds every label and only some features, the others hold features and no label.
The split follows from who owns the receiver.

**2. Full state flooding would not dissolve it.** Delivered ratio is an endpoint
application measurement, in no routing protocol and no LSDB. The asymmetry is
about *service outcome evidence*, not topology or network state.

**3. Some evidence exists only across the boundary.** Attachment-segment loss is
`gw-a` out-packets minus `gw-b` in-packets — a subtraction neither owner can
perform alone.

**4. A fixture where local telemetry is structurally misleading.** The optical
agent is data-richest and its strongest local feature does not predict the
outcome.

**5. A shared service–infrastructure map as the precondition for federation.**
A peer's outcome is uninterpretable until the map says which segments it
crossed and who owned each.

**6. Ground truth.** The receiver either got the packets or it did not.

**Not claimed as novel:** ridge regression, EWMA, LangGraph, A2A, MCP, the
emulation stack, or multi-domain orchestration as a topic.

---

## 3. Claims

| # | Claim | Evidence |
| --- | --- | --- |
| **C1** | Without sharing, two of three owners cannot learn the outcome at all | S0: flat predictor error for Packet A and Optical across the whole sequence |
| **C2** | Sharing improves each owner's predictions and decisions | S0 vs S1: per-agent prediction error, decision regret, episodes to stable choice |
| **C4** | The benefit is largest where local telemetry is blind | Locally-invisible vs locally-visible: the S0→S1 gap widens |
| **C6** | Some faults are detectable only across the boundary | Attachment loss localised by counter differencing, by no owner alone |
| **C7** | Attribution works, and the method available depends on disclosure | Accuracy per method against the injected ground-truth segment |
| **C8** | Attribution produces correct action **and correct non-action** | Owning domain acts, others refrain, disruption avoided |

C2 and C4 are the contribution. C1 establishes the floor is structural. C7–C8
are what the shared evidence is *for*. C6 is the cheapest striking result.

---

## 4. The core experiment

Four sharing conditions, identical fixtures, seeds and schedules
([design §11.3](design.md#113-sharing-conditions)),
each run across stationary → drift → abrupt shift → recurrence.

**Headline figure:** per-agent prediction error over episodes, four conditions,
Packet A and Optical plotted separately from Packet B. **S0 should be a flat
line for two of three agents.** If it is not, the premise is wrong and that is
worth knowing immediately.

---

## 5. Experiments

Each produces a run bundle: all three journals and `context.db`, policies,
predictor snapshots, the schedule actually applied, and raw receiver logs.

**E1 — Platform.** Healthy provisioning and correct refusal. Confirms episodes
complete with unanimous acceptance, per-domain execution and receiver-verified
delivery; confirms an unresolvable request terminates `no_agreement`.
*Precondition, not a result.*

**E2 — Sharing conditions.** S0/S1/S2/S3 over the full schedule. Per-agent
prediction error, decision regret against the retrospectively best
configuration, episodes to stable choice, disclosure volume. *C1, C2.*

**E3 — Visibility classes.** S0 vs S1 separately under locally-visible and
locally-invisible impairment. The gap should be small in the first and large in
the second. *C4 — the sharpest result available.*

**E3b — Joint detection.** Inject attachment-segment loss and ask each agent to
localise it. No owner can alone. Compare S0, counter sharing, and outcome
sharing alone: outcome sharing says *that* service degraded, counter sharing
says *where*. *C6.*

**E3c — Attribution and action.** Inject into a known segment — Packet A's core,
the attachment, or Packet B's core. Score: did each agent correctly determine
whether the fault was its own; did the owning domain act; did the others
correctly refrain; how much disruption did refraining avoid. Run under S0,
counter sharing and full disclosure so all three attribution methods are
exercised. *C7, C8.*

**E4 — Drift and recurrence.** Abrupt shift inverting the best configuration,
then recurrence of the earlier regime. Adaptation latency, forgetting, and
whether the forgetting factor trades one against the other. Under S0 and S1.
*C2.*

---

## 6. Baselines and ablations

| Condition | What changes |
| --- | --- |
| **P0** — EWMA predictor | Per-configuration average instead of the feature model |
| **P1** — no learning | Predictors frozen; isolates learning from negotiation |
| **P2** — rule-based sharing decision | S3's reasoning replaced by its deterministic fallback |
| **P3** — oracle | Retrospectively best configuration per episode; upper bound, not achievable online |

S0 vs S1 is the headline. P3 bounds it. P0 shows what the trivial predictor
already achieves — report it even when it is close.

---

## 7. Metrics

| Group | Measures |
| --- | --- |
| Learning | Prediction MAE per agent over episodes; adaptation latency; error on a recurring regime |
| Decision | Regret vs P3; episodes to stable choice; refusal correctness |
| Attribution | Segment-localisation accuracy by method; correct-action and correct-non-action rate; disruption avoided |
| Disclosure | Records, fields and bytes per episode and cumulatively; split by knowledge kind |
| Negotiation | Rounds, refusals by reason, agreement rate, `no_agreement` rate |
| Cost | Transactions, disruption datagrams, occupancy; A2A messages and bytes |

**Per agent, always.** The three are differently positioned and an aggregate
hides the result. Service delivery and correct refusal are reported
**separately** — a refusal is not a failure.

---

## 8. Build phases

**Phase 0 — unblock measurement.** Close **F4** so a receiver sample can be
proven to postdate a change. Run `sudo scripts/service-up.sh` end to end and
capture the first run bundle. **Never yet done.**

**Phase 1 — condition harness and segment attribution.** `tc netem` profiles,
the three visibility classes, the schedule driver; segment counter collection at
the four bracketing interfaces.

**Then verify the premise, before building any agent.** Three checks, each able
to kill a claim cheaply:

1. **Delivered ratio varies by configuration** under the schedule. If not, there
   is nothing to learn.
2. **A locally-invisible impairment is absent from every domain's counters** and
   present at the receiver. If a domain sees it locally, C4 evaporates.
3. **Segment losses sum to end-to-end loss** within tolerance. If not, exact
   attribution is unavailable and C7 falls back to statistical methods.

Fix **F3** here if check 3 fails for parsing rather than physical reasons — the
telemetry extractor has never run against the pinned SR Linux image.

**Phase 2 — MCP server and one agent.** `packet-a-mcp` first, with device
credentials held there rather than in the agent. Then `agent-packet-a` as its
only client: gates, journal, context store, SIMAP projection.

**Phase 3 — three agents over A2A.** Agent Cards, task lifecycle, six exchanges,
round cap, unanimous commit. Deterministic decisions. Delivers E1.

**Phase 4 — predictors and sharing.** RLS with forgetting, EWMA baseline,
`OUTCOME` publication, S0–S3 switches. Delivers E2, E3, E3b, E3c, E4.

Close **F2** before Phase 4: a repair requiring the failed router to answer gNMI
cannot support the assurance episodes.

**Open decision — settle before Phase 4 ends.** Whether this paper runs the
reasoning engine. Deterministic agents drop Phase 5 entirely, are three to four
months cheaper and far more reproducible, but invite *"why is this agentic?"*.

**Reproducibility.** Pin netem profiles, forgetting factor, seeds, A2A spec
version and — if the engine runs — model id, version and temperature. A result
that cannot be replayed from the journal is not a result.

---

## 9. Threats to validity

| Threat | Mitigation |
| --- | --- |
| **Trivial decision space** — eight configurations | State it. The claim is about evidence availability, not search difficulty |
| **Host limits mistaken for network effects** | Calibrate reference traffic; confirm the host is not the bottleneck before attributing loss |
| **Predictor circularity** | The label comes from the receiver, never from a model |
| **Correlated episodes** | The independent unit is a complete chronological stream, not an episode |
| **Future-data leakage** | Chronological evaluation only; no best-checkpoint selection on the test stream |
| **Per-interface ≈ per-flow** | Holds only because there is one service. Stated, not assumed away |
| **Full topology replication** | An assumption, declared. Whether operators would agree is a policy question |

---

## 10. Not tested in this paper

- **Bandwidth allocation.** One flow, no policing. Offered load is never
  reported as a reservation.
- **Compensation and loop stability.** Paper 2.
- **Evaluation of the reasoning layer.** Paper 3.
- **Optical restoration.** One fibre chain; a cut is unrecoverable by design.
- **Scale.** Three owners, eight configurations. No scalability claim.
- **Adversarial peers.** Honest but self-interested; a lying peer is out of
  scope.
- **Privacy guarantees.** Disclosure volume is measured, not defended.

---

## 11. Statistical design

**The independent unit is a complete chronological stream**, not an episode, not
a packet, not a predictor update. Episodes within a stream are correlated by
construction: the predictor carries state across them and the condition schedule
is ordered.

- Use **matched exogenous streams and seeds** across conditions, and paired
  effect estimates. S0 and S1 must see the identical condition sequence.
- Preserve within-stream dependence when bootstrapping; do not resample episodes
  independently.
- **Predeclare** the primary endpoint (per-agent prediction MAE for Packet A and
  Optical), the meaningful effect size, and the number of streams, from a pilot.
- Report uncertainty, distributions and stream counts — not point estimates
  alone. Adjust for multiple confirmatory contrasts or label the rest
  exploratory.
- **Do not stop when significance appears.** Stopping rules are fixed before the
  grid runs.

**Learning curves** are plotted with regime boundaries marked, showing both the
predictive metric (MAE) and the service metric (delivered ratio), because a
better predictor that does not change decisions is not a result.

**No finite error-free run proves a guarantee.** Every claim is scoped to the
tested owners, objectives, workload and emulator fidelity.

---

## 12. Run bundle and reproducibility

Every experiment emits one bundle. A result that cannot be replayed from it is
not a result.

```text
run-<id>/
  manifest.json        seeds, versions, git SHA, condition schedule id, sharing condition
  conditions/
    schedule.yaml      the chronological sequence actually applied
    netem.yaml         per-link profiles, per visibility class
  agents/
    agent-packet-a/    policy.yaml, predictor.json snapshots, journal.jsonl, context.db
    agent-optical/     ...
    agent-packet-b/    ...
  raw/
    receiver.log       iperf3 interval output, unmodified
    segment-counters/  four bracketing interfaces, timestamped
  analysis/
    metrics.parquet    one row per episode per agent
    figures/
```

**Pinned per run:** netem profiles, forgetting factor `lambda`, RLS
regularisation, seeds, A2A specification version, SR Linux and Mininet-Optical
image digests, and — if the reasoning engine is enabled — model id, version and
temperature.

**`context.db` is archived whole.** It is one SQLite file, which is why the
embedded store was chosen over separate database servers.

---

## 13. Figures and tables

Planned up front so the experiments produce what the paper needs:

| # | Figure | Shows |
| --- | --- | --- |
| **F1** | Per-agent prediction MAE over episodes, four sharing conditions | **The headline.** S0 flat for Packet A and Optical |
| F2 | The same, split by visibility class | C4 — the gap widens where telemetry is blind |
| F3 | Decision regret vs the P3 oracle, by condition | C2 |
| F4 | Attribution accuracy by method and by disclosure level | C7 |
| F5 | Correct-action / correct-non-action rates, and disruption avoided | C8 |
| F6 | Disclosure volume against decision quality | The cost axis |
| F7 | Learning curves across the regime shift and recurrence | C2, adaptation vs forgetting |

| # | Table | Shows |
| --- | --- | --- |
| T1 | Segment-localisation accuracy, per owner, per method | C6, C7 |
| T2 | Refusals by reason, per agent | Correct refusal as correct behaviour |
| T3 | Cost vector per episode: transactions, disruption, occupancy | §9 of the design |

---

## 14. Claim-to-evidence release criteria

A claim is reportable only when its criterion is met. Otherwise it is reported
as unresolved — **not quietly dropped**.

| Claim | Release criterion |
| --- | --- |
| **C1** | Packet A and Optical prediction MAE shows no significant improvement over the full stream under S0, across all matched streams |
| **C2** | S1 beats S0 on per-agent MAE **and** on decision regret, with the effect exceeding the predeclared size |
| **C4** | The S0→S1 gap under locally-invisible impairment significantly exceeds the gap under locally-visible impairment |
| **C6** | Attachment-segment loss is localised under counter sharing and not localised by any agent under S0 |
| **C7** | Attribution accuracy is ordered exact > conditional > correlational, with the exact method unavailable under S0 |
| **C8** | Non-owning domains refrain in the large majority of injected faults, and the disruption avoided is quantified |

---

## 15. Open decisions

| Decision | Deadline | Default if unmade |
| --- | --- | --- |
| Agentic or deterministic P1 (design §1) | end of Phase 4 | Deterministic — cheaper and more reproducible |
| Sharing conditions: is S3 in P1 or deferred to P3? | end of Phase 4 | Run S3, report it, do not claim it |
| Number of matched streams per condition | after the Phase 1 pilot | Set by the predeclared effect size |
| Loop period for observation refresh | Phase 2 | 10 s tick, 15 s freshness bound |
