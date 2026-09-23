# Project at a glance: the system and the paper

**Target:** Elsevier *Computer Networks* (COMNET).
**Updated:** 23 September 2026.
**Status:** the networking foundation exists; the complete agent system, four
core mechanisms, and research experiments remain to be implemented and evaluated.

**Working title:** *Learning and Bargaining Agents for Cross-Owner Packet–Optical
Network Services*.

We are designing an **agentic AI networking system** in which independently
owned packet and optical networks cooperate to deliver services, negotiate
resource use, and improve their decisions from experience.

The paper's organizing idea is **collective intelligence under independent
ownership**. Its central question is:

> Can autonomous network-owner agents combine evidence, optimization, bargaining,
> and continual learning to make better end-to-end service decisions—and are
> those benefits worth the additional cost?

This is an agentic networking systems paper, not a new communication-protocol
paper. This report describes the proposed system and study, not measured results.

## 1. The problem we are solving

Consider a service crossing three networks:

```text
Customer → Alice's packet network → Bob's optical network
         → Carol's packet network → Destination
```

Packet networks forward data through routers; the optical network carries it
over fiber using light. Each network belongs to a different person or
organization, with its own resources, costs, operating policies, priorities,
and right to refuse.

Establishing a service therefore requires more than finding a technically valid
route. The system must answer:

- Which combination of paths and optical resources can carry the service?
- How much bandwidth should competing services receive?
- Is the proposed resource use acceptable to every owner?
- Does the connection actually meet the requested performance?
- What should change when conditions deteriorate?
- What can previous outcomes teach the agents about subsequent decisions?

The research problem combines technical feasibility, independent owner interests,
and changing network conditions. These are independently controlled networks,
not merely packet and optical technology layers under one operator.

## 2. What the system consists of

There is exactly one persistent **Domain Service Orchestrator (DSO)** per owner.
The DSO is the agent—not another controller sitting above a separate agent.

```text
Packet A agent ↔ Optical agent ↔ Packet B agent
      ↓               ↓               ↓
 Local tools      Local tools      Local tools
      ↓               ↓               ↓
 A's controller   O's controller   B's controller
```

Each agent has capabilities for:

- Observing local conditions and requesting evidence from peers.
- Interpreting service requests and diagnosing problems.
- Running numerical search and allocation methods.
- Evaluating its owner's benefit and negotiating proposals.
- Requesting approved actions from its own controller.
- Verifying outcomes and updating local performance predictors.

There is no central authority above the owners. An initiating agent coordinates
a request, but cannot command another owner's resources.

### Shared information, separate authority

The design assumes owners share approved topology and configuration information.
Each DSO keeps a replica; topology sharing is a full mesh, while service
negotiation involves owners along the service path. Shared topology does not
automatically provide fresh measurements, current resource availability, or
permission to act.

Each agent retains its own operational state and controller access. The proposed
software uses LangGraph workflows, PostgreSQL-backed state, Neo4j graph
projections, and pgvector-backed document retrieval. A2A supports peer
communication; MCP exposes local tools. Two MCP server types are planned:
separate packet instances for Packet A and Packet B, plus an optical instance.

These are implementation choices, not the research contribution. Full topology
sharing is an explicit disclosure assumption—not a privacy guarantee.

The architecture documents 57 workflow nodes, including three conditional
language-model reasoning nodes. Those nodes are documented responsibilities,
not implemented capabilities.

See the [system overview](system-overview.md) and
[detailed architecture](domain-agent-architecture.md).

## 3. The four mandatory mechanisms

| Mechanism | Its job in the system |
| --- | --- |
| Ant Colony Optimization (ACO) | Explore discrete packet paths and supported optical route/channel alternatives. |
| Particle Swarm Optimization (PSO) | Search continuous bandwidth allocations for competing services on those alternatives. |
| Nash bargaining | Evaluate proposals using each owner's benefit relative to its fallback, seeking an acceptable agreement. |
| Continual learning | Update performance predictors from observed outcomes so later decisions use better estimates. |

All four are mandatory in the full proposed system. Removing one creates an
experimental comparison, not an alternative definition of the complete system.

Their relationship is:

> Search generates options; bargaining evaluates owner interests; learning
> improves the estimates; agents coordinate the process.

ACO scouts and PSO particles are numerical search entities, not additional
network-owner agents.

### Where language models fit

