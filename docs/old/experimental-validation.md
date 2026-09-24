# Experimental validation plan

**Target:** Elsevier *Computer Networks* agentic AI networking systems paper.
**Scope revised:** 23 September 2026.
**Status:** proposed experiments, not implemented tests or measured findings.

Study an integrated system for network services crossing independently owned
Packet A, Optical, and Packet B domains. **ACO, PSO, Nash bargaining, and continual
learning are required in B0 and in the contribution evaluation.** Component
removal is an ablation. The [paper plan](paper-positioning.md) and
[coupled method](agentic-system-method.md) define the research design.

Plan on the current VM; deploy and measure in the separate environment described
by the [installation guide](../../installation.md). The current data plane exists; the
agent federation, full allocation capability, and learned decision system do not
become implemented through this document.

## 1. Research questions and claims

| ID | Research question | Required evidence |
| --- | --- | --- |
| RQ1 | Can independently owned packet/optical agents jointly provision and assure a network service while each retains local authority? | Implemented local decisions, separate policies/credentials, intent origination at each owner, and independent receiver outcomes. |
| RQ2 | Does coupled ACO discrete search and PSO continuous allocation improve service/resource decisions enough to justify its cost? | Separate and joint ablations, matched fitness-evaluation budgets, conventional solvers, and small-instance reference bounds. |
| RQ3 | Does Nash bargaining provide useful service and owner-utility trade-offs under conflicting interests? | Matched feasible candidates, per-owner gains and disagreement values, refusal cases, and owner-respecting greedy comparison. |
| RQ4 | Does continual learning improve future decisions under changing conditions without unacceptable forgetting? | Chronological predict-before-update streams, frozen and memory-only baselines, recurring conditions, update cost, and service effects. |
| RQ5 | What does grounded agent reasoning contribute to evidence acquisition, diagnosis, and replanning? | B0/B1/B3 and reasoning-node comparisons, consumed decision traces, ambiguous cases, verified outcomes, and model overhead. |

**Collective intelligence is a cross-cutting hypothesis, not a fifth mechanism
or an assumed result.** Test whether peer evidence, counteroffer-driven revision,
and outcome-informed learning improve joint service decisions at a justified
cost while each owner keeps its authority. E10 connects RQ1/RQ5 to adaptive
feedback versus fixed proposal exchange; E11 connects RQ1/RQ4 to feedback ×
learning; E09 retains the distributed/centralized comparison. Agent count, shared
topology, message volume, and narrated reasoning do not establish this benefit.

### 1.1 Scope of this study

Required: full-system integration, path/allocation choices, distinct owner
preferences, service competition, demand/quality shifts, assurance, learning
adaptation, and the marginal and interaction effects of all four mechanisms.

No claims of topology privacy, truthful strategic reporting, production high
availability, arbitrary device control, or universal scalability follow from this
study. Detailed message-fault, transaction-race, consensus/failover, and Byzantine
experiments are outside the research scope. Ordinary execution failures still
need bounded handling and truthful reporting.

A refusal/deferment can be correct behavior but is not delivered service.
Never combine those outcomes into a single favorable success denominator.

### 1.2 Publication scope profiles

| Profile | Purpose and capability | Interpretation |
| --- | --- | --- |
| P0: required allocation/learning simulator | Three separately controlled owners, multiple demands, discrete alternatives, continuous allocations, chronological shifts, and independent resource/outcome models. | Mechanism and learning findings within the disclosed simulation; not measured physical forwarding. |
| P1: current packet–optical emulation | Eight SR Linux routers, four-ROADM Mininet-Optical line, two selectable wavelengths carried one at a time, one reference UDP flow, and scoped agent adapters to build. | Emulated service integration and supported packet recovery; modeled optical quality. |
| P1-A: allocation-capable emulation to implement | Service identifiers, owner-scoped per-service shaping/scheduling, optical-capacity accounting, competing flows, readback, and independent measurements. | Required before claiming measured PSO allocation/competition benefits on the emulated network. |
| P2: hardware | Actual selected controllers/devices and calibrated observations. | Additional hardware-specific evidence, not a prerequisite. |

