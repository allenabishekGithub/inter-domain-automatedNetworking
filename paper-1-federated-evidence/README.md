# Paper 1 — Recovery under limited disclosure and stale evidence

**Status:** proposed research; algorithm and evaluation not implemented.

**Target:** IEEE Transactions on Network and Service Management (TNSM), subject
to contribution strength and verification of the required Q1 ranking edition.

**Working title:** *Recovery Under Limited Disclosure and Stale Evidence in
Multi-Domain Networks*.

**Decision:** recommended first paper, with a small comparative pilot before
building the complete controller stack.

## The problem

A service crosses Packet A, Optical, and Packet B. Each owner has partial
observations, disclosure restrictions, and its own authority. Measurements may
arrive late or refer to different traffic cohorts and configurations.

The proposed controller chooses **which evidence to request, when to collect
compatible groups, and when that evidence supports a permitted recovery action**.
It must account for collection and execution delay, refuse unsupported changes,
and measure the cost of continued impairment when it waits or escalates.

For example, two boundary counters can help localize loss only when their flow,
packet cohort, counter semantics, and relevant configuration revisions are
compatible. Recent timestamps alone do not establish this. A useful collection
plan should avoid acquiring one reading so early that it becomes unsuitable
before the other reading and required approvals arrive.

## Candidate contribution and novelty boundary

The [proposal](tnsm-proposal.md) develops three candidate contributions:

1. A problem formulation connecting evidence collection, owner disclosure
   constraints, changing state, and evidence needed at execution time.
2. An online method for selecting and scheduling complementary evidence groups
   and deciding when to recover, recollect, or escalate.
3. A reproducible evaluation against strong diagnosis methods under identical
   execution checks, with recovery, disclosure, and collection-waste outcomes.

These are research targets. The [literature review](state-of-the-art.md) finds
precedents for feature/label separation, cross-domain diagnosis, action-based
testing, and decision-region identification. Agents, maps, freshness checks, or
stopping when an action is known do not independently establish novelty.

The pilot must test whether anticipating joint evidence validity offers an
advantage beyond a fixed matched-counter bundle and EC2/HEC-style adaptive
diagnosis with the same validity checks. If it does not, narrow or change the
contribution before investing in the full system.

## Evaluation

| Experiment | Purpose |
| --- | --- |
| E1 — Platform and measurement validity | Validate counters, receiver freshness, authority, and recovery execution |
| E2 — Recovery versus disclosure | Compare methods over disclosure budgets and incident types |
| E3 — Delays and state changes | Test compatible-group scheduling, expiration, and recollection; include a stationary control |
| E4 — Missing evidence and model error | Test refusals, timeouts, uncertainty, missed repairs, and escalation cost |
| E5 — Generalization and scale | Hold out regimes and vary domain count, evidence sources, and action space |

Primary outcomes are cumulative service impairment over a fixed incident
horizon and time to verified recovery. Also report disclosure, harmful actions,
repair coverage, missed repairs, expired evidence, and repeated requests.
Prediction error is optional diagnostic evidence, not the paper's headline.

Comparators include local-only, fixed matched evidence, full permitted sharing,
information-gain/value-of-information acquisition, EC2/HEC-style decision-region
methods, and periodic refresh with adaptive diagnosis. All use the same
authority, evidence-validity, and execution checks. Details and hypotheses are
in the [plan](plan.md).

## Build sequence

| Phase | Deliverable |
| --- | --- |
| 0 | Measurement definitions and live-platform prerequisites |
| 1 | Offline harness, action-effect model, proposed algorithm, and strong pilot comparisons |
| 2 | One controller and scoped MCP access, after the pilot decision |
| 3 | Three controllers, peer evidence exchange, approvals, and live recovery |
| 4 | Expanded evaluation, scaling, and reproducible results |

Start the offline pilot while resolving F2/F3/F4/F6 for live experiments. An
offline result does not establish live service recovery. The
[full build plan](plan.md#8-build-phases) sets phase exit criteria.

Paper 1 uses deterministic decisions. An action-effect model may be fitted from
controlled training interventions, with evaluation cases held out. Hidden fault
injections are evaluator-only data. LLM reasoning, retrieval ablations, and
continuous rate-control stability belong to Papers 3 and 2 respectively.

## Documents in this folder

| File | Role |
| --- | --- |
| [tnsm-proposal.md](tnsm-proposal.md) | Recommended contribution, method, novelty limits, venue fit, and go/no-go criteria |
| [state-of-the-art.md](state-of-the-art.md) | Prior-work assessment and primary-source references |
| [plan.md](plan.md) | Hypotheses, baselines, experiments, metrics, phases, and release criteria |
| [design.md](design.md) | Shared proposed architecture and evidence collection integration |

The design remains canonical for the base system inherited by Papers 2 and 3.
Its 25-node episode workflow is a proposed implementation starting point, not a
novelty claim or completed runtime. Record the final graph and schema version
before comparing paper extensions.

## Working here

- Shared implementation belongs at the repository root.
- `experiments/` holds this paper's run configurations and condition schedules.
- `results/` holds run bundles and analysis, with simulated and live results
  identified separately.
- The earlier C1/C2/C4/C6/C7/C8 claim set is superseded by this direction and the
  plan's H1–H3 hypotheses. Old claim IDs remain only in historical assessments.