Language-model reasoning helps agents decide which evidence to request,
interpret ambiguous symptoms, and propose supported next steps.

It does not replace the numerical algorithms. The model cannot invent
authoritative utility scores, declare an infeasible allocation valid, or
override an owner's refusal. The no-LLM comparison retains all four numerical
and learning mechanisms.

## 4. How a service request moves through the system

### Step 1: Understand the request

A request specifies endpoints and service requirements, such as bandwidth
bounds, latency or loss objectives, duration, deadline, and budget.

The receiving agent identifies the affected owners and obtains relevant evidence.

### Step 2: Explore paths with ACO

ACO generates compatible discrete alternatives across the participating networks.

Candidates must correspond to resources and actions supported by the declared
simulator or testbed. Naming an optical alternative does not create one in the
emulator.

### Step 3: Allocate bandwidth with PSO

For candidate paths, PSO searches allocations across competing services.

Allocations must respect service minimums, maximums, and shared resource
capacities. A request that cannot be supported must be refused or renegotiated,
not silently assigned less than its required minimum.

This is genuine continuous allocation, not using PSO to choose a numbered path.
The numerical search uses a declared service/owner-aware objective; the Nash
objective can guide allocation fitness as well as final selection.

### Step 4: Evaluate owner interests and bargain

Each owner evaluates a proposal against its fallback:

```text
owner gain = utility of proposal − utility of fallback
```

Utilities can account for resource use, opportunity cost, disruption, and service
value. Learned performance estimates can influence predicted costs, but cannot
rewrite the owner's preferences.

With fixed bargaining weights, the proposed Nash objective selects among feasible,
mutually positive-gain candidates:

```text
maximize sum_i w_i * log(gain_i)
subject to positive gain for every participating owner
           and all service, resource, and budget constraints
```

Every owner must still approve its contribution. If there is no acceptable
positive-gain proposal, there is no Nash agreement.

For illustration, with equal weights:

| Candidate | Gains for Packet A, Optical, Packet B | Nash product |
| --- | --- | ---: |
| X | (10, 1, 1) | 10 |
| Y | (4, 4, 3) | 48 |
| Z | (8, −1, 8) | Inadmissible |

Candidate Y is preferred among these candidates, despite X having a higher sum
of gains. Z leaves one owner worse off than its fallback. These are invented
utility values explaining the objective, not measured results or a universal
fairness guarantee. No global-optimality, truthful-reporting, or Nash-equilibrium
claim follows from this example.

### Step 5: Revise when necessary

An owner may request evidence, counteroffer, or refuse.

Feedback can trigger another PSO allocation search or different ACO alternatives.
The process has bounded observation, computation, negotiation-round, and time
budgets. The same total budget covers initial search and subsequent revisions.

If no acceptable supported plan exists, the system reports that honestly.

### Step 6: Execute locally and verify independently

Each owner applies its approved contribution through its own controller.

Success requires network evidence—such as fresh receiver measurements—not merely
successful API responses or agreement between agents.

For an operating service, the same loop supports diagnosis and supported recovery.
Healthy unchanged segments should be retained; unsupported repairs must not be
invented.

### Step 7: Learn from the outcome

After the episode is scored, local predictors can update using new observations
and bounded replay of earlier experience.

The initial proposal is to learn network-performance or change-disruption
estimates using incremental predictors. Past-only validation and regression
checks determine whether an update is promoted. Promoted versions affect later
episodes; the predictor used inside an active episode remains fixed.

This is actual parameter learning, not simply recording incidents, retrieving
previous conversations, or updating ACO pheromone. It does not require LLM
fine-tuning or cross-owner parameter averaging. Future evaluation labels must
never enter training or promotion decisions.

The full loop is:

```text
request or symptom → gather evidence → ACO paths → PSO allocations
→ owner utilities and Nash agreement → local execution → independent verification
→ predictor update → better estimates for later decisions
```

The detailed specification is in the [coupled method](agentic-system-method.md).

## 5. Where collective intelligence enters

Collective intelligence is the group-level capability being investigated,
not another algorithm.

We make it concrete through three observable relationships:

1. **Peer evidence changes a decision.** An optical observation changes a
   packet agent's diagnosis or proposal.
2. **Peer feedback changes the joint plan.** An owner's counteroffer causes
   a revised allocation or path search.
3. **Experience changes later cooperation.** A verified outcome updates a local
   predictor, whose estimates influence subsequent proposals and agreements.