P0 and P1 are required complementary evidence. P1-A is required for *emulated
allocation* claims; otherwise label those results P0-only. The existing eight
configurations cannot by themselves establish useful PSO allocation, broad search
advantage, or learning under resource competition. Larger discrete candidate sets
and resource competition are required in P0, not an optional afterthought.

## 2. Freeze the experimental contract

Before confirmatory runs, freeze hypotheses, primary effects, workloads, owner
policies, units, objective functions, initial predictors, numerical algorithms,
seeds, replay/update schedules, promotion rules, budgets, prompts, base model
versions, and independent checks. Preserve code/container/index versions and
machine resources. Predeclare exclusions and stopping rules.

Learning changes predictor parameters during a chronological trial, according
to the frozen rule. Do not freeze the evolving state in B0 or retune update
hyperparameters on future evaluation data. Keep base LLM weights fixed unless
explicitly evaluating their training separately.

Pilot changes create a new experiment version. After a fix, rerun the affected
matched comparisons; do not pool only favorable old/new results.

## 3. Testbed and independent measurement

Use [data-plane.md](../../data-plane.md) for exact nodes, addresses, ownership, and
current capabilities. Packet A owns sender operations; Packet B owns fresh
receiver measurements; Optical owns the fixed optical line. A2A carries peer
evidence and local MCP instances expose owned observations/actions.

Require separate owner policies, inventories, credentials, and adapter access.
Distinct containers using one unrestricted privileged backend do not establish
independent ownership. A synthetic-owner lab does not imply commercial deployment.

P0 must expose the same type of decision interface but retain an independent
ground-truth resource ledger and outcome generator. Do not evaluate prediction
accuracy against the predictor's own outputs. For P1/P1-A, independently collect
receiver goodput/loss, path readback, allocation enforcement, optical readings,
and action times. Do not use majority model opinion or a controller ACK as truth.

Record modeled versus observed delay, capacity, QoT, and costs. The current
1 Mbit/s is offered traffic, not reserved bandwidth. Both optical wavelengths
use the same fiber chain; a cut has no alternate route. Current optical monitor
output is not independent proof of installed rules or end-to-end delivery.

Resolve the relevant [known issues](known-issues.md), especially unreachable-router
recovery, telemetry parsing, stale receiver summaries, unchanged optical resets,
and optical-health interpretation, before relying on automated experiment output.
Retain raw run bundles; unit tests alone do not validate live delivery.

## 4. Workloads and parameter sweeps

Use structured intents specifying endpoints, service class, minimum/maximum
bandwidth, measurable latency/loss objectives, duration, deadline, and declared
budget. Vary owner preferences independently of physical feasibility.

| Workload | Required variation |
| --- | --- |
| Healthy provisioning | Intent at each owner, feasible requests, and authorized but infeasible requests. |
| Resource competition | Multiple demands sharing bottlenecks, minimum-rate constraints, varying discrete alternatives, and changing arrivals. |
| Owner conflict | Different resource prices, disruption aversion, service values, disagreement values, and fixed bargaining weights. |
| Assurance | Packet A/B faults, optical cut, ambiguity, absent observations, and supported repairs only. |
| Learning streams | Stationary regime, gradual/abrupt demand or measured-quality change, and recurrence of earlier conditions. |
| Held-out combinations | Fault location × evidence availability × owner preferences × demand regime, separated from development. |
| Collective decision cases | Complementary owner observations, candidate-specific counteroffers, shared bottlenecks, and cases where initial proposals already suffice or no acceptable agreement exists. |

For P0, predeclare small exact-reference instances and larger finite candidate/
demand settings. Choose sizes from pilot feasibility, report the actual grid,
and cap algorithmic compute. Do not disguise a scalability claim as a single
three-owner result. P1 begins with calibrated reference traffic; P1-A traffic
must demonstrate actual capacity competition without host bottlenecks dominating.

