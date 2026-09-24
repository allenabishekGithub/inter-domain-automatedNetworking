# Paper 1 — Research and build plan

**Updated:** 24 September 2026.

**Status:** proposed; no algorithmic advantage or live recovery result established.

**Target:** IEEE TNSM. Confirm the institution's required Q1 database, category,
and edition before submission.

**Research basis:** [TNSM proposal](tnsm-proposal.md) and
[state-of-the-art assessment](state-of-the-art.md).

**Implementation reference:** [shared design](design.md).

## 1. The question

Can scheduling compatible cross-domain evidence for the anticipated execution
time improve service recovery under disclosure limits, compared with established
active diagnosis using the same validity and authority checks?

The controller chooses measurements, collection order or concurrency, and when
to act, recollect, or escalate. Changing state and delayed responses can
invalidate a useful observation before the pending action. Merely rejecting old
records is a baseline capability, not the proposed contribution.

## 2. What is new

Novelty remains conditional. The candidate extension jointly considers:

- complementary evidence groups, such as counters for a common packet cohort;
- owner-specific permitted fields, disclosure costs, and collection delays;
- uncertainty about state at the anticipated execution time;
- permitted actions and their expected service effects;
- loss incurred while acquiring evidence, waiting, or escalating.

The contribution must exceed a well-adapted decision-region method with freshness
checks. Action-based diagnosis, EC2, HEC, vertical federated learning, and
cross-domain telemetry are precedents documented in the review. No claim of
being first, optimal, privacy-preserving, or unconditionally safe is authorized
by this plan.

## 3. Claims

The following are **testable hypotheses**, not results. H1–H3 replace the old
C1/C2/C4/C6/C7/C8 Paper 1 claims; those IDs in historical assessments refer to the
pre-review proposal. They are also distinct from the C1–C3 implementation
findings in the retained implementation findings in §16.

| ID | Hypothesis | Required comparison |
| --- | --- | --- |
| H1 | The method improves the recovery–disclosure tradeoff under constrained budgets | Equal-budget service loss versus strong fixed and adaptive methods; disclosure savings versus full permitted sharing at predeclared recovery/risk/coverage margins |
| H2 | Anticipating group validity reduces wasted collection and improves timely recovery when evidence is delayed or state changes | Same execution checks throughout; ablate group scheduling and prediction of validity; include a stationary control |
| H3 | The useful tradeoff persists in specified held-out regimes and larger configurations | Held-out incident streams, model error, refusals, and increasing domains/evidence/action counts; report failure boundaries |

Platform correctness is an E1 prerequisite, not an additional novelty claim.
Lower predictor error or an absence of actions cannot by itself establish H1.

## 4. The core experiment

Start with three domains and the eight existing joint configurations. Build an
offline, deterministic incident replay with explicit time, request delays,
observation windows, counter cohorts, owner revision vectors, and policy changes.
Allow requests for either stored records or fresh measurements; charge their
declared costs separately.

Maintain uncertainty over network state and estimate action effects using a
declared model. Calibrate that model with controlled training interventions.
Hold evaluation incidents out, including timing patterns and impairment regimes.
The hidden injection schedule and counterfactual outcomes belong to the evaluator
and are never runtime features.

For each replayed incident, run all methods with paired exogenous conditions,
identical owner policies, action spaces, management resources, and execution
checks. Observe consequences over a fixed horizon even after refusal or
escalation. A no-change outcome continues to incur impairment if service remains
degraded. Define which incidents are repairable under the allowed actions using
evaluator-only information.

Use the offline pilot to test the algorithmic idea before the complete runtime.
Later reproduce selected conditions on the live testbed and distinguish measured
traffic from simulated outcomes. Eight configurations bound the pilot action
space; they do not establish scalability.

## 5. Experiments

| ID | Experiment | Design and purpose |
| --- | --- | --- |
| E1 | Platform and measurement validity | Healthy provisioning, unrepairable cases, matched flow/cohort counters, resets, receiver sample freshness, approvals, local-only effects, F2 recovery, and truthful verification |
| E2 | Recovery versus disclosure | Sweep budgets and permitted fields across healthy, repairable, and unrepairable incidents; compare cumulative loss, recovery time, risk, coverage, and disclosure |
| E3 | Delay and changing state | Vary response and execution delays, parallel-request limits, path changes, policy revisions, and observation validity; measure expiration/recollection and run a stationary negative control |
| E4 | Missing evidence and model error | Refusals, dropped responses, counter uncertainty, unseen impairments, incorrect priors/action effects; score missed repairs and escalation cost as well as harmful actions |
| E5 | Generalization and scale | Hold out regimes/topologies; increase domain count, candidate configurations, and evidence sources independently; report planning time, memory, message volume, and recovery quality |

