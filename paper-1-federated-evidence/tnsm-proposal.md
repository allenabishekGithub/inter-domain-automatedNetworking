# Paper 1 — Proposed TNSM contribution

**Date:** 24 September 2026.

**Status:** recommended research proposal; algorithm, guarantees, and results
remain to be developed. The [plan](plan.md) specifies validation and build
phases; the [design](design.md) specifies the shared implementation.

**Basis:** [state-of-the-art assessment](state-of-the-art.md).

## 1. Recommendation

Develop **Recovery Under Limited Disclosure and Stale Evidence in Multi-Domain
Networks** as Paper 1's working topic.

The proposed contribution is an online method that jointly chooses **which
cross-domain evidence to request, when to collect it, and whether it supports a
permitted recovery action before its validity expires**. Investigate whether
planning evidence collection around the prospective execution time improves
recovery under disclosure limits compared with established active diagnosis
augmented with ordinary freshness checks.

This is a specific candidate for novelty, not verified priority. It is more
precise than proposing another agent architecture, a learning partition, or an
experiment showing that more information improves diagnosis.

IEEE TNSM explicitly covers service provisioning, reliability and quality
assurance, management functions, and policies, and welcomes both theoretical
and applied contributions. It asks for significant contributions supported by
evaluation, scalability analysis, or optimization. The topic fits that scope;
the work must still establish its contribution.
[Official journal scope](https://www.comsoc.org/publications/journals/ieee-transactions-network-and-service-management).

## 2. The operational problem

A service crossing Packet A, Optical, and Packet B starts losing traffic.
Each owner has partial observations and its own permitted actions. Some peer
records are expensive or prohibited to disclose. Measurements arrive at
different times, and paths or configurations can change during the investigation.

For example, comparing an upstream count from the previous path with a downstream
count from the current path can suggest a fault that the two measurements do
not actually establish. Requesting additional telemetry may delay recovery or
cause earlier measurements to become unsuitable for the pending action.

The proposed system should request a useful group of measurements, validate that
they describe compatible traffic and configurations, select a justified action,
obtain the affected owners' approval, and verify the outcome. If the evidence
cannot support a decision, it should request a fresh observation or escalate.
The cost of waiting or escalating must be included in the evaluation.

This is an illustrative scenario, not an observed repository result. Matching
timestamps alone is insufficient: counter comparisons require corresponding
packet cohorts, and topology/policy versions must be interpreted per owner.

## 3. What is already known

The [literature assessment](state-of-the-art.md) establishes precedents for
cross-domain inference, VFL, agent coordination, scoped evidence, and accountable
recovery. Additional decision-theory checks impose another boundary:

- Ash and Hayes-Roth's **Using Action-Based Hierarchies for Real-Time Diagnosis**
  (1996) already considers useful actions under incomplete diagnosis and
  deadlines. [Publisher abstract](https://www.sciencedirect.com/science/article/pii/S0004370296000240).
- Golovin, Krause, and Ray's **Near-Optimal Bayesian Active Learning with Noisy
  Observations** (NIPS 2010) develops EC2 for costly tests and equivalence-class
  determination. [Proceedings](https://proceedings.neurips.cc/paper/2010/hash/1e6e0a04d20f50967c64dac2d639a577-Abstract.html).
- Javdani et al.'s **Near Optimal Bayesian Active Learning for Decision Making**
  (AISTATS 2014) develops HEC for overlapping decision regions: identifying a
  sufficient decision need not identify one unique hypothesis.
  [Proceedings](https://proceedings.mlr.press/v33/javdani14.html).

Consequently, neither stopping once an action is known nor grouping faults by
their acceptable actions is our invention. Adding deadlines or metadata also
does not establish a contribution. The specific extension to test is the
interaction of changing network state, compatible measurement groups, owner
disclosure policies, and the evidence needed at execution time.

If an existing decision-region algorithm with a freshness filter solves this
problem equally well, the proposed algorithmic contribution has not succeeded.

## 4. Proposed technical method

### 4.1 Evidence and action model

Represent a measurement by its owner, service/flow scope, observed value and
uncertainty, packet cohort or interval, relevant configuration revisions, and
collection time. Represent requests by permitted disclosure level, cost, and
expected completion delay. Distinguish requesting a stored record from obtaining
a new measurement. Neither a timestamp nor a signature proves the value is true.

Retain an uncertainty model of the current network state. Old evidence may remain
useful historically while becoming inadequate to authorize a current action.
Propagate uncertainty over the collection and execution delay under explicit
state-transition assumptions. If the model cannot bound that evolution, require
fresh evidence or abstain; do not silently assume the network stopped changing.

For each candidate configuration, estimate service performance and switching
disruption using a declared action-effect model. Develop that model from
controlled training interventions and hold out evaluation cases. The fault
injector's hidden state is available only to the evaluator. A predictor fitted
to correlations is not automatically an action-effect model.

Owner approvals determine authority. Measurement validity determines evidential
support. Test them separately. Initially assume authenticated, cooperative owners
that can refuse disclosure; do not add Byzantine agreement or a claim of
cryptographic privacy to this paper.

### 4.2 Scheduling groups of evidence

For a candidate action, identify groups of evidence that would answer its
outstanding decision questions. Examples include paired boundary measurements
for a common cohort and observations of the proposed alternate path. Estimate
when the whole group could be available and whether it would remain useful
through the anticipated execution delay.

Select the next request group using its expected reduction in operational loss,
disclosure cost, completion delay, and likelihood of needing recollection.
Replan after responses, timeouts, or relevant state changes. Consider sequential
and parallel requests under the same management-plane resource constraints.

The reason to examine groups is complementarity: two matched counter readings
can establish something neither establishes alone. Whether exploiting that
complementarity produces an advantage over strong existing methods is an
experimental question. Greedy selection has no automatic approximation guarantee.

### 4.3 Stopping and execution

Stop collecting when a permitted action meets the declared risk/benefit
criterion, or when no feasible request can justify a decision within the budget
and deadline. Revalidate dependencies immediately before the external effect.
Record what was checked, what each owner authorized, what was actually applied,
and fresh receiver evidence of the result.

Do not describe this record as a proof of physical safety. A checkable record
establishes compliance with the stated model and checks. Any stronger guarantee
requires assumptions about measurement accuracy, state evolution, and the
validation-to-execution interval.

## 5. Research objective and candidate contributions

Optimize expected service impairment over a fixed incident horizon, including
waiting time and switching disruption, subject to a declared disclosure budget
and an action-risk constraint. Report all components separately and vary the
budget and risk threshold. Escalation is a distinct outcome; continued service
loss cannot disappear from the objective merely because the controller abstains.

Define harmful action relative to a prespecified counterfactual or operational
threshold. Controlled replay can estimate the consequence of keeping the current
configuration versus changing it. A live system cannot observe both outcomes
simultaneously, so distinguish evaluation ground truth from runtime estimates.

Three proposed contributions are:

1. **Problem formulation:** recovery decisions with disclosure restrictions and
   evidence whose usefulness depends on observation compatibility and execution
   time. Precisely show the difference from static decision-region determination.
2. **Method:** joint selection and scheduling of evidence groups and recovery
   actions, with a stopping rule and explicit handling of invalidated evidence.
   Supply an exact small-instance reference, complexity analysis, and a scalable
   approximation or heuristic. Prove only properties that actually follow.
3. **Systems evidence:** demonstrate when the method improves service recovery
   and disclosure cost across independent owners, including conditions where it
   provides no advantage. Release the workload, fault schedules, and artifacts.

A tractable model with a derived bound would strengthen the first two
contributions. The simple statement that an action passes the test used to
approve it is not, by itself, a substantive theoretical result. An empirical
systems contribution is possible if it establishes useful, generalizable
findings with sufficiently strong comparisons.

## 6. Experiments that decide whether the idea works

### Essential baselines

| Baseline | Purpose |
| --- | --- |
| Receiver-only sharing and competent local rules | Establish the cheapest useful operational baseline. |
| Fixed boundary-measurement bundles | Test whether a simple coherent collection rule already suffices. |
| Full permitted sharing | Measure the benefit and cost of broad observation access. |
| Information-gain or value-of-information acquisition | Compare with conventional active diagnosis. |
| EC2 or HEC as appropriate, with the same validity checks | Test the additional scheduling mechanism against action-oriented acquisition. |
| Periodic freshness refresh with adaptive decision selection | Isolate the benefit over ordinary refresh policies. |
| Exact planning for small instances | Measure heuristic suboptimality under the same modeled information. |

All decision methods receive the same permitted information, action-effect
model, owner approvals, and execution validation. In particular, the baseline
must reject stale or incompatible evidence too. The intended advantage is fewer
wasted requests and better timely decisions, not defeating a baseline by making
it knowingly use invalid data.

### Scenario dimensions and metrics

Vary report delay, state-change rate, missing responses, request budgets, and
disclosure policies. Include stationary cases, path changes during collection,
counter resets, multiple faults, and cases with no available repair. Test
miscalibrated delays and unmodeled faults. Do not deliberately cripple all
local observations to create the entire benefit.

Measure cumulative service loss, time to verified recovery, switching disruption,
harmful-action rate, avoidable abstention, disclosure volume, expired/recollected
records, and controller overhead. Plot recovery performance versus disclosure
budget with uncertainty intervals. Report risk and recovery coverage together;
always abstaining must not look like successful management.

Use paired fault schedules, independent runs, and a holdout by topology or
fault regime. Assess confidence intervals at the independent-run level rather
than treating correlated packets or adjacent time windows as independent trials.

## 7. Fit to the existing repository

Keep the three-owner architecture, service map, packet paths, receiver outcomes,
and finite action catalogue as infrastructure. Use deterministic controller logic
for the core experiments. Learning is optional for estimating action effects;
its prediction accuracy is secondary to recovery quality.

Use the eight configurations for a pilot and an exact reference. They do not
make evidence acquisition or its hypotheses equally small, so bound and document
the initial hypothesis and request spaces separately. Expand to other topologies,
services, and domain counts before broad scalability claims.

Close the measurement freshness, telemetry parsing, failed-primary recovery, and
partial-write issues in the
[implementation prerequisites](plan.md#16-implementation-prerequisites-and-retained-findings).
The existing optical margin model does not automatically change packet delivery.
Either validate an optical-to-service impairment relationship or describe the
study as network emulation with controlled packet impairments. Do not sell the
optical layer as a validated physical experiment without that evidence.

Keep continuous rate compensation and interacting-loop stability in Paper 2.
Keep LLM reasoning and retrieval comparisons in Paper 3. Paper 1 already has a
complete research question without those additions.

## 8. Immediate decision and submission claims

Build a small offline incident replay before the complete agent runtime. Establish
whether evidence actually becomes unusable during collection often enough to
matter, and whether scheduling matched measurements changes the achievable
recovery/disclosure tradeoff. Then compare the proposed rule against fixed
bundles and HEC/EC2 with freshness handling, and repeat the strongest cases on
the live emulator.

Predefine a meaningful service-recovery margin and disclosure saving from the
pilot/SLO requirements before evaluating the held-out scenarios. Continue only
if the improvement survives strong baselines and is not confined to an artificial
corner case. If conventional refresh and fixed bundles match the result, revise
the direction before scaling the agent infrastructure.

The contribution sentence to aim for, **only if the results support it**, is:

> We develop and evaluate an online recovery method that schedules compatible
> cross-domain evidence under disclosure limits, accounting for its validity at
> execution time, and quantify the resulting tradeoff between service disruption,
> decision risk, and information exchange.

Replace this with the actual algorithmic distinction and measured findings when
writing the manuscript. Do not add “first,” “optimal,” “privacy-preserving,” or
“guaranteed safe” without the literature, proofs, and threat model those claims
require. The recommendation is to investigate this precise method, not to submit
the current architectural proposal as an already novel system.