Freeze common exogenous request/fault streams. Closed-loop methods may observe
different outcomes after taking different actions; pair the external conditions,
not fictitiously identical post-action telemetry. Use identical recorded
snapshots only when isolating decision logic.

Calibrate host throughput, controller delays, observation windows, probe overhead,
clock error, and inference resources. A tiny packet sample cannot establish a
rare-loss guarantee. Report RTT when one-way delay is not independently measurable;
do not silently use RTT/2 or add measured percentiles across domains.

## 5. Systems and baselines

| ID | Definition | Main contrast |
| --- | --- | --- |
| B0 | Full owner-agent system: grounded reasoning + ACO + PSO + Nash bargaining + continual predictor learning. | Proposed system. |
| B1 | B0 with all generative calls replaced by documented evidence-driven rules and learning-hypothesis templates; retain all four numerical/learning mechanisms. | Incremental LLM value, not removal of optimization or learning. |
| B2 | Centralized LLM planner with the same ACO/PSO/Nash objectives, learner/update rules, authorized evidence/tools, and aggregate compute/model budgets; owners still approve local actions. | Placement of planning, not extra control authority. |
| B3 | B0 with a competent fixed diagnostic observation order and explicit stopping conditions; same model and four mechanisms. | Adaptive observation selection. |
| B4 | Simpler owner-respecting system using constrained K-shortest paths, a constrained non-swarm allocator, greedy agreement with local consent, fixed predictors, and deterministic diagnosis. | Whether the integrated complexity is worthwhile. |

Give baselines comparable development effort, supported actions, observation
availability, policy checks, user objectives, and independent measurements.
B2 retains owner-specific predictors and receives no privileged ground truth.
B3 retains diagnostic/proposal reasoning but its dispatcher follows the fixed
query order. Publish actual feature matrices and per-component budgets.

Use the same initial predictor and optimizer states. Match aggregate objective
evaluations for numerical search, observation budgets for acquisition, and
input/output allowance and model/version for model comparisons. Also report
wall time: an equal evaluation count does not imply equal execution cost.

### 5.1 Required component ablations

| ID | Change from B0 | Isolation rule |
| --- | --- | --- |
| A1: no ACO | Conventional constrained path search replaces ACO. | Keep PSO, Nash, learning, and candidate/evaluation limits matched. |
| A2: no PSO | Constrained non-swarm allocation replaces PSO. | First use identical discrete candidates and utility estimates; then compare closed-loop effects. |
| A3: no Nash | Greedy selection using a fixed declared service/normalized-utility objective. | First use identical candidates to isolate selection; in end-to-end tests replace any Nash-based PSO fitness too. Retain each owner's positive gain, policy, and consent. |
| A4: frozen learning | Freeze the initial performance predictors. | Retain ordinary ACO pheromone updates, PSO, reasoning, and Nash; disable predictor updates only. |
| A5: memory only | Retrieve past outcomes with fixed predictors. | Distinguish remembering incidents from continual parameter learning. |
| A6: reasoning nodes | Disable each online reasoning node and the learning-hypothesis LLM separately. | Retain numerical optimizers and deterministic learner/update rules. |
| A7: retrieval | Compare document, graph, and structured context. | Match context budget and retain all local authorization/feasibility checks. |
| A8: fixed proposal exchange | Retain ACO, PSO, Nash, and continual learning, but freeze the path/allocation candidate pool after initial submission. | Disable post-submission peer-driven candidate revision; retain numerical fitness queries, current feasibility checks, owner veto, and selection among still-valid submitted candidates. |

Required interaction tests: ACO × PSO and predictor learning × Nash selection,
plus adaptive peer feedback × predictor learning in E11, with prespecified
workloads and budgets. A complete 16-cell sweep of the original four mechanisms
is not mandatory; explain which interactions the design can identify. Independent
improvements do not by themselves prove synergy. Use exact enumeration and a
certified continuous reference where tractable, and report solver limits.