The visibility classes in the shared design remain useful fixtures. Validate
which permitted local observations each fixture actually changes; do not impose
flat learning curves or label a condition locally invisible by assertion.
Model-only gOSNR changes are a negative control unless a separate impairment
coupling is implemented and identified as such.

## 6. Baselines and ablations

Baseline IDs here are local to Paper 1.

| ID | Method | Purpose |
| --- | --- | --- |
| B0 | Local/receiver evidence only, with declared permitted feedback | Operational floor; do not disable legitimate local information to manufacture an advantage |
| B1 | Fixed matched-counter bundle plus declared alternate-path checks | Strong simple rule; use synchronized/cohort-compatible acquisition |
| B2 | Full permitted evidence sharing, with freshness maintenance | High-disclosure reference; it obeys policies and is not an oracle |
| B3 | Information-gain and value-of-information acquisition | Separate implementable variants with published/adapted objectives documented |
| B4 | EC2/HEC-style decision-region acquisition plus validity checks and reacquisition | Closest methodological comparison; document assumptions, adaptations, and departures from original guarantees |
| B5 | Periodic refresh plus adaptive diagnosis | Tests whether ordinary refresh removes the proposed advantage; tune its period fairly |
| B6 | Proposed group scheduling for anticipated execution-time validity | Candidate method |

All methods have the same validity predicate, authority checks, action-risk
threshold, action-effect model access, and post-action verification. Each may
recollect invalid evidence. Hold management concurrency limits and accounting
constant; count refresh traffic and refused requests according to declared costs.

For sufficiently small instances, compute an exact **model-based** reference
policy or exhaustive schedule under the same information constraints. A
clairvoyant evaluator with future fault knowledge, if shown, is a separate bound
and must not be described as a deployable baseline.

Ablate joint grouping, anticipation of expiration/invalidation, and replanning
after responses. Keep the execution checks enabled in every acquisition ablation.
Use shared held-out tuning budgets and state computational limits. An RLS/EWMA
predictor comparison may be diagnostic; it is not a replacement for B1/B4/B5.

## 7. Metrics

**Primary:** cumulative service impairment over a fixed incident horizon at
matched disclosure budgets. Specify the service objective, weighting of waiting
and switching disruption, and risk threshold before confirmatory runs. Also
report the components separately and sweep weights or constraints.

| Metric family | Required outputs |
| --- | --- |
| Recovery | Time to receiver-verified recovery; success rate; time outside the objective; unresolved loss through the full horizon |
| Action risk and coverage | Harmful actions under a prespecified operational/counterfactual definition; attempted repairs; avoidable abstention and missed repair opportunities; risk–coverage curves |
| Disclosure | Requests, fields/records, bytes, owner-specific sensitivity costs, and amortized refresh traffic; this is an exposure proxy, not a privacy guarantee |
| Acquisition efficiency | Expired or incompatible records, rejected groups, recollections, response latency, and collection-to-execution delay |
| Decision quality | Regret against the declared model-based reference where computable; calibration and prediction error only where models are used |
| System cost | Planner runtime, memory, messages, model-training cost, and action-verification overhead |

A live incident cannot reveal the outcomes of both changing and retaining the
configuration simultaneously. Identify counterfactual estimates from controlled
replay separately from measured live outcomes. Do not censor unresolved incidents
out of recovery-time plots or present abstention as successful recovery.

## 8. Build phases

### Phase 0 — Measurement contract and live prerequisites

