# Research and build plan

**Status:** plan, 23 September 2026. Companion to the [design](design.md).
Nothing here is a measured result.

**Target venue:** IEEE TNSM, or CNSM/NOMS for a conference version first.
This is a network *management* contribution, not a protocol or algorithm paper.

---

## 1. The question

> In a service crossing separately owned networks, the party that can measure
> the outcome is not the party that chose the configuration. What does sharing
> that outcome across an ownership boundary buy each owner, what does it cost in
> disclosure, and can agents decide what to share better than a fixed rule?

**One question. One paper.** Everything below serves it; anything that does not
has been cut.

### Why it is not the usual federated-learning setup

Standard federated learning partitions a dataset: every party holds features and
labels, and federating buys more data. Here **ownership separates features from
labels**:

| | Features | Labels |
| --- | --- | --- |
| `agent-packet-a` | Its action, discards, utilisation | none |
| `agent-optical` | Its channel, gOSNR, margins | none |
| `agent-packet-b` | Its action, discards | **all of them** |

Packet B holds every label and only some features. Packet A and Optical hold
features and no label at all. Neither side can build a good predictor alone, and
the split is structural — it follows from who owns the receiver.

The fixture sharpens this deliberately (design §4.1): some impairments are
**locally invisible**, degrading service in a way no owner's own telemetry
reveals; and the optical agent's gOSNR is **modelled-only**, a feature that
looks informative and is not.

### What is new here

Six things, in descending order of how hard they are to argue with.

**1. Ownership separates features from labels.** Standard federated learning
partitions a dataset — every party holds features *and* labels, and federating
buys more data. Here one party holds every label and only some features, and the
others hold features and no label at all. The split follows from who owns the
receiver, not from how a dataset was divided. This regime is not well studied.

**2. Full state flooding would not dissolve it.** A link-state database carries
adjacency, metrics and up/down. Delivered ratio is an endpoint application
measurement on a host one owner operates: it appears in no routing protocol, no
LSDB and no standard telemetry export. The asymmetry is not topological and not
even about network state — it is specifically about *service outcome evidence*.

**3. Some evidence exists only across the boundary.** Loss on the optical
attachment shows as `gw-a` out-packets exceeding `gw-b` in-packets — a
subtraction neither owner can perform alone. A fault invisible to every party
individually and visible to two jointly, demonstrable with one `netem` rule and
a subtraction.

**4. A fixture where local telemetry is structurally misleading.** The optical
agent is the data-richest of the three and its strongest local feature, gOSNR,
does not predict the outcome — because a changed optical margin does not change
packet loss in this emulator (design §4.1). An agent that learns to distrust its
own richest signal in favour of a peer's evidence is demonstrating precisely the
behaviour under study.

**5. Disclosure treated as an agent decision, and measured.** The claim is not
"sharing helps". It is that agents reasoning about *what* to share approach
full-disclosure quality at materially lower disclosure (C3), with P2 ablating
the reasoning out so a negative result is available and reportable.

**6. Ground truth.** Most agentic-AI evaluation is LLM-judged or human-rated.
Here the receiver either got the packets or it did not, and a citation either
resolves to a held record or it does not. Decision quality, attribution accuracy
and faithfulness are all measured against something external to the model.

**What is deliberately not claimed as novel:** the algorithms (ridge regression,
EWMA), the frameworks (LangGraph, A2A, RAG/GraphRAG), the emulation stack, or
multi-domain orchestration as a topic. The contribution is the problem
structure, the fixture that isolates it, and the measurements.

---

## 2. Claims and the evidence each needs

| # | Claim | Evidence |
| --- | --- | --- |
| C1 | Without sharing, two of three owners cannot learn the service outcome at all | S0 runs: flat predictor error for Packet A and Optical across the whole episode sequence |
| C2 | Sharing outcomes across the ownership boundary measurably improves each owner's predictions and decisions | S0 vs S1: per-agent prediction error, decision regret, episodes to a stable choice |
| C3 | Agents that reason about what to share and request approach full-disclosure quality at materially lower disclosure | S3 vs S1 and S2: quality within a declared margin at lower disclosed volume |
| C4 | The benefit is largest exactly where local telemetry is blind | Locally-invisible condition class vs locally-visible: the gap between S0 and S1 should widen |
| C5 | Shared evidence is used faithfully | Grounding-gate firing rate; no agent asserts a peer's condition without citing that peer's disclosure |
| C6 | Some faults are detectable only by combining telemetry across an ownership boundary | Attachment-segment loss localised by cross-owner counter differencing, and by no owner alone |
| C7 | Agents can attribute end-to-end degradation to the owning segment, and the method available depends on what peers disclose | Attribution accuracy per method (exact / conditional / correlational) against the injected ground-truth segment |
| C8 | Attribution produces correct action **and correct non-action** | Rate at which the owning domain acts and non-owning domains refrain; disruption avoided by not reconfiguring healthy domains |