### 5.2 Fixed proposal exchange control (A8)

A8 is a competent non-adaptive-exchange control, not disconnected agents unable
to establish a service. Use the same approved topology, initial evidence package,
owner policies, initial predictors, algorithms, and aggregate budget caps as B0.
Owners generate and assemble compatible initial proposals using ACO/PSO, with
the same numerical capacity/utility queries and Nash-derived fitness as B0.
Ordinary optimizer updates and local reasoning are retained. Define the initial
evidence-gathering procedure and proposal-submission boundary before trials.

After submission, freeze the set of path/allocation pairs. Owners still evaluate
gains, perform Nash selection, approve or refuse, execute locally, and verify
delivery. New peer diagnostic evidence or counteroffers cannot initiate new
observation requests or candidate construction within that episode. Freshness
and safety checks remain mandatory: invalidate stale/unsafe candidates, recompute
their gains when needed, and reselect among still-valid submitted candidates or
report no agreement. Never execute a stale plan to make the control look worse.

Continual predictor updates still occur after scored outcomes and may change
the initial proposals of later episodes. A8 alone is not frozen learning and
is not removal of Nash bargaining. Define an episode as the complete request
or fault-response decision up to its deadline; a counteroffer cannot be relabeled
as a new episode to evade the fixed-pool restriction.

Let A8 spend its allowed search budget on initial proposals, while B0 divides
the same total budget between initial search and feedback-driven revisions.
Neither condition gets an extra budget per round; declare each budget schedule,
maximum rounds, and stopping rule. Match permitted observations, model versions,
utility access, and development effort. Report actual cost and equal-budget
quality curves; unused budget is not evidence of equal execution time.

This contrast isolates the *bundle* of post-proposal peer evidence acquisition
and replanning, not all inter-agent communication or an individual message's
effect. Use E10's equal-information decision replay to separate that bundle from
simply giving one planner additional information. No owner checks are ablated.

## 6. Instrumentation, outcomes, and metrics

Retain episode/service/owner IDs, timestamps and clock uncertainty, requests,
observation sources, candidate paths and allocations, rejected options, utility
components, owner gains, bargaining rounds, actual local actions, raw receiver
outcomes, and stopping reasons.

Record ACO/PSO seeds, parameters, fitness evaluations, feasible-candidate coverage,
and time. Record model/version, prompts, context IDs, output, gate result, actual
consumed choice, latency/tokens/cost, and fallbacks. Record predictor versions
before/after, replay samples, training/validation cutoffs, update cost, and
promotion/rejection. Never retain credentials or expose private chain-of-thought.

For collective decisions, link each consumed peer observation, constraint, or
counteroffer to its source owner/time, receiving node, episode/round, before/after
candidate versions, predictor version, and resulting supported action or
`no_change`. Record why a revision stopped and which budget it consumed. Connect
completed outcome IDs to later predictor releases and proposals; messages merely
delivered but not consumed are separate. These are structured decision records,
not a demand to expose internal model reasoning.

| Metric family | Operational meaning |
| --- | --- |
| Delivery | Verified within-deadline requests divided by all offered requests; additionally report independently feasible-request success. |
| Negative outcomes | Correct/false refusal, deferral, deadline miss, failed execution, unresolved delivery, and manual intervention separately. |
| Allocation | Delivered/allocated bandwidth, blocking, utilization, constraint violations, and stated-objective gap to the reference solution. |
| Owner benefit | Per-owner gains over disagreement, budget adherence, acceptance/refusal, and weighted log-gain when every gain is positive. |
| Agent decisions | Diagnosis accuracy/abstention against hidden ground truth, chosen observations, changed proposals, unnecessary writes, and interventions. |
| Assurance | Fault-to-detection, fault-to-sustained-recovery, SLA violation time, unknown observation time, and unrecovered fraction. |
| Learning | Pre-update prediction error/calibration, cumulative service performance, adaptation after a shift, loss on recurring old conditions, and update/promotion cost. |
| Collective decision effects | Paired service/owner outcome differences against A8 and B2; consumed peer evidence, proposal revisions, and links from learned estimates to later joint decisions. Trace counts describe mechanisms, not benefit by themselves. |
| Overhead | Observation/MCP calls, peer messages/bytes, numerical fitness evaluations, model usage, CPU/memory, training/replay storage, and total elapsed decision time. |