Define packet cohorts/windows, counter semantics, timestamps, revisions, and
fresh receiver evidence. Resolve and validate F4, F3, F2, and F6 as required for
the live experiments; retain other findings in [§16](#16-implementation-prerequisites-and-retained-findings).
Run the lab and capture an E1 bundle before claiming live recovery.

**Exit:** documented measurement limits and reproducible platform checks.
The offline pilot may begin while live prerequisites are being resolved.

### Phase 1 — Harness and comparative pilot

Build the condition harness and offline event replay. Provide healthy,
repairable, and unrepairable cases, delays, state changes, owner refusals, and
model error. Separate runtime inputs from evaluator truth.

Implement B1, B4, and the proposed method first, plus the small-instance
reference where feasible. Define the objective, permissible evidence, action
model, and validity predicate before tuning. Add B0/B2/B3/B5 to confirm that any
advantage survives stronger comparisons.

**Exit/go-no-go:** a reproducible comparison showing where the proposed method
helps, ties, and fails. Proceed if a meaningful recovery/disclosure advantage
survives common execution checks and realistic collection accounting. If fixed
bundles or adapted HEC match it across the relevant regime, revise the
contribution before building the complete agent stack. Publishable novelty
cannot be inferred from implementing the protocol.

### Phase 2 — One controller and scoped MCP access

Build one deterministic controller, the local tool server, evidence records, and
the acquisition loop. Enforce credentials and authorization below caller-supplied
domain labels. Implement request/response validity and journaling before writes.

**Exit:** replayable decisions, rejected stale/incompatible/unauthorized inputs,
idempotent effects, and verified local execution with retained evidence.

### Phase 3 — Three controllers and live recovery

Add peer identity, A2A application messages, scoped evidence requests, approval
dependencies, relevant revision invalidations, and receiver verification.
Record what was approved separately from what was applied. Exercise refusal,
timeout, partial application, and unavailable-device recovery.

**Exit:** selected E1–E4 scenarios reproduced live with accurate unresolved and
partial outcomes, no cross-owner writes, and attributable measurement records.

### Phase 4 — Expanded evaluation and research artifact

Freeze the algorithm, graph/schema version, baselines, tuning protocol, primary
metrics, and statistical analysis. Run E2–E5 on held-out incidents and release
configs, traces, analysis, and limitations.

**Exit:** claim-to-evidence review in §14, reproducible figures, and an updated
literature/venue check. Phase 4b (Paper 2) and Phase 5 (Paper 3) inherit this
validated base; neither is required for Paper 1.

## 9. Threats to validity

- An artificial disclosure policy can manufacture the benefit. Justify policies
  and include permissive, restrictive, and no-budget controls.
- Absolute timestamps do not establish compatible packet cohorts. Account for
  clock uncertainty, propagation, resets, duplicates, and background traffic.
- Each owner has its own revision sequence. Use scoped revision dependencies;
  identical numbers from different owners do not imply a common network state.
- The scheduler can be advantaged by access to the simulator's future state or
  true fault class. Enforce and audit the runtime/evaluator boundary.
- Priors or action-effect models may be wrong. Use training interventions,
  calibration checks, held-out regimes, and explicit uncertainty.
- A three-domain emulator is a feasibility test. Simulated scaling is useful
  but cannot establish carrier-scale live performance.
- Signatures establish provenance under their assumptions, not telemetry truth.
  Freshness/approval checks leave a validation-to-execution interval that must
  be modelled, bounded, or handled by recollection/abstention.

## 10. Not tested in this paper

Continuous interacting assurance loops and rate compensation are Paper 2.
LLM reasoning, semantic retrieval, and their incremental value are Paper 3.
Byzantine owners, cryptographic privacy, unconditional physical safety, and
production-scale deployment are outside the initial Paper 1 scope.

The current optical model does not make a changed gOSNR cause real packet loss,
and two wavelengths on one fibre do not provide fibre-cut restoration. Do not
claim those capabilities from the pilot.

## 11. Statistical design

Use independent incident streams/seeds as experimental units, with paired
conditions across methods. Split training, tuning, and final evaluation by
incident stream and, where appropriate, topology/regime; packets within an
incident are not independent replications.

Use pilot variance and a prespecified practically meaningful effect to determine
sample size. Declare primary budgets, risk limits, recovery noninferiority
margins, coverage requirements, and analysis before final runs. Report paired
effect sizes and confidence intervals, including uncertainty around harmful
action rates and unresolved incidents. Correct or clearly label exploratory
multiple comparisons.

A nonsignificant difference is not proof of equal recovery. Claims of reduced
disclosure at comparable performance require the declared margin and adequate
precision. Report null and adverse results and identify where method overhead
outweighs its benefit.

## 12. Run bundle and reproducibility

Every run must identify simulated versus live execution and include:

```text
manifest.json          code/config/schema versions, seeds, dependencies, mode
topology.json          owner slices, service path, action space, revision scope
policy.json            permitted evidence/actions, budgets, approval requirements
conditions.json        evaluator-only injections and exogenous timing
training-manifest.json training/tuning split, interventions, fitted model version
requests.jsonl         request groups, issue/completion times, cost, refusals
evidence.jsonl         values, owners, cohorts, windows, revisions, uncertainty
decisions.jsonl        estimates, eligible actions, selected request/action, stop reason
approvals.jsonl        owner authorization and exact action dependencies
effects.jsonl          attempted/applied changes and pre-execution checks
verification.jsonl    fresh receiver outcomes and unresolved/partial states
metrics.json           declared metrics and incident-level outcomes
analysis/              scripts and parameters that reproduce figures
```

Paths are a proposed artifact contract, not existing output files. Retain enough
raw counter/traffic data to audit derived measurements, plus the command,
environment, tool versions, and errors needed to replay the run. Keep evaluator
files inaccessible to runtime policies. Store credentials outside artifacts.
Record model assumptions and exact-baseline limitations.

## 13. Figures and tables

1. Recovery/service impairment versus disclosure, with uncertainty and coverage.
2. Recovery-time distributions including unresolved incidents.
3. Collection waste and recollection versus delay and state-change rate.
4. Harmful-action risk versus attempted-repair coverage.
5. Mechanism ablations under stationary and changing-state conditions.
6. Planner/system scaling and held-out-regime performance.
7. Prior-work comparison, baseline adaptations, and live-platform limitations.

## 14. Claim-to-evidence release criteria

| Item | Release criterion |
| --- | --- |
| E1 prerequisite | Measurement compatibility, receiver freshness, authorization, and applied-state verification are demonstrated within stated limits |
| H1 | Benefit survives B1/B4/B5 comparisons and full accounting for waiting, refresh traffic, disruption, and missed repairs |
| H2 | Gains persist with the same execution checks and are attributable to acquisition decisions; report stationary-case overhead |
| H3 | Held-out and scale results establish the stated domain of usefulness and expose failure boundaries |
| Reproducibility | An independent replay reproduces the tables/figures from retained artifacts |
| Novelty | Updated literature assessment supports a specific extension beyond active diagnosis plus freshness checking |

If the evidence supports only a subset, narrow the title, abstract, and claims.
If the pilot is negative, retain the useful platform work and revise the method;
do not substitute an architecture-only novelty claim.

## 15. Open decisions and defaults

| Decision | Default / resolution point |
| --- | --- |
| Controller engine | Deterministic for Paper 1; LLM evaluation deferred to Paper 3 |
| Objective and risk definition | Fixed-horizon operational loss with disclosure constraint; fix terms and thresholds during the pilot |
| Evidence validity | Cohort, revision, and uncertainty dependencies; calibrate timing assumptions, with no universal fixed freshness window |
| Action-effect model | Controlled training interventions and held-out validation; no hidden injection labels at runtime |
| Strong adaptive baseline | Implement and document EC2/HEC adaptations before claiming an advantage |
| Pilot expansion | Scale domains, evidence sources, and actions after Phase 1 justifies it |
| Statistical sample size | Determine from pilot variance and meaningful effects before confirmatory evaluation |
| Journal/Q1 check | TNSM on scope; verify ranking source/category/year and current submission requirements before submission |

## 16. Implementation prerequisites and retained findings

These open findings were recorded in the 17 September 2026 repository assessment
against commit `57755d478efb1984fc3438eca8d6342c31e441ca`. The assessment passed
86 component tests (46 packet, 40 optical) and exercised synthetic inputs/fake
devices; it did not validate a live lab. This table preserves the prerequisites
after removal of the standalone issue document. No item is closed by this
documentation update.

The current workspace is for planning and design. Run live checks in the
designated validation environment. Before closing an item, record its chosen
approach, resolving commit, and verification evidence. An unsupported capability
may instead remain explicitly excluded from the experiments and claims.

| ID | Open finding and required behaviour | Acceptance evidence and source |
| --- | --- | --- |
| F1 | Optical lifecycle cleanup and process signalling can affect unrelated instances. Track owned resources and validate process identity; keep global cleanup an explicit exclusive-host maintenance operation. | Start/stop leaves an unrelated fixture untouched; a stale PID cannot signal an unrelated process. [Optical lifecycle](../optical-network/topology.py), [startup](../scripts/service-up.sh), [shutdown](../scripts/service-down.sh). |
| F2 | Backup activation reads the primary core before writing, so gNMI failure can prevent repair even with a healthy backup. Distinguish forwarding failure, management-only failure, and unknown state; define corroborating evidence and policy. | Separate link failure, primary-router unavailability, and management-only failure yield a verified permitted action or explicit deferral. [Backup path](../packet-network/backup_path.py). |
| F3 | Telemetry parsing can drop path-keyed or module-prefixed responses without reporting incomplete coverage. Normalize supported forms and retain missing-data reasons. | Capture fixtures from the pinned image; supported responses produce attributed counters and malformed/partial responses cannot look complete. [Telemetry](../packet-network/telemetry.py), [gNMI](../packet-network/gnmi.py). |
| F4 | Whole-run receiver summaries can replace interval samples; stored logs can appear current; relative interval identities repeat across sessions. Add session identity, observation bounds, and explicit freshness. | Summaries cannot replace intervals; restarted sessions differ; stale/no-traffic is explicit; recovery evidence covers the required post-effect window. Merely seeing a previously unseen interval is insufficient. [Traffic](../packet-network/traffic.py). |
| F5 | Startup may report success before fresh delivery/attachment readiness, and partial failures or teardown errors may be obscured. Add preflight, bounded verification, owned-resource cleanup, deadlines, and aggregated status. | Failures at each stage produce truthful non-success outcomes and identify remaining resources; delayed attachment is handled. [Startup](../scripts/service-up.sh), [shutdown](../scripts/service-down.sh), [optical lifecycle](../optical-network/topology.py). |
| F6 | A failed second packet-route write can leave mixed state without durable receipts or reconciliation. Record progress and operation identity; do not claim atomic multi-router changes. | Second-write failure, lost response, and restart permit explicit reconciliation or unresolved reporting without blind repetition; verify delivery independently. [Backup path](../packet-network/backup_path.py), [controller contract](../mcp-server-design.md#shared-tool-and-result-contract). |
| F7 | Repeating an unchanged optical request can reset ROADMs and repeat disruptive writes. Add verified retain-current behaviour and partial-operation reconciliation. | Unchanged verified requests avoid resets; retunes are receiver-verified; failure at each step is partial/unresolved. [Optical client](../optical-network/client.py), [tests](../optical-network/tests/test_optical.py). |
| F8 | Optical `configured` status does not prove installed rules, supported-channel health, adequate monitor coverage, or service delivery. Keep observed configuration and verified health separate. | Missing/contradictory monitors yield unknown/degraded status; success cannot follow from `configured` alone. [Client](../optical-network/client.py), [CLI](../optical-network/main.py). |
| F9 | Attachment command failures can be unchecked and partial setup can leave resources behind. Track command status and owned-resource progress. | Failures at every attachment stage are reported and partial resources are removed or identified without global reset. [Attachment](../optical-network/packet_bridge.py), [lifecycle](../optical-network/topology.py). |
| F10 | CLI JSON can be mixed with prose, expected operational errors can escape handling, and one-shot telemetry cannot calculate rates. Define structured result/error and sampling contracts. | JSON commands decode as one result, failures have stable exit/error behaviour, and rates use at least two samples with unavailable/reset counters explicit. [Packet CLI](../packet-network/main.py), [telemetry](../packet-network/telemetry.py). |
| C1 | Caller-side inventory scoping and shared lab privileges do not establish independent operator authority. Add scoped credentials, certificate/identity checks, server-side enforcement, and separate bootstrap powers. | Wrong-domain requests denied at MCP, adapter, and device boundaries; document actual optical API binding/access. [Control boundary](../data-plane.md#control-boundary). |
| C2 | Retain independent evidence for the live fixture and claimed recovery/disruption results. Aggregate loss alone does not establish a contiguous outage duration. | Reproducible deploy–traffic–retune–packet-repair–optical-cut–teardown bundle with raw receiver, route, monitor, timing, version, and host records; see §12. |
| C3 | Keep capability claims, study scope, and provisioning semantics consistent. Paper 1 now studies evidence scheduling for recovery; Paper 2 adds continuous compensation; Paper 3 evaluates reasoning. | Review docs and manifests against implemented capabilities; use a policy-approved healthy-path provisioning action instead of relying on a repair command's rehearsal `--force` flag. |

Resolve F1–F5 before treating affected fixture output as reliable automated
experiment evidence. Resolve F6–F10 and C1 with the scoped controller/effect
workflows. C2/C3 are required before freezing claims and manifests. Existing
unit-test success alone does not close these findings. The explicit validity and
request-group mechanisms in this plan introduce further checks beyond this
historical list.