C2 and C4 are the contribution. C1 establishes the floor is real rather than
imposed. C3 is what makes it an *agent* paper rather than a telemetry paper. C5
is the discipline that makes the rest believable.

---

## 3. The core experiment

Four sharing conditions, identical fixtures, identical seeds, identical
condition schedules:

| | Condition | What is disclosed |
| --- | --- | --- |
| **S0** | No sharing | Nothing beyond replicated topology. Floor. |
| **S1** | Full disclosure | Every outcome and every telemetry summary, every episode. Ceiling on learning, worst on disclosure. |
| **S2** | Fixed rule | A declared static policy — e.g. publish only on objective violation, or every *n*th episode. |
| **S3** | Agent-decided | Each agent reasons about what to disclose and what to request (design §8.4). |

Disclosure spans two of the three knowledge kinds (design §11.3): **live state**
(counters, oper-states) and **service outcome** (delivered ratio). Structure —
the topology graph — is replicated in every condition including S0, so the
comparison isolates evidence sharing rather than map sharing.

Run each across the full condition schedule: stationary → gradual drift →
abrupt shift → recurrence of an earlier regime.

**The headline figure** is per-agent prediction error over episodes, four
conditions, with Packet A and Optical shown separately from Packet B. S0 should
be a flat line for two of the three agents. If it is not, the premise is wrong
and that is worth knowing early.

---

## 4. Experiments

Five. Each produces a run bundle: all three journals and `context.db`, policies,
predictor snapshots, the condition schedule actually applied, every retrieval
set, every prompt and response, and raw receiver logs.

**E1 — Platform.** Healthy provisioning and correct refusal. Confirms episodes
complete with unanimous acceptance, per-domain execution and receiver-verified
delivery, and that an unresolvable request terminates as `no_agreement`.
*Not a result; the precondition for every result.*

**E2 — Sharing conditions.** S0/S1/S2/S3 over the full condition schedule.
Per-agent prediction error, decision regret against the retrospectively best
configuration, episodes to stable choice, and disclosure volume. *C1, C2, C3.*

**E3 — Visibility classes.** Repeat S0 vs S1 separately under locally-visible
and locally-invisible impairment. The S0→S1 gap should be small in the first
and large in the second. *C4 — and the sharpest result available here.*

**E3b — Joint detection.** Inject loss on the optical attachment segment and ask
each agent to localise it. No owner can, alone: the evidence is the difference
between `gw-a` out-packets and `gw-b` in-packets, and neither holds both
(design §11.4). Measure localisation accuracy under S0, under counter sharing,
and under outcome sharing alone — outcome sharing tells an agent *that* service
degraded, counter sharing tells it *where*. *C6.*

**E3c — Attribution and action.** Inject loss into a known segment — Packet A's
core, the attachment, or Packet B's core — and score each agent on: did it
correctly determine whether the fault was its own; did the owning domain act;
did the non-owning domains correctly refrain; and how much disruption was
avoided by their refraining. Run under S0, counter sharing, and full disclosure,
so the three attribution methods of design §9.2 are exercised in turn. *C7, C8.*

**E4 — Drift and recurrence.** Abrupt shift inverting which configuration is
best, then recurrence of the earlier regime. Report adaptation latency,
forgetting, and whether the forgetting factor trades one against the other.
Run under S0 and S1 to show how sharing changes adaptation speed. *C2.*

**E5 — Faithful use of peer evidence.** Grounding gate on and off. Measure
claims about a peer's condition that cite no disclosure, cite a disclosure the
agent does not hold, or contradict it. Include episodes where a peer's
disclosure is stale or partial. *C5.*

---

## 5. Baselines and ablations

| Condition | What changes |
| --- | --- |
| P0 — EWMA predictor | Per-configuration average instead of the feature model. Shows what the trivial predictor achieves. |
| P1 — no learning | Predictors frozen. Isolates learning from negotiation. |
| P2 — rule-based sharing decision | S3's reasoning replaced by its deterministic fallback. Isolates the agentic contribution to C3. |
| P3 — oracle | Retrospectively best configuration per episode. Upper bound, not achievable online. |

S0 vs S1 is the headline. P3 bounds it. P2 says whether reasoning about
disclosure beats a good static rule — and a negative there is a real result.

---

## 6. Metrics

| Group | Measures |
| --- | --- |
| Learning | Prediction MAE per agent over episodes; adaptation latency after shift; error on a recurring regime |
| Decision | Regret vs P3, episodes to stable choice, refusal correctness |
| Attribution | Segment-localisation accuracy by method; correct-action and correct-non-action rate; disruption avoided |
| Disclosure | Records, fields and bytes disclosed per episode and cumulatively; which fields; split by knowledge kind (state vs outcome) |
| Negotiation | Rounds, refusals by reason, agreement rate, `no_agreement` rate |
| Faithfulness | Grounding-gate firing rate, ungrounded claims about peers, citation resolution failures |
| Cost | Tokens and latency per decision; transactions, disruption datagrams, occupancy; A2A messages and bytes |