Define all units, denominators, censoring, and partial-credit rules before runs.
Do not use percentage improvement on negative log objectives without a valid
normalization. Jain's index or another fairness score needs a declared input;
it does not prove fair bargaining. Count failed calls and rejected updates in cost.

A configuration change is unnecessary only under a declared independent
minimal-action criterion; adjudicate ambiguous cases rather than assuming all
extra actions are wrong. Planned fault injection is not an operator intervention;
unplanned researcher diagnosis/repair is.

## 7. Common execution procedure

1. Restore the frozen initial network, learner, and optimizer states for each
   independent replicate; retain state within a chronological learning stream.
2. Verify setup, owner boundaries, clocks, measurements, and known resource limits.
3. Start independent probes and execute the paired external request/fault stream.
4. At episode `t`, predict and decide using only information available before
   the outcome; log the selected observations, ACO/PSO alternatives, owner gains,
   and accepted service decision.
5. Execute through owning controllers and independently verify delivery or failure.
6. Score episode `t` before releasing its observed labels to the learner; update
   using new and replayed past data, then promote or retain the prior predictor.
7. Continue through the preregistered horizon, including regime shifts and return
   to earlier conditions. Retain no-agreement, failed, and unresolved episodes.
8. Reset and repeat whole streams with independent seeds; randomize baseline run
   order and disclose cache/provider effects.

Scoring future episodes before updating is prequential evaluation. A locked
future test set must never drive training, tuning, or promotion. Past-only
validation used for promotion is distinct from the independent research evaluator.

## 8. Experiment catalogue

### E01 — Domain authority, identities, and controller boundaries

Check each owner's scoped observations/actions and its right to refuse.
Demonstrate distinct policies, separate controller access, and no cross-owner
mutation. These are systems prerequisites, not the novelty claim.

### E02 — Full cross-owner service loop

From each intent ingress, establish service, verify delivery, handle a supported
packet fault, and report an optical cut honestly. Trace reasoning, optimization,
agreement, execution, and subsequent learning. P1 validates only its actual
capabilities; P0/P1-A supply meaningful allocation episodes.

### E03 — ACO discrete search

Use growing candidate spaces and heterogeneous quality/cost conditions.
Compare A1 under equal search budgets; report quality, diversity, feasibility,
and overhead. The tiny eight-choice fixture is a sanity check, not proof of
search advantage.

### E04 — PSO continuous allocation

Use multiple services competing for finite resources. Hold discrete candidates
fixed for A2, then run the closed-loop comparison. Check rate/capacity constraints
independently. Report conventional-solver performance even when it beats PSO.

### E05 — Nash bargaining across owners

Vary owner preferences and disagreement values while holding feasible candidates
fixed for A3. Include cases where a single owner refuses and where no positive-gain
agreement exists. Report per-owner outcomes, agreement rate, user QoS, and
cost—not only an aggregate objective.

### E06 — Continual adaptation and retention

Compare B0/A4/A5 on matched chronological stationary, shifted, and recurring
streams. Show actual parameter updates, prediction changes, and later service
effects. Report forgetting and update cost. No future labels or best-checkpoint
selection on the test stream.

### E07 — Agent diagnosis and assurance

Inject declared physical faults and separate missing/contradictory-observation
cases, hiding fault labels from agents. Compare B0/B1/B3 and A6/A7. Record
evidence selection, replanning, verified recovery, unnecessary optical resets,
and justified unresolved outcomes.

