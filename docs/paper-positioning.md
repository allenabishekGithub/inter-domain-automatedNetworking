# Agentic networking systems paper: scope and contributions

**Target:** Elsevier *Computer Networks* (COMNET).
**Direction:** revised 23 September 2026.
**Status:** proposed research system; no new implementation or measured result is
established by this document.

**Working title:** *Learning and Bargaining Agents for Cross-Owner Packet–Optical
Network Services*.

The paper studies autonomous provisioning and assurance of network services
across Packet A, Optical, and Packet B, **each owned by a different person or
organization**. Each owner has its own agent, objectives, resources, and right to
refuse. These are separate administrative owners, not merely technology layers
under one operator.

**ACO, PSO, Nash bargaining, and continual learning are all required parts of
the proposed system and the journal evaluation.** Removing one creates an
experimental ablation, not a smaller version that satisfies the full paper scope.
A2A and MCP remain implementation interfaces; local authorization and independent
service verification remain basic engineering requirements.

**Organizing idea: collective intelligence under independent ownership.**
The paper asks whether exchanging evidence, revising proposals in response to
peers, and learning from verified outcomes improves joint service decisions.
Agentic operation describes each DSO; collective intelligence describes the
group-level capability being investigated. It is not a fifth algorithm, a new
central authority, a shared LLM, or a claim established merely by having agents.

## 1. Define one coupled agentic networking problem

**Research question:** How can agents belonging to independent packet and optical
owners jointly search discrete service paths, allocate continuous resources,
reach mutually acceptable agreements, and improve subsequent decisions from
experience under changing demand and network conditions?

**Collective-intelligence hypothesis:** adaptive collaboration yields useful
service and owner-outcome improvements over competent fixed proposal exchange
at a measured cost. Test this across the existing RQ1, RQ4, and RQ5 rather than
adding a disconnected research theme. Distributed planning need not outperform
centralized planning on every workload.

The agent loop is:

```text
intent or service symptom → obtain local/peer evidence
→ ACO discrete candidates → PSO feasible continuous allocations
→ owner utility evaluation and Nash bargaining
→ locally approved execution → independent service verification
→ continual model update → improved inputs to later decisions
```

Peer constraints can trigger new observations, resource allocations, or path
candidates within a bounded decision budget. Agents must know when to retain a
healthy segment, counteroffer, defer, or reject an infeasible request. A service
failure on the only optical route cannot be repaired by pretending a second
wavelength is a disjoint route.

Three observable links define the proposed collaboration:

1. Peer evidence changes an observation request, diagnosis, or proposal.
2. An owner's constraint or counteroffer triggers revised ACO alternatives or
   PSO allocations, while Nash selection and individual approval remain required.
3. Verified cross-domain outcomes update local predictors whose later estimates
   change proposals or agreement choices. Sharing model parameters is not required.