Per agent, always. The three agents are differently positioned and that is the
entire point — an aggregate hides the result.

Service delivery and correct refusal are reported separately. A refusal is not a
failure.

---

## 7. Build phases

**Phase 0 — unblock measurement.** Close **F4** (receiver freshness) so a sample
can be proven to postdate a change. Run `sudo scripts/service-up.sh` end to end
on a prepared host and capture the first real run bundle. Never yet done.

**Phase 1 — condition harness and segment attribution.** Two pieces of
fixture, both read-only or environment-level, neither needing an agent:

- `tc netem` profiles, the three visibility classes, and the schedule driver
  (design §4.1).
- Segment counter collection at the four bracketing interfaces (design §9.1),
  using telemetry that already exists.

**Then verify the premise, before building any agent.** Three checks, and each
one can kill the paper cheaply:

1. Delivered ratio genuinely varies by configuration under the schedule. If it
   does not, there is nothing to learn.
2. A locally-invisible impairment is absent from every domain's counters and
   present at the receiver. If a domain can see it locally, C4 evaporates.
3. Segment losses sum to end-to-end loss within tolerance. If the decomposition
   does not close, exact attribution is unavailable and C7 falls back to the
   statistical methods.

Fix **F3** here if check 3 fails for parsing reasons rather than physical ones:
the telemetry extractor has never been run against the pinned SR Linux image.

**Phase 2 — MCP server and one agent.** `packet-a-mcp` first: the tool contract,
domain scoping, and device credentials held there rather than in the agent
(design §13). Then `agent-packet-a` as its only client — gates, journal, context
store, graph projection. No peers, no reasoning.

**Phase 3 — three agents over A2A.** Agent Cards, task lifecycle, six exchanges,
round cap, unanimous commit. Deterministic decisions throughout. Delivers E1.

**Phase 4 — predictors and sharing.** RLS predictor with forgetting, EWMA
baseline, `OUTCOME` publication, and the S0/S1/S2 switches. Delivers E2 (three
conditions), E3, E4.

**Phase 5 — the reasoning layer.** Engine at its thirteen nodes, retrieval,
grounding gate, and the S3 disclosure decision. Delivers S3 and E5.

**Phase 6 — evaluation.** Full grid, seeds and model version pinned, bundles
archived.

Close **F2** before Phase 4: a repair that requires the failed router to answer
gNMI cannot support the assurance episodes.

**Indicative effort**, one person working steadily: Phase 0 one to two weeks;
Phase 1 three to four; Phases 2–3 six to ten; Phase 4 three to four; Phase 5
six to eight; Phase 6 six to eight; writing four to six. Roughly seven to ten
months end to end. The premise checks in Phase 1 are the cheapest possible
place to discover the study does not work.

**Reproducibility.** Pin model id and version, temperature, retrieval budgets,
embedding model, A2A spec version, netem profiles, forgetting factor, and seeds.
Archive every prompt and response tagged with the issuing node. A result that
cannot be replayed from the journal is not a result.

---

## 8. Explicitly not in this paper

Deferred to a possible second paper, or out of scope entirely:

- **Whether reasoning beats rules in general.** Only the disclosure decision is
  tested (P2). The broader question is a different paper.
- **Retrieval-mode comparison.** GraphRAG is used to interpret peer evidence.
  Comparing it against flat RAG is not a claim here.
- **Per-node LLM ablation.** Interesting, and not this paper.
- **Fault diagnosis as a contribution.** Faults are a condition generator, not a
  subject.
- **Bandwidth allocation.** One flow, no policing. Offered load is never
  reported as a reservation.
- **Optical restoration.** One fibre chain; a cut is unrecoverable by design.
- **Scale.** Three owners, eight routers, eight configurations. No scalability
  claim.
- **Adversarial peers.** Honest but self-interested. A peer that lies about its
  own telemetry or outcomes is out of scope — though it is the obvious
  follow-on. Design §12 states the controls that *are* in place (mTLS, signed
  and bound messages, replay records, peer text handled as data rather than
  instruction); none is evaluated as a defence here.
- **Privacy guarantees.** Disclosure volume is *measured*, not *defended*. No
  differential-privacy or secure-aggregation claim.
- **Whether full topology replication is realistic.** Structure is replicated in
  every condition and treated as an assumption, stated as one. Whether operators
  would agree to it is a policy question, not a result here.
- **Commercial settlement.** No currency, no pricing.

---

## 9. Relationship to the previous design

The documents in [`old/`](old/) describe a wider system built on ACO, PSO and
Nash bargaining, plus an allocation simulator that was never built. They are
retained as source material — the related-work survey, the installation guide,
the data-plane specification and the known-issues register remain useful. The
data-plane specification in particular records the optical decoupling caveat
that design §4.1 is built around.

The scope reduction removed mechanisms this testbed could not evidence. It
removed no demonstrated result, because there were none.