### E08 — Coupling and complete-system value

Run required ACO × PSO and learning × Nash interaction contrasts, and B0/B4.
Test whether the integrated loop changes allocations/agreements and networking
outcomes beyond isolated components, with total overhead included.

### E09 — Distributed versus centralized planning

Compare B0/B2 with equal authorized information opportunities, mechanisms,
objectives, aggregate budgets, and local owner approvals. Report delivery,
decision time, observation/communication cost, and owner outcomes. Do not weaken
the centralized baseline or infer fault tolerance from its absence of failures.

This is also the planning-placement control for collective intelligence. B2 may
query the same owner-local utility/prediction tools and keeps local approvals;
it receives no private evaluator state. A B0 advantage over A8 does not imply
an advantage over B2, and a centralized win does not invalidate the experiment.

### E10 — Peer-informed collective decisions

**Question:** does adaptive peer feedback improve decisions beyond competent
fixed proposal exchange? Compare B0/A8; reuse B2 from E09 to assess placement.
Run P0 for path/allocation and owner-conflict cases. Use P1 only for supported
diagnosis/recovery; allocation claims require P0 or validated P1-A capabilities.

Use complementary observations, shared bottlenecks, and candidate-specific
counteroffers that can revise a proposal. Include single-domain-evidence cases,
already-sufficient initial proposals, redundant peer evidence, and infeasible
requests. These controls test when collaboration is unnecessary or cannot help;
do not choose only cases that force a fixed-exchange failure.

1. **Equal-information decision replay:** supply every planner the same finite
   pre-action evidence snapshot, with equal numerical utility-query access,
   initial predictor state, and total search/model budgets. Keep outcome labels
   hidden and do not supply observations caused by a future action. Compare
   proposal quality, independent feasibility, owner acceptance, and cost.
   Differences here cannot be credited simply to one method seeing more facts.
2. **Closed-loop service trials:** match initial evidence, allowed observation
   opportunities, exogenous request/fault streams, and total budgets. B0 can
   request peer evidence and revise after submission; A8 follows section 5.2.
   Independently measure actual outcomes. Different actions can produce different
   subsequent telemetry; do not force that telemetry to be identical.

For provisioning, predeclare verified delivery within deadline divided by all
offered requests as the primary service endpoint. For assurance, use SLA-violation
duration with unresolved cases retained. Report feasibility/false refusals,
per-owner gains, agreement rates, unnecessary changes, decision time, peer
messages/bytes, and model/search costs. Separate gains conditional on agreement
from agreement frequency so dropping difficult cases cannot look beneficial.

Report paired effects and uncertainty, not a single "collective IQ" score.
Show consumed-evidence-to-revision traces alongside the comparisons; traces alone
are not causal proof. The replay and closed-loop contrasts answer different
questions and must be reported separately. Claim benefit only for tested cases
and report overhead, null effects, and regressions.

### E11 — Continual learning and collective adaptation

**Question:** do updated predictors improve subsequent joint decisions, and
does adaptive peer feedback change that learning benefit? Extend E06 with a
required feedback × learning contrast; reuse E10's fixed-exchange definition.

| Condition | Post-proposal peer feedback | Predictor updates |
| --- | --- | --- |
| B0 | Adaptive | Continual |
| A4 | Adaptive | Frozen |
| A8 | Fixed proposal exchange | Continual |
| A8 + A4 | Fixed proposal exchange | Frozen |

All cells retain ACO, PSO, Nash, owner approval, and ordinary optimizer-state
updates under the same declared rules. Also reuse A5 (adaptive feedback with
memory retrieval and fixed predictors) to distinguish parameter learning from
remembering outcomes. Keep retrieval configuration matched in each factorial
contrast. Do not add federated training, parameter averaging, or LLM fine-tuning.