The [method specification](agentic-system-method.md#collective-intelligence-through-peer-feedback)
defines bounded feedback and decision traces. Collective intelligence is not
collective authority: every owner retains its policy and refusal rights.

## 2. Give each required mechanism a distinct job

| Required mechanism | Role | Observable output |
| --- | --- | --- |
| Ant Colony Optimization (ACO) | Explore discrete packet paths and permitted optical route/channel combinations. | A diverse set of feasible alternatives and search cost. |
| Particle Swarm Optimization (PSO) | Search continuous per-service bandwidth allocations for the discrete alternatives. | Capacity-feasible allocation vectors and predicted QoS/cost. |
| Nash bargaining | Choose among feasible path/allocation proposals using each owner's utility and disagreement value. | An accepted agreement with positive owner gains, or an explicit no-agreement outcome. |
| Continual learning | Update domain-local QoS/disruption predictors from completed service outcomes, with replay and regression checks. | Versioned parameter changes used by subsequent ACO heuristics, PSO scoring, and utility estimates. |
| Grounded agent reasoning | Select observations, diagnose symptoms, and choose supported counteroffers or replanning steps. | Evidence-to-decision traces, not explanations alone. |

The [coupled method](agentic-system-method.md) defines the variables, interactions,
learning procedure, and required capability extension. Do not use PSO merely to
select one of eight discrete configurations, or call saving an incident in a
database continual learning. LLM weight fine-tuning is not required: the learned
objects can be explicit network-performance predictors.

## 3. Make a defensible systems novelty argument

The proposed contribution is the **specific coupling of agent reasoning,
mixed discrete/continuous optimization, owner-aware bargaining, and ongoing
learning for cross-owner packet–optical service delivery**.

Candidate contributions are:

1. A runnable agentic system in which separate owners negotiate and execute
   their own portions of an end-to-end service.
2. A precise coupled decision method: define how ACO alternatives, PSO resource
   choices, owner utilities, feedback, and learned estimates influence one another.
3. Reproducible evidence of the benefits, costs, failure cases, and interactions
   of those mechanisms under demand and network changes, including whether
   adaptive peer collaboration improves on fixed exchange.

These are hypotheses to substantiate, not established novelty. ACO has already
been studied for distributed IP/MPLS-over-optical routing/restoration, and Nash
bargaining for multi-domain optical services. See the
[targeted literature assessment](related-work-and-novelty.md). Separate ownership,
agent frameworks, or putting four known algorithms together is not by itself a
new contribution. The final paper must identify a substantive difference and
demonstrate its consequences.

Collective intelligence itself is not new. Distributed domain agents and
cross-domain negotiation with collective memory have precedents in
[EDAIR and the collective-memory work](related-work-and-novelty.md#collective-intelligence-positioning).
Claim the specific implemented mechanism and measured effects, not a first
networking "hivemind" or guaranteed emergent superiority.

**Recommendation:** pursue this integrated scope if all four mechanisms have a
specified role and a credible evaluation. It is a larger project than the prior
diagnosis-only plan. If a component brings no benefit or adds excessive overhead,
report that finding; do not redefine success to ensure every method wins.

## 4. Evaluate the full system and remove components experimentally

The [evaluation plan](experimental-validation.md#5-systems-and-baselines)
defines B0–B4. B0 is the complete system. B1 removes generative reasoning while
retaining the four mechanisms; B2 centralizes planning while preserving local
owner approval; B3 fixes observation order while retaining the same model and
four mechanisms; B4 is a competent simpler networking system.

Mandatory component studies replace ACO with conventional path search, PSO with
a constrained non-swarm allocator, Nash selection with owner-respecting greedy
selection, and continual learning with frozen predictors. Also isolate memory
retrieval from actual parameter updates. Test ACO × PSO and learning × bargaining
interactions under matched objective-evaluation budgets.

Add A8, a fixed-proposal-exchange comparator that retains all four mechanisms,
numerical fitness queries, feasibility checks, and owner consent but disables
post-proposal peer-driven replanning. E10 tests peer-informed decisions against
A8; E11 crosses adaptive feedback with continual learning. Reuse E09's matched
centralized planner and E06's frozen/memory-only controls. These additions bring
the existing [experiment catalogue](experimental-validation.md#8-experiment-catalogue)
to eleven families rather than starting a separate evaluation programme.
Trace counts alone do not prove benefit.

Use normal provisioning, competing services, heterogeneous owner preferences,
packet faults, optical unavailability, ambiguous observations, and chronological
demand/quality shifts. Measure independently verified service delivery,
allocation quality, per-owner gains, diagnosis/recovery, forgetting, adaptation
speed, unnecessary changes, and tool/model/optimization cost.

Freeze algorithms, prompts, hyperparameters, update rules, initial states, and
workload splits before confirmatory runs. In continual-learning trials the
predictor state must change according to those rules: freezing learned parameters
throughout would remove the mechanism being tested. Score each chronological
episode before using its observed outcome for an update.

## 5. Implement one complete agentic demonstration first

The current eight-configuration, single-UDP-flow testbed is the first integration
fixture, **not sufficient evidence for the complete optimization-and-learning
claim**. Required research work includes a richer resource-allocation model with
multiple service demands, meaningful continuous bandwidth decisions, diverse
discrete alternatives, and changing conditions.

1. Implement all four mechanisms in a reproducible simulator with separate owner
   agents and an independent feasibility/outcome checker.
2. Run a service sequence: ACO finds alternatives, PSO allocates resources,
   owners bargain, the system verifies outcomes, and the learner updates its
   predictors for subsequent requests.
3. Include conflicting preferences, infeasible requests, network degradation,
   and a held-out chronological change followed by recurrence of earlier conditions.
4. Demonstrate end-to-end agent control on the existing emulated UDP fixture:
   healthy delivery, packet failure, supported recovery, and honest optical failure.
5. Add and validate per-service allocation enforcement before claiming measured
   continuous allocation or competing-service benefits on the emulated network.
6. Repeat the full study with matched baselines and required ablations.

The richer simulator is required for mechanism evaluation; the current emulation
anchors service realism. Report them separately. If allocation remains simulated,
say so explicitly. Hardware experiments and LLM fine-tuning are not prerequisites.

The next deliverable is the **coupled ACO–PSO–Nash–learning specification and
evaluation fixtures**, followed by implementation in the separate testbed
environment. Documentation does not implement these capabilities.

## COMNET readiness assessment

**Assessment date:** 23 September 2026.
**Verdict:** a credible direction for a *Computer Networks* systems paper, with
enough potential research scope, but not yet enough implemented and measured
evidence to substantiate the proposed contributions. This is a project
assessment, not journal policy or an acceptance forecast.

The priority is now precision, implementation, and evidence—not adding more
algorithms or terminology. Freeze the agreed research scope while allowing the
implementation details, pilot-driven corrections, and experimental method to
be made concrete. Keep ACO, PSO, Nash bargaining, and continual learning
mandatory, with collective intelligence as the organizing hypothesis.

### Why the direction fits

COMNET has published practical LLM-assisted network management, including an
LLM/RAG agent integrated with TeraFlowSDN for intent-based network operations.
This supports topical fit; it does not establish the novelty or acceptability
of our design. See [Adanza et al., Computer Networks 272 (2025), 111647](https://doi.org/10.1016/j.comnet.2025.111647).

The substantive networking problems here are cross-owner service establishment,
allocation of scarce resources to competing demands, reconciliation of owner
objectives, cross-domain diagnosis, and adaptation to changing conditions.
Those problems—not simply the presence of AI—should drive the introduction,
method, workloads, and conclusions.

### Where the strongest value lies

The three candidate contributions in section 3 form one coherent package:

1. **A working cross-owner system:** independently controlled agents negotiate,
   act through local controllers, and verify end-to-end service delivery.
   Implementation is necessary but does not by itself establish novelty.
2. **A specific feedback-driven decision method:** define how peer evidence,
   ACO alternatives, PSO allocations, Nash gains, and learned performance
   estimates influence one another. Show what a simpler arrangement handles
   poorly and how the proposed mechanism addresses it.
3. **Evidence about when collaboration and learning help:** E10/E11 test adaptive
   peer feedback and its interaction with learning, alongside the existing
   component and centralized comparisons. Useful findings include costs,
   limitations, and conditions where collaboration is unnecessary.

A systems contribution does not require inventing a new algorithm in every
component. It does require a substantive implemented difference and reproducible
evidence explaining its consequences.

### Main reviewer risks and how to address them

**Coupling that remains only a workflow diagram.** A reviewer may ask whether
this is a new decision method or existing algorithms connected through a
workflow. Provide implementable pseudocode for search placement, candidate
exchange, feedback triggers, budget allocation, utility evaluation, predictor
updates, and stopping rules. The exact effect of a peer counteroffer or learned
estimate must be inspectable in code and decision traces.

**An unjustified PSO subproblem.** If conventional constrained optimization solves
the allocation problem more accurately or cheaply, PSO's inclusion needs an
honest accounting. Retain the required PSO implementation, but compare it with
competent constrained alternatives under matched conditions. Do not create
artificial difficulty or weaken a baseline to make PSO win. Being mandatory
in the design does not make a component's benefit predetermined.

**An inadequate testbed or generic resource problem.** Eight configurations and
one flow can demonstrate integration, not substantial search, allocation, or
adaptation advantages. Build the richer multi-service simulator and validate
per-service enforcement before claiming emulated allocation benefits. Workloads
must exercise genuine packet–optical constraints and cross-layer interactions,
not merely rename a generic allocation problem with networking labels.

**An LLM that only explains numerical decisions.** Three conditional LLM nodes
are not a weakness; selective reasoning is a defensible architecture. But their
outputs must affect evidence acquisition, diagnosis, or proposals in useful
ways. Use B1 and E07 to compare against evidence-driven non-generative rules;
fluent explanations and the number of LLM calls are not success measures.

**Overlap with close prior work.** Cross-domain negotiation and collective memory
already exist; the revised abstract of the
[collective-memory study](https://arxiv.org/abs/2509.26200v2) also describes a
Nash bargaining reference. Recent
[operator-federation work](https://arxiv.org/abs/2609.08441v1) addresses agentic
orchestration across administrative domains. These are meaningful overlaps.
Neither collective-intelligence terminology nor independent-owner agents can
carry the novelty argument alone. Compare the closest full texts and record
uncertainty where details are inaccessible.

### Submission-readiness checklist

These are internal evidence targets, not a guarantee of positive results or
Elsevier's official submission requirements. No item is marked complete by
this documentation update.

- [ ] An executable, reproducible method with concrete objectives, utilities,
  constraints, search/feedback rules, and learner updates.
- [ ] Evidence of meaningful networking value relative to competent simpler
  methods, with uncertainty, limitations, and total cost reported; any claimed
  improvement is supported by measured results rather than assumed.
- [ ] Component comparisons explain what each mechanism contributes, including
  null effects, negative results, and cases where conventional methods win.
- [ ] E10/E11 connect collaboration and learning to actual service outcomes,
  not merely message counts or changed proposals. A synergy claim additionally
  requires the prespecified interaction contrast.
- [ ] Emulated service-control evidence is clearly separated from simulation-only
  allocation findings; measured allocation claims include enforcement checks.
- [ ] A precise comparison with the closest papers identifies a substantive
  difference and the evidence for its consequences.

The [claim-to-evidence criteria](experimental-validation.md#14-claim-to-evidence-release-criteria)
map these targets to the existing experiments. Eleven experiment families provide
coverage; their number is not a contribution. A few carefully controlled findings
matter more than many shallow demonstrations. Distributed agents need not beat
centralized planning everywhere, and every component need not win on every case.

### Recommendation

Proceed with the agreed design and freeze its research scope. The strongest
potential argument remains this testable hypothesis:

> Adaptive peer feedback and outcome-based learning improve the joint path,
> allocation, and agreement decisions of independently governed network agents,
> under identifiable conditions and at a quantified cost.

Report whether, where, and to what extent the hypothesis holds. There is enough
potential value for a serious COMNET submission, but the current design and
networking foundation do not yet demonstrate that contribution. The remaining
challenge is precision and evidence, not a shortage of ideas.