For example, a packet agent may propose a technically feasible allocation that
the optical owner finds too disruptive. The optical agent explains the relevant
constraint, the agents search revised alternatives, and all owners evaluate the
new proposal. Measured disruption after execution can then inform later decisions.

This illustrates behavior in the proposed allocation-capable system, not an
existing capability of the single-flow emulator. Whether the behavior produces
better service outcomes remains an experimental question.

Record which peer inputs were actually consumed, which proposals changed,
which predictor versions were used, and what independently measured outcome
followed. Record supported decisions and concise structured reasons, not private
model chain-of-thought. Message counts and explanations alone do not demonstrate
collective benefit.

**Collective intelligence does not mean collective authority.** Owners can
cooperate while retaining different objectives and refusal rights. It requires
neither a shared LLM nor a central boss.

## 6. What we intend to contribute in the paper

The paper should present three connected contributions.

### Contribution 1: An implemented cross-owner agentic system

A runnable system that provisions and assures packet–optical services through
independently controlled owner agents, with local decisions and independently
verified outcomes.

The contribution must go beyond an architecture diagram or agents exchanging
messages.

### Contribution 2: A precisely defined coupled decision method

A reproducible method specifying how:

- ACO alternatives feed PSO allocation.
- Owner utilities influence search and Nash selection.
- Peer evidence and counteroffers trigger revisions.
- Verified outcomes update predictors.
- Updated predictions influence later collective decisions.

This coupling is the strongest candidate methodological contribution.

### Contribution 3: Evidence about benefits, costs, and limitations

Experiments must establish where the system helps, which mechanisms contribute,
whether interactions matter, and when simpler methods are preferable.

Collective intelligence provides the organizing question; measured networking
outcomes provide the evidence. Benefits, novelty, and journal acceptance are not
established by the design.

### What we cannot claim as novelty by itself

There are already precedents for:

- Per-domain intelligent agents: [EDAIR](https://ieeexplore.ieee.org/document/11073742/).
- ACO-based packet–optical routing and restoration: [the COMNET study](https://doi.org/10.1016/j.comnet.2020.107747).
- Cross-domain negotiation and collective memory, with a Nash bargaining reference
  in the revised abstract: [Chergui et al.](https://arxiv.org/abs/2509.26200v2).
- Agentic orchestration across federated operator domains:
  [Carballo González et al.](https://arxiv.org/abs/2609.08441v1).

Consequently, “agents + swarm methods + bargaining + learning” is insufficient as
a novelty claim. We must distinguish the actual mechanism and demonstrate its
consequences. We should not claim the first networking “hivemind.”

The [literature assessment](related-work-and-novelty.md) records access limits
and evidence levels; these brief comparisons do not establish that prior work
lacks a particular feature. The [paper plan](paper-positioning.md) defines the
candidate contribution and its evidence requirements.

### COMNET readiness assessment

The current assessment is **a credible COMNET research direction, but not yet a
demonstrated journal contribution**. The scope already contains enough potential
value. The next priority is to make the method precise, implement it, and gather
convincing evidence—not add more algorithms or terminology.

COMNET has published practical LLM/RAG-assisted network management with
TeraFlowSDN, supporting topical fit without guaranteeing novelty or acceptance.
See [Adanza et al.](https://doi.org/10.1016/j.comnet.2025.111647).

The main reviewer risks are:

- Coupling described only by a diagram, without implementable search placement,
  feedback, budget, utility, and learning rules.
- PSO adding cost without useful benefit over conventional constrained allocation.
- An eight-choice, single-flow fixture standing in for meaningful multi-service
  evaluation, or workloads lacking genuine packet–optical interactions.
- LLM calls producing explanations without improving actual decisions. Having
  only three conditional LLM nodes is not itself a weakness.
- Close prior work already covering domain agents, negotiation, collective
  memory, and operator federation.

Submission readiness requires a reproducible implementation, demonstrated
networking value at reported cost, component and interaction comparisons,
E10/E11 service-outcome evidence, clearly separated simulation/emulation findings,
and precise distinctions from the closest papers. Negative results must remain
visible. Eleven experiment families are coverage, not eleven contributions.

**Recommendation: freeze the agreed research scope and proceed to implementation
and validation.** All four mechanisms remain mandatory, but their superiority
is not predetermined; distributed agents need not always beat centralized
planning. The [full readiness assessment and checklist](paper-positioning.md#comnet-readiness-assessment)
records the risks and evidence targets. These are project criteria, not official
journal rules or an acceptance forecast.

## 7. What experiments we will conduct

The plan contains eleven experiment families.

| Experiment | What it establishes |
| --- | --- |
| E01 — Owner boundaries | Agents can act only through their own authorized resources and approvals. |
| E02 — Complete service loop | Request, planning, agreement, execution, verification, and supported recovery work together. |
| E03 — ACO search | Whether ACO offers useful candidate quality relative to conventional search and its cost. |
| E04 — PSO allocation | Whether PSO offers useful allocations compared with competent constrained alternatives. |
| E05 — Nash bargaining | How bargaining affects owner gains, agreements, refusals, and service outcomes. |
| E06 — Continual learning | Whether predictors adapt, improve later decisions, and retain performance when earlier conditions recur. |
| E07 — Agent reasoning | Whether adaptive evidence gathering and diagnosis improve verified outcomes. |
| E08 — Coupling | Whether component interactions matter and whether the full system earns its complexity. |
| E09 — Planning placement | How distributed agents compare with matched centralized planning. |
| E10 — Collective decisions | Whether adaptive peer feedback improves on fixed proposal exchange. |
| E11 — Collective adaptation | Whether continual learning and adaptive peer feedback reinforce each other. |

### E10: adaptive collaboration versus fixed proposal exchange

E10 compares the full system with **A8, the fixed-exchange control**.

A8 retains ACO, PSO, Nash bargaining, learning between episodes, numerical
fitness queries, and owner consent. However, its submitted path/allocation
candidate pool is fixed: post-submission counteroffers cannot trigger new
candidates. Current feasibility and freshness checks still apply. Unsafe
candidates must be invalidated, not executed to make the control look worse.

A8 may spend its search budget on initial proposals; the full system divides
the same total budget between initial search and revisions. A counteroffer
cannot be relabeled as a new episode to evade the fixed-pool restriction.

E10 includes both:

- **Equal-information decision replay:** planners receive the same pre-action
  evidence snapshot and comparable numerical query access, so one does not win
  simply because it was given more facts.
- **Closed-loop trials:** match initial conditions, evidence opportunities,
  exogenous workloads, and total budgets; measure actual service outcomes.

It includes cases where collaboration is unnecessary, redundant, or cannot
produce an agreement. Different actions can produce different subsequent
telemetry, so closed-loop observations need not remain identical.

### E11: learning and feedback together

E11 uses four conditions:

| | Continual predictors | Frozen predictors |
| --- | --- | --- |
| Adaptive peer feedback | Full system, B0 | Learning disabled, A4 |
| Fixed proposal exchange | A8 | A8 + A4 |

All four conditions retain ACO, PSO, Nash bargaining, ordinary optimizer updates,
and owner approval. The comparison separates the benefit of learning from its
interaction with feedback. An improvement from learning alone is not
automatically evidence of synergy.

Run chronological streams with stationary conditions, a demand/quality shift,
and recurrence of an earlier regime. Score before updating, repeat independently
reset streams, and measure both service effects and retention. Reuse the
memory-only comparison to distinguish learning from retrieval.

### Other comparisons

| Baseline | Purpose |
| --- | --- |
| B0 — Full system | All four mechanisms and grounded agent reasoning. |
| B1 — No generative reasoning | Replace LLM calls with documented rules/templates while retaining all four mechanisms. |
| B2 — Centralized planning | Keep comparable information, mechanisms, total budgets, and local owner approval; change planning placement. |
| B3 — Fixed diagnostic observation order | Test adaptive evidence selection while retaining reasoning and the four mechanisms. |
| B4 — Simpler conventional system | Test whether the integrated complexity is worthwhile against competent conventional methods. |

Component studies replace ACO, PSO, Nash selection, and continual learning
individually, and test memory-only retrieval, reasoning nodes, retrieval choices,
and fixed proposal exchange. Required interaction studies cover ACO × PSO,
learning × Nash, and adaptive feedback × learning.

If Nash guides PSO fitness, the full no-Nash comparison must replace that fitness
as well as the final selector. Otherwise Nash still influences the supposedly
no-Nash condition.

A distributed win over fixed exchange does not imply a win over centralized
planning. Report conventional methods winning, null effects, and regressions.

### Measurements and experimental discipline

Measure:

- Independently verified delivery, allocated/delivered bandwidth, and feasibility.
- Per-owner gains, agreement frequency, refusals, and unresolved requests.
- Diagnosis, recovery, service-level violations, and unnecessary changes.
- Prediction error, adaptation, retention, and forgetting.
- Total model, tool, numerical search, training, and communication cost.

Correct refusal is distinct from successful delivery. Failed and unresolved
cases remain in the results. Gains conditional on agreement must not hide low
agreement rates.

Use matched budgets, declared stopping rules, independent outcome checks, and
uncertainty estimates. Correlated episodes within one adaptive stream are not
independent replicates; repeat whole streams. Decision traces help explain
mechanisms but are not causal proof by themselves.

The [experiment plan](experimental-validation.md) is the authoritative source
for definitions, workloads, statistical design, artifacts, and claim criteria.
All experiments described here are planned, not executed results.

## 8. What already exists—and what still needs building

The repository implements the networking foundation:

- Eight SR Linux routers across two packet domains.
- A four-ROADM Mininet-Optical line.
- Primary/backup packet choices and two selectable optical wavelengths, carried
  one at a time.
- Eight joint configurations and a reference UDP flow.
- Packet and optical control/observation tooling.

The complete agents, numerical mechanisms, learning loop, and
collective-intelligence evaluation are still planned. Existing domain-scoped
tooling does not by itself establish fully independent owner credentials and
authorization.

The current fixture has important limits:

- It does not enforce per-service bandwidth allocations. Offered sender load
  is not a bandwidth reservation.
- Its single-flow workload cannot demonstrate meaningful competition between
  services.
- Both optical wavelengths use the same fiber route; retuning cannot repair
  a fiber cut.
- Eight configurations are insufficient evidence for broad search advantages.
- Relevant control, telemetry, and measurement issues must be resolved before
  treating autonomous outcomes as research evidence.

The study therefore needs complementary environments:

| Profile | Purpose and status |
| --- | --- |
| P0 — Richer simulator | Required, still to build: multiple competing services, meaningful bandwidth choices, larger candidate sets, chronological changes, and independent outcome checks. |
| P1 — Existing emulator | Implemented networking foundation; agent integration still to build. Tests supported service control, packet recovery, and independent delivery evidence. |
| P1-A — Allocation-capable emulation | Add service identification, shaping/scheduling, capacity accounting, and measurements before claiming emulated allocation benefits. |
| P2 — Hardware | Additional evidence, not a prerequisite for the agreed study. |

Simulation findings must remain clearly distinguished from measured network
results. If allocation is only simulated, report it as simulation.

See the [data-plane specification](data-plane.md) and
[known-issues register](known-issues.md).

## 9. What we do next, and how the manuscript comes together

The next implementation work is to:

1. Finalize owner utilities, disagreement values, numerical parameters, learner
   features, and feedback stopping rules.
2. Specify precisely where search runs and how agents assemble and evaluate
   joint candidates.
3. Build the coupled simulator and competent comparisons together.
4. Integrate owner agents with the networking foundation and resolve relevant
   measurement/control issues.
5. Add and validate allocation enforcement before claiming measured allocation
   on the emulator.
6. Run the eleven experiment families and write conclusions supported by those
   results.

The manuscript can follow this structure:

1. Problem, motivation, and collective-intelligence research question.
2. Related work and precise distinctions.
3. Cross-owner agentic system architecture.
4. Coupled optimization, bargaining, feedback, and learning method.
5. Implementation, testbed profiles, and experimental design.
6. Results: service outcomes, owner trade-offs, component value, collaboration,
   adaptation, and total cost.
7. Limitations, threats to validity, and conclusions.

The study does not establish topology privacy, truthful strategic reporting,
production high availability, universal scalability, or arbitrary device
control. Synthetic independent owners are not evidence of commercial deployment.
Communication interfaces and execution safeguards support the system; they are
not the paper's research focus.

The [implementation roadmap](implementation-roadmap.md) sequences the work.
The updated thesis is:

> We investigate how independently governed network agents develop useful
> collective decision-making through evidence exchange, coupled optimization,
> bargaining, and continual learning—and quantify the resulting service benefits,
> owner trade-offs, and costs.

The next milestone is an executable, testable system—not another algorithm added
to the list.