Run independently reset chronological streams through stationary conditions, a
demand/quality shift, and recurrence of an earlier regime. Score each episode
before training on its outcome; freeze its predictor versions while it runs.
Match initial state, exogenous streams, update rules, and aggregate resource
caps, and report training as part of cost. Training examples may diverge after
different actions; this is a closed-loop effect, not permission to use future
labels. No-update conditions need not waste resources on dummy training.

Record the chain from verified joint outcome to local parameter update, changed
prediction, later proposal/owner gain, and joint agreement or refusal. Model
parameters can remain local: changed estimates influence peer decisions through
proposals and attributable evaluations. Report prediction improvement separately
from actual service improvement and from the frequency of changed proposals.

Use the same predeclared stream-level service measure in all four cells, such as
delivery fraction after the shift. Let `Y` denote a condition's mean on that
measure. Estimate the interaction, with uncertainty over independent streams:

```text
Delta = (Y_adaptive,learning - Y_adaptive,frozen)
      - (Y_fixed,learning    - Y_fixed,frozen)
```

For lower-is-better measures declare the direction explicitly. Report both
learning effects even when the interaction is zero or negative. Also measure
adaptation time, recurring-regime retention, owner gains, and total overhead.
An additive learning benefit is not evidence of synergy with peer feedback.

## 9. Coverage and staged execution

Build the deterministic controller/measurement foundation first. Integrate
ACO/PSO/Nash, then reasoning and the required learner; run comparative pilots
early. A partial integration demo does not satisfy the complete paper scope.

Publish a coverage matrix for E01–E11, B0–B4, A1–A8, the combined A8 + A4
condition, P0/P1/P1-A, workload regime, and independent checks. Mark missing cells
`NOT RUN`, not successful. Required
mechanisms must be exercised on appropriate cases; they need not execute on
every healthy polling tick.

## 10. Statistical design and interpretation

The independent unit is a reset replicate or a complete chronological stream,
not each packet, optimizer iteration, or correlated learning episode.
Use matched exogenous streams/seeds and paired effect estimates. Preserve
within-stream dependence when bootstrapping or fitting repeated-measure models.

Predeclare primary service and mechanism endpoints, meaningful effect sizes,
sample-size/power reasoning based on pilots, and stopping criteria. Report
uncertainty, distributions, and sample counts; adjust for multiple confirmatory
contrasts or label exploratory analyses. Do not stop when significance appears.

Show completion-by-time with deadline/unrecovered fractions. Do not drop failed
runs to report a favorable recovery median. Plot learning curves with regime
boundaries and both predictive and service metrics. Report conventional methods
winning, null effects, regressions, and overhead trade-offs.

No finite error-free run proves a universal guarantee. Keep claims scoped to
the tested owners, objectives, resources, workload, and simulator/emulator fidelity.

## 11. Reproducibility package and result schemas

Retain versioned manifests, code/configuration, environments, topology/resource
models, owner policies, workload streams, hidden evaluation labels, raw independent
measurements, optimizer traces, model inputs/outputs, learning states/replay
membership, analysis scripts, and plot-to-run mappings.

Each manifest identifies profile, baseline/ablation, seed tuple, initial-state
hash, stream/regime, model/prompt versions, optimization and query budgets,
predictor/update configuration, and measurement windows.

For E10/E11, include feedback mode, initial evidence snapshot/package hash,
proposal-pool freeze point, round cap, budget schedule, and whether the run is
decision replay or closed-loop execution. Preserve peer-input-to-decision links
and outcome-to-predictor-to-later-proposal links in the run bundle.

Each summary identifies offered/feasible/delivered/refused/unresolved counts,
timing/censoring, owner gains, allocation checks, diagnosis, predictor errors,
forgetting, numerical/model/update cost, interventions, and raw-artifact hashes.
Use null with a reason for unavailable measurements, not zero.

Archive provider model IDs and dates. Recorded responses can replay decision
logic but do not replace live-model cost/variance measurements. Pricing needs
dated billing units; local inference needs hardware/runtime/resource disclosure.

