# Paper 1 — Federated outcome evidence and service attribution

**Status:** not started. Recommended first paper.
**Target:** IEEE TNSM. Conference version first at CNSM or NOMS.
**Depends on:** nothing. This paper *is* the base system.

---

## The problem

A service crosses three separately owned networks. **The party that can measure
the outcome is not the party that chose the configuration.**

| Agent | Holds features | Holds labels |
| --- | --- | --- |
| `agent-packet-a` | its action, discards, utilisation | **no** |
| `agent-optical` | its channel, gOSNR, margins | **no** |
| `agent-packet-b` | its action, discards | **yes** — delivered ratio, loss, jitter |

Packet B holds every label and only some features. Packet A and Optical hold
features and no label at all. Neither side can build a good predictor alone,
and the split follows from **who owns the receiver** — not from how a dataset
was partitioned. Standard federated learning does not address this regime.

The paper asks what sharing outcomes across that boundary buys, what it costs in
disclosure, and whether agents can attribute degradation to the owner who caused
it.

## Claims

| # | Claim | Evidence |
| --- | --- | --- |
| **C1** | Without sharing, two of three owners cannot learn the outcome **at all** | S0 runs: flat predictor error for Packet A and Optical across the whole sequence |
| **C2** | Sharing measurably improves each owner's predictions and decisions | S0 vs S1: per-agent prediction error, decision regret, episodes to stable choice |
| **C4** | The benefit is largest exactly where local telemetry is blind | Locally-invisible vs locally-visible impairment: the S0→S1 gap should widen |
| **C6** | Some faults are detectable **only** by combining telemetry across the boundary | Attachment-segment loss localised by cross-owner counter differencing |
| **C7** | Agents can attribute degradation to the owning segment, and the method available depends on what peers disclose | Attribution accuracy per method against the injected ground-truth segment |
| **C8** | Attribution produces correct action **and correct non-action** | Owning domain acts; non-owning domains refrain; disruption avoided |

C2 and C4 are the contribution. C1 establishes the floor is structural rather
than imposed. C7–C8 are what the shared evidence is *for*. C6 is the cheapest
striking result in the set.

## What it needs built

Build phases **0–4** of the [shared plan](plan.md#8-build-phases). No
capability beyond them.

| Phase | Delivers |
| --- | --- |
| 0 | F4 closed; lab runs end to end; first real run bundle |
| 1 | Condition harness (netem, three visibility classes); segment counters; **premise checks 1–3** |
| 2 | `packet-a-mcp` and one agent |
| 3 | Three agents over A2A |
| 4 | RLS predictors, `OUTCOME` publication, S0–S3 switches |

## Architecture

The full system design is [`design.md`](design.md). The sections
this paper leans on hardest:

| Section | Why it matters here |
| --- | --- |
| [§2](design.md#2-the-premise-ownership-splits-observation) | The observation asymmetry — the paper's premise |
| [§5](design.md#5-conditions-what-makes-this-a-learning-problem) | Conditions and the three visibility classes, including the modelled-only trap |
| [§11](design.md#11-learning-and-sharing) | Features/labels split, the RLS predictor, what sharing changes |
| [§10](design.md#10-attribution) | Four-segment decomposition, three attribution methods, the action rule |
| [§8](design.md#8-the-simap) | The SIMAP, and why a shared map is the precondition for peer evidence meaning anything |

This paper's own [`design.md`](design.md) additionally specifies the **25-node
LangGraph set** scoped to P1 (§7.6, with each of the 14 reasoning nodes'
deterministic rule) and the **`context.db` schema** (§8.1).

This is the **base graph** — two graphs, 25 nodes, 14 reasoning / 6 gates / 5
effectors. Paper 2 adds a third graph and seven more nodes; Paper 3 keeps this
topology exactly.

**This paper does not need:** continuous loops or rate adaptation
([Paper 2 design](../paper-2-compensation/design.md)), or evaluation of the
reasoning layer ([Paper 3 plan](../paper-3-grounded-reasoning/plan.md)).

**Open decision — settle before Phase 4 ends.** Whether this paper runs the
reasoning engine at all. Deterministic agents drop Phase 5, are three to four
months cheaper and far more reproducible, but invite *"why is this agentic?"*.
See the [programme overview](../README.md#three-papers--choose-one).

## Experiments

| | Experiment | Establishes |
| --- | --- | --- |
| **E1** | Platform: healthy provisioning and correct refusal | Precondition, not a result |
| **E2** | Sharing conditions S0/S1/S2/S3 over the full schedule | C1, C2 |
| **E3** | Visibility classes: S0 vs S1 under locally-visible and locally-invisible impairment | C4 |
| **E3b** | Joint detection: attachment-segment loss by counter differencing | C6 |
| **E3c** | Attribution and action: inject into a known segment, score all four behaviours | C7, C8 |
| **E4** | Drift and recurrence: abrupt shift then return to an earlier regime | C2 |

**Headline figure:** per-agent prediction error over episodes, four sharing
conditions, with Packet A and Optical plotted separately from Packet B. **S0
should be a flat line for two of the three agents.** If it is not, the premise
is wrong.

Baselines: P0 (EWMA predictor), P1 (no learning), P3 (oracle). Full definitions
in [plan §6](plan.md#6-baselines-and-ablations).

## Next action

**Phase 0.** Close F4, run `sudo scripts/service-up.sh` end to end, capture a
run bundle. Never yet done, and everything here assumes it works.

Then Phase 1's premise checks — any of which can kill a claim cheaply.

## Documents in this folder

| File | Contents |
| --- | --- |
| [`design.md`](design.md) | System architecture as this paper builds and uses it |
| [`plan.md`](plan.md) | Claims, experiments, baselines, metrics, build phases, threats |

This folder's [`design.md`](design.md) is **canonical for the shared system**.
Papers 2 and 3 inherit that base and define their additions in their own design
documents. This folder's [`plan.md`](plan.md) defines the base build phases and
validation programme.

## Working here

- **Code is shared**, at the repository root. Do not fork the agent, MCP servers
  or data plane into this folder.
- `experiments/` — this paper's run configurations and condition schedules.
- `results/` — run bundles and analysis.
