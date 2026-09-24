# Paper 3 — Grounded agent reasoning for multi-domain network operations

**Status:** not started. Blocked on Paper 1's system.
**Target:** IEEE TNSM, or an agent/AI venue where the ground-truth angle lands harder.
**Depends on:** [Paper 1](../paper-1-federated-evidence) — Phases 0–4 complete.

> **Base-system update, 24 September 2026:** Paper 1 now targets
> [recovery under limited disclosure and stale evidence](../paper-1-federated-evidence/tnsm-proposal.md)
> with deterministic evidence scheduling. That adaptive method is a required
> comparator and fallback here. Hold acquisition policy constant when isolating
> reasoning value; evaluate any LLM change to acquisition separately.
> Freeze the inherited graph/schema version before comparison. The claims below
> remain proposals and need their own literature and empirical validation.


---

## The problem

Agentic AI evaluation is mostly LLM-judged, human-rated, or benchmark-gamed.
Everyone knows it, and reviewers are tired of it.

This system offers something rare: **an external referent for both halves of the
question.** Decision quality is measured against packets that arrived or did
not. Faithfulness is measured against records that resolve or do not. Neither is
a matter of opinion.

The paper asks three things:

1. Does retrieval-grounded reasoning make better network decisions than rules?
2. Is the reasoning **faithful**, and does gating it keep it so?
3. Which of fourteen reasoning nodes actually earn their tokens?

The third is the question the field mostly avoids.

## Claims

| # | Claim | Evidence |
| --- | --- | --- |
| **C5** | Reasoning is faithful because it is **gated**, not because it is trusted | Ungrounded-assertion rate with the gate off; firing and fallback rate with it on |
| **C3** | Agents that reason about what to share approach full-disclosure quality at materially lower disclosure | S3 versus Paper 1's adaptive scheduler, S1, and S2: recovery/risk/coverage within declared margins at lower disclosure |
| — | Per-node reasoning value | Fourteen single-node ablations: which nodes carry the benefit, and which could be rules |

**Honest risk, stated up front.** C3 is the most likely null result in the whole
programme: with eight configurations and a modest episode count, a good static
disclosure rule may tie or beat a reasoned one. Report it either way. **Do not
build the paper's spine on C3** — build it on C5 and the per-node ablation,
where a negative result is still a contribution.

## What it needs built

Everything Paper 1 builds, plus **Phase 5**:

| Component | Detail |
| --- | --- |
| Reasoning engine | At its fourteen nodes ([design §2](design.md#2-where-reasoning-sits)) |
| Typed judgment contract | `decision`, `rationale`, `citations[]`, `confidence` |
| Grounding gate | Citation resolution and direction checking; fallback on failure |
| Retrieval modes | R0 none, R1 flat vector, R2 graph only, R3 GraphRAG |
| Tool-selection surface | `plan_observations` chooses among **read-only** MCP tools within a declared budget; named actions are never shown to the engine ([design §6](design.md#6-mcp-tools-the-engine-may-select)) |
| S3 disclosure decision | What to disclose, what to request, what a disclosure licenses |

## Architecture

| Section | Why it matters here |
| --- | --- |
| [Paper 1 §7.6](../paper-1-federated-evidence/design.md#76-the-langgraph-node-set) | The node taxonomy: 14 reasoning, 6 gates, 5 effectors — and why the gates can never be a model call |
| [§2–§4](design.md#2-where-reasoning-sits) | The reasoning engine: what it decides, the contract, the grounding gate, the boundaries |
| [Paper 1 §8](../paper-1-federated-evidence/design.md#8-the-simap) | The SIMAP and the four traversal directions that ground retrieval |
| [§5](design.md#5-retrieval) | Retrieval modes, and what each decision point retrieves |
| [§8](design.md#8-injection-boundary) | Peer content is data, never instruction — the injection boundary |

This paper's [`design.md`](design.md) specifies **what changes inside each of
the fourteen reasoning nodes** relative to Paper 1's rules (§2.2) and the
**`reasoning_call` table** that makes the per-node ablation analysable (§5.2).

**The graph topology is unchanged** — same two graphs, same 25 nodes. Rules and
engine execute the identical graph, so any measured difference is attributable
to the reasoning rather than to a different control flow.

**The line this paper defends:** *it may reason, but it may not assert.* Every
load-bearing claim cites a live observation or a held record; failures go to the
deterministic fallback and are journalled as ungrounded, never silently retried.
That is what makes an LLM admissible in a network control path.

## Experiments

| | Experiment | Establishes |
| --- | --- | --- |
| **E5** | Grounding gate on vs off, including deliberately ambiguous evidence where a plausible-but-wrong story is available | C5 |
| **Retrieval ablation** | R0 / R1 / R2 / R3 on the same decisions, scored on decision quality **and retrieved-context precision** — how much of what was retrieved was actually cited | Q2 |
| **Per-node ablation** | Disable the engine at one reasoning node at a time; the other thirteen keep reasoning. Fourteen runs | Per-node value |
| **Disclosure comparison** | S3 against Paper 1's deterministic adaptive scheduler, a good static rule, and full permitted sharing | C3 |

**Expected shape of the per-node result:** a few nodes carry most of the
benefit — likely `diagnose`, `plan_observations`, `select_candidate` — and
several could be rules. **Saying which is more useful than "LLM agents work."**

The retrieval modes are expected to separate mainly on diagnosis rather than
provisioning, since provisioning has only eight candidates to choose among.

## Reproducibility

Stricter here than elsewhere. Pin the model id and version, temperature,
retrieval budgets, embedding model and seeds. Archive **every prompt and every
response, tagged with the node that issued it**, in the run bundle.

A mid-study model change invalidates every prior run. Choose once and do not
move.

## Documents in this folder

| File | Contents |
| --- | --- |
| [`design.md`](design.md) | System architecture as this paper builds and uses it |
| [`plan.md`](plan.md) | Claims, experiments, baselines, metrics, build phases, threats |

The [Paper 1 design](../paper-1-federated-evidence/design.md) is **canonical for
the shared system**. This folder's [`design.md`](design.md) is authoritative for
Paper 3's additions; inherited behavior follows Paper 1. This folder's
[`plan.md`](plan.md) defines the reasoning and retrieval evaluations.

## Working here

- **Code is shared**, at the repository root. Phase 5 components go into the
  shared `agent/` tree, not into this folder.
- `experiments/` — retrieval-mode grids, ablation matrices, prompt sets.
- `results/` — run bundles, prompt/response archives, analysis.