Preserve invalid-harness runs with predeclared reasons. Controller/model failures,
poor optimization, and unsuccessful learning are system outcomes, not automatic
exclusions. A bug fix requires a new version and matched reruns.

## 12. Figures, tables, and paper presentation

Prioritize an owner-boundary architecture, coupled-method diagram, P0/P1 capability
table, baseline feature matrix, search/allocation quality-versus-budget plots,
per-owner bargaining outcomes, chronological learning/forgetting curves, required
interaction contrasts, and verified service recovery/cost results.

Include E10's outcome-versus-cost comparison and E11's four-condition interaction
plot. Label fixed-exchange and centralized controls explicitly; do not substitute
communication counts for verified service effects.

Every figure must link to real run IDs. Do not present hypothetical gains or
illustrative curves as results. Use a decision timeline showing observations,
ACO/PSO choices, peer feedback, accepted actions, verification, and the next
predictor release.

## 13. Threats to validity and mitigation

Main threats are a trivial search space, no real continuous actuator, simulator/
predictor circularity, host limits mistaken for network effects, future-data
leakage, unfair baseline tuning, correlated episodes, and attribution of
deterministic protection to a model. Address them through richer declared
fixtures, independent models/checkers, actual allocation readback where claimed,
chronological splits, matched budgets, and component/interaction ablations.

Full topology sharing is not confidentiality. Domain-specific utility gains can
reveal preferences. Synthetic cooperative owners do not establish resistance to
malicious or strategically dishonest operators. P1's single optical route does
not demonstrate general optical restoration.

Collective-intelligence threats include extra information/compute masquerading
as collaboration, weak fixed-exchange controls, correlated models repeating an
error, selection of only collaboration-favoring cases, and post-hoc stories about
which message caused success. Use E10's equal-information replay, matched total
budgets, competent A8, no-benefit cases, independent outcome checks, and E11's
factorial contrast. Three owners do not establish large-population emergence.

## 14. Claim-to-evidence release criteria

| Proposed claim | Minimum evidence |
| --- | --- |
| Cross-owner autonomous service system | E01/E02 and independent service measurements; actual owner isolation, not merely separate process names. |
| Useful ACO–PSO coupling | E03/E04/E08, matched budgets, conventional references, and explicit continuous decision support. |
| Useful Nash negotiation | E05 with heterogeneous owners and meaningful service/utility trade-offs. |
| Continual learning improves future service decisions | E06 with actual parameter updates, no future leakage, frozen/memory-only comparisons, retention, and overhead. |
| Generative reasoning adds value | E07 and B0/B1/A6 comparisons showing consumed decisions and attributable effects. |
| Adaptive peer collaboration improves joint decisions | E10 B0/A8 comparisons, equal-information replay and independently measured closed-loop outcomes, decision traces, overhead, and E09 B2 context; preserve owner consent. |
| Continual learning improves collective adaptation | E11's four conditions plus E06/A5; actual updates affect later joint decisions, with retention/cost reported. A synergy claim additionally needs the prespecified feedback × learning interaction. |
| Integrated system merits its complexity | E08/E09 and B0/B4, including negative cases and complete compute/communication/learning costs. |

These criteria do not guarantee positive findings or journal acceptance.
All four methods being mandatory does not make their superiority predetermined.

## 15. Method and comparison references

Use the [literature assessment](../../related-work-and-novelty.md) for algorithm and
agentic-system precedents. Existing ACO packet–optical and Nash multi-domain
optical research prevents novelty claims based only on applying their names.
The [collective-intelligence positioning](../../related-work-and-novelty.md#collective-intelligence-positioning)
records conceptual and cross-domain agent precedents; the term itself is not
the novelty claim.

For measurement definitions, use [RFC 7679](https://www.rfc-editor.org/rfc/rfc7679.html)
for one-way delay and [RFC 7680](https://www.rfc-editor.org/rfc/rfc7680.html) for
one-way loss, while declaring what the actual probes measure.
