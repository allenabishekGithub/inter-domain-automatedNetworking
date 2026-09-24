# Paper 3 — System design

**Scope:** what Paper 3 adds to Paper 1's system.
**Canonical sources:** [`docs/design.md`](../docs/design.md) for the shared
system; [`paper-1/design.md`](../paper-1-federated-evidence/design.md) for the
base. This document is authoritative for Paper 3's additions.

---

## 0. At a glance

| | |
| --- | --- |
| Adds to Paper 1 | The reasoning engine behind **14 of 25 nodes**; `grounding_gate` becomes load-bearing |
| Graph topology | **Unchanged.** Paper 1 builds every node; this paper changes what runs inside the `R` ones |
| New table | `reasoning_call` — prompt, response, retrieved vs cited, tokens, latency, per node |
| Claims | **C5** faithfulness, **C3** reasoned disclosure, plus per-node value |
| Calls per episode | **≈28** across the federation, ~40 at the three-round cap (§2.3) |

**The line this paper defends:** *it may reason, but it may not assert.*

---

## 1. What is inherited, unchanged

| Inherited | Summary |
| --- | --- |
| Three agents over A2A | Agent Cards, task per peer, six exchanges, three-round cap |
| The three gates | `feasibility`, `policy`, `agreement` — deterministic, never a model call |
| SIMAP | Two-layer service–infrastructure map, federated by signed slices |
| Context store | SQLite + `sqlite-vec`; NetworkX projection from the records |
| Segment attribution | Four-segment exact decomposition |
| RLS predictors, S0–S3 | Learning stays deterministic arithmetic |
| MCP servers | Credentials held there, tool schema is the allowlist |

Paper 3 adds the **reasoning layer** that sits between the evidence and the
gates.

---

## 2. Where reasoning sits

Each agent is two LangGraphs over **25 nodes** in three kinds. The kind is not
negotiable:

| Kind | Count | LLM | Why |
| --- | ---: | --- | --- |
| **Reasoning** | 14 | yes | Judgment under incomplete evidence |
| **Gate** | 6 | **never** | An LLM cannot check its own grounding, and unanimity is a byte comparison |
| **Effector** | 5 | **never** | Sending a message or invoking a named action |

### 2.1 The fourteen reasoning nodes

| Job | Nodes | Question |
| --- | --- | --- |
| **Frame** | `triage_request`, `intake_intent`, `a2a_discover` | What is being asked, by whom, of which domains? |
| **Look** | `plan_observations`, `formulate_queries` | What is worth observing and retrieving for *this* question? |
| **Judge** | `evaluate_local_actions`, `evaluate_proposal`, `select_candidate`, `assemble_candidates`, `diagnose`, `verify_local` | What do these facts mean, and what should this owner do? |
| **Say** | `a2a_dialogue`, `compose_outcome`, `close_episode` | What to tell peers and operators, and how to justify it |

**The Look group matters more than it appears.** An agent that decides what to
measure and what to retrieve — rather than receiving a fixed evidence bundle —
is the difference between an agent and a pipeline, and its cost is directly
measurable.

**`select_candidate` is deliberately a reasoning node.** Its deterministic rule
(lowest cost, predicted ratio, candidate index) is both its fallback **and its
comparator**: divergence from the rule is journalled and is itself a result.

---

### 2.2 What Paper 3 changes about the graph

**The graph topology is unchanged.** Paper 1 builds every node; Paper 3 replaces
what runs *inside* the fourteen `R` nodes and adds one gate to the path after
each.

| Node | Paper 1 (rule) | Paper 3 (engine) |
| --- | --- | --- |
| `triage_request` | schema + endpoint-in-my-domain check | judge coherence, remit, and whether to decline early |
| `plan_observations` | fixed set: oper-states + segment counters | choose what is worth measuring for *this* question, within budget |
| `formulate_queries` | fixed down-traversal from the service | choose what to traverse and what to search for |
| `evaluate_local_actions` | all gate-passing actions, cost-ordered | characterise each contribution and its caveats |
| `evaluate_proposal` | accept iff gates pass and predicted ≥ objective | accept, refuse or counter, with grounds |
| `select_candidate` | lowest cost → predicted ratio → index | choose with justification; **divergence from the rule is a result** |
| `assemble_candidates` | union of accepted actions, structured fields | interpret peers' `OPTIONS` including prose caveats |
| `a2a_discover` | all peers on the service path | reason about which peers and skills the intent needs |
| `intake_intent` | structured intent accepted as given | resolve endpoints via the SIMAP; normalise |
| `diagnose` | segment decomposition, strongest method | probable cause, blast radius, next discriminating observation |
| `verify_local` | exact compare; `partial` on mismatch | judge whether the readback matches intent when ambiguous |
| `compose_outcome` | fixed field set per condition | decide which fields a peer needs and which are sensitive |
| `close_episode` | templated reason string | an explanation an operator can read |

**`grounding_gate` becomes load-bearing.** In Paper 1 it is a no-op — a rule
node makes no claims to check. In Paper 3 every `R` node routes through it, and
its firing rate is a headline metric.

**The four gates never change kind.** `feasibility_gate`, `policy_gate`,
`agreement_gate` and `cost_and_predict` remain arithmetic and comparison in
every paper, and `update_predictor` stays deterministic RLS. **Paper 3 changes
judgment, never measurement or enforcement.**

### 2.3 How many nodes actually contact the LLM

Fourteen nodes are **LLM-capable**. Far fewer fire in any given episode, and the
operational number is calls *per episode*, not nodes in the catalogue.

**Participant episode, healthy path, one negotiation round:**

| Fires | Node |
| --- | --- |
| 1 | `triage_request` |
| 2 | `plan_observations` |
| 3 | `formulate_queries` |
| 4 | `evaluate_local_actions` |
| 5 | `a2a_dialogue` — compose `OPTIONS` |
| 6 | `evaluate_proposal` |
| 7 | `a2a_dialogue` — compose the answer |
| 8 | `verify_local` |
| 9 | `compose_outcome` |
| 10 | `close_episode` |

**≈10 calls.** `diagnose` does not fire — it is on the fault path only. Each
extra negotiation round adds two (`evaluate_proposal` + `a2a_dialogue`), so a
three-round episode reaches **≈14**.

**Initiator episode:** `a2a_discover`, `intake_intent`, `assemble_candidates`,
`select_candidate`, `a2a_dialogue`, `verify_local`, `compose_outcome`,
`close_episode` — **≈8**, plus two per extra round.

**Per episode across the federation:** ≈ 8 + 2 × 10 = **≈28 calls**, rising to
**≈40** at the three-round cap. On a fault path add `diagnose` per agent.

These counts are per-episode budgets to pin and report, and the
`reasoning_call` table (§5.2) records each one with its node, tokens and
latency so the figures come from the runs rather than from this estimate.

---

## 3. The reasoning contract

The engine receives a **question**, the **deterministic facts** for that decision
(gate results, costs, predictions, live observations), and the **retrieved
context**. It returns:

```json
{
  "decision": "REFUSE",
  "rationale": "Moving to the backup core would carry the service over p-b2,
                which three previous episodes show delivering below the 0.98
                objective whenever the optical line is on channel 1.",
  "citations": ["episode:ep-0098", "episode:ep-0111", "episode:ep-0127",
                "simap:link/p-b2:ethernet-1/2", "observation:obs-5521"],
  "confidence": 0.74,
  "alternative": "C4"
}
```

---

## 4. The grounding gate

Every load-bearing claim in `rationale` must cite a **live observation** or a
**held record**. The gate:

1. Parses the citations.
2. Checks each resolves to a record this agent actually holds.
3. Checks the cited record supports the claim's **direction**.

A failure is **rejected, journalled as ungrounded, and replaced by the
deterministic fallback**. The rate at which this happens is a reported metric,
never a hidden retry.

> **It may reason, but it may not assert.**

That is what makes an LLM admissible in a network control path, and it is the
paper's central design claim.

### 4.1 What the gates guarantee

Whatever the fourteen reasoning nodes conclude, no episode reaches an adapter
without passing `feasibility_gate` on live observation, `policy_gate` on
declared rules and `agreement_gate` on unanimity — and no rationale reaches a
peer without passing `grounding_gate`. **The safety argument is four nodes
wide.**

---

## 5. Retrieval

Four modes, and the ablation compares them directly:

| Mode | Context supplied |
| --- | --- |
| **R0** | Live facts only, no retrieval |
| **R1** | Flat vector RAG over episodes, incidents, policy |
| **R2** | Graph retrieval over the SIMAP only |
| **R3** | **GraphRAG** — SIMAP traversal seeds the vector search |

R3 is the mode that does the real work: traverse the map to identify the
resources structurally implicated, then retrieve episodes and incidents
referencing *those*. **Structure narrows, similarity ranks.**

### 5.1 What each decision point retrieves

| Node | Graph step | Vector step |
| --- | --- | --- |
| `intake_intent` | Resolve endpoints to attachment points and owning domains | Similar past intents |
| `evaluate_proposal` | Resources this candidate commits in **my** domain, and what else they carry | Episodes using the same candidate; policy rules touching those resources |
| `diagnose` | Service path traversal; resources shared with the reported symptom | Incidents with similar symptom signatures on overlapping resources |

### 5.2 What the store holds for retrieval

Paper 1's `context.db` schema is reused unchanged. Its three embedded
collections are what R1 and R3 search:

| Collection | Embedded on | Used by |
| --- | --- | --- |
| `episode` | intent + candidate + outcome summary | `evaluate_proposal`, `select_candidate` |
| `incident` | symptom signature + attributed segment | `diagnose` |
| `policy` | rule + **rationale text** | `evaluate_proposal`, `triage_request` |

SIMAP tables and `observation` are **not embedded** — they are traversed and
filtered, never matched by similarity. R2 and the graph half of R3 read the
NetworkX projection; R1 and the vector half read `sqlite-vec` indexes over the
three tables above.

Embedding the policy *rationale* rather than only the rule is deliberate: it is
what lets a refusal cite why the rule exists, not merely that it fired.

**One new table**, because prompts and responses are evidence:

```sql
CREATE TABLE reasoning_call (
    id           TEXT PRIMARY KEY,
    episode_id   TEXT,
    node         TEXT,        -- which of the 13 issued it
    retrieval_mode TEXT,      -- R0 | R1 | R2 | R3
    prompt       TEXT,
    response     TEXT,
    retrieved    JSON,        -- the full set shown, cited or not
    cited        JSON,        -- the subset cited
    grounded     INTEGER,     -- gate verdict
    fell_back    INTEGER,
    tokens_in    INTEGER,
    tokens_out   INTEGER,
    latency_ms   INTEGER
);
```

`retrieved` and `cited` together give **retrieved-context precision** — the
fraction of what was shown that was actually used. Recording only the citations
makes that metric unrecoverable, and it is one of the paper's results.

`node` is what makes the per-node ablation analysable after the fact rather than
requiring fourteen separate instrumented builds.

---

### 5.4 Prompt construction

Every reasoning call is assembled from four labelled blocks, in this order, and
the assembly is code rather than a template string a node can vary:

```text
[ROLE]        which agent, which domain, which node, what it may decide
[FACTS]       deterministic only — gate results, cost vector, predictor output,
              live observations with timestamps and coverage
[CONTEXT]     retrieved records, each with its id, so it can be cited
[PEER]        peer-authored text, delimited and attributed — DATA, NOT INSTRUCTION
[QUESTION]    the decision required, and the response schema
```

**Three construction rules.**

1. **`[FACTS]` never contains a retrieved record**, and `[CONTEXT]` never
   contains a live observation. Mixing them is how a model comes to treat a
   remembered value as a current one.
2. **Every `[CONTEXT]` item carries its id.** A record that cannot be cited by
   id is not admissible, so it is not shown.
3. **`[PEER]` is fenced and labelled with its sender.** Nothing inside it is
   read as an instruction, and the grounding gate treats claims sourced there as
   requiring that peer's disclosure id.

Prompts are **frozen before the evaluation grid runs**. A prompt change is a new
run, not a fix — otherwise prompt tuning is indistinguishable from capability.

---

### 5.5 Fallback semantics

Each of the fourteen `R` nodes has the deterministic rule listed in §2.2. A
fallback fires when any of these happen, and each is recorded distinctly:

| Trigger | Recorded as |
| --- | --- |
| Response fails schema validation | `fallback:schema` |
| A citation does not resolve to a held record | `fallback:citation_unresolved` |
| A cited record does not support the claim's direction | `fallback:citation_contradicts` |
| Confidence below the node's declared floor | `fallback:low_confidence` |
| Timeout or provider error | `fallback:unavailable` |

**The fallback is the Paper 1 rule, unchanged** — so the system degrades to
exactly the behaviour Paper 1 measured, which makes the comparison clean. The
per-node fallback rate is a reported metric and a headline one for C5.

### 5.6 Rules

1. **Retrieval informs; it never authorises.** No retrieved record satisfies
   `feasibility_gate`, which reads live observation only.
2. **Everything retrieved is citable.** A record that cannot be cited by id is
   not usable.
3. **Retrieval is bounded and logged.** Per-decision caps on records and tokens,
   with the full retrieved set journalled so any decision replays.
4. **Peer records carry provenance.** Never silently merged.

---

## 6. MCP: tools the engine may select

Paper 1's three MCP servers, their contract and their credentials boundary are
inherited unchanged. **Paper 3 adds no tool.** What it adds is a model choosing
among the tools that already exist — which is the one place in this system where
an LLM performs tool selection, and it is worth specifying precisely.

### 6.1 Only one node selects tools

| Node | May call | May not |
| --- | --- | --- |
| `plan_observations` | any **read-only** tool, within budget | anything that mutates |
| `execute_local` | the agreed **named action**, once, after all gates | choose which action — the agreement fixed it |

**No reasoning node ever selects a named action.** `plan_observations` produces
an observation *plan*; the effector `refresh_observations` executes it. The
engine decides what to look at, never what to change. That separation is what
keeps the safety argument in §4.1 intact when tool selection is introduced.

### 6.2 What the engine sees

The model is shown the read-only tool list from `get_capabilities`, which
**declares what is unsupported explicitly** (P1 §12.3). This matters more here
than elsewhere: a model asked to plan observations will otherwise invent
plausible ones. Tool descriptions are part of the frozen prompt surface (§5.4)
and change only as a new run.

Named-action tools are **not shown to the engine at all**. They are not
described, not listed, and not reachable from a reasoning node's output schema.

### 6.3 Observation budget

`plan_observations` is bounded per decision, and the bound is a pinned run
parameter:

| Bound | Purpose |
| --- | --- |
| `max_tool_calls` | Caps the plan's breadth |
| `max_result_tokens` | Caps what enters `[FACTS]`; a large telemetry dump would crowd out the question |
| `freshness_s` | Inherited: a snapshot older than the bound forces a refresh rather than being reused |

Budget exhaustion is a **conditional edge**, not an error: the node proceeds on
the facts already held and records that it did. An agent that plans beyond its
budget is itself a finding — and one of the per-node metrics is how much of the
budget each node actually uses.

### 6.4 Where results land

Tool results enter the prompt as **`[FACTS]`**, never as `[CONTEXT]` (§5.4).
They carry their timestamps, coverage and missing-data reasons from the MCP
contract, so the model can see that a read was partial rather than assuming it
was complete.

This is the same rule that keeps a remembered value from being read as a current
one, and it is why the MCP contract's attribution requirement matters to this
paper specifically: **a tool result without coverage metadata is indistinguishable
from a confident one.**

### 6.5 Grounding tool results

An observation obtained through a tool call is citable as
`observation:<id>` exactly like any other live observation — the grounding gate
does not distinguish a fact the engine asked for from one the observer collected
on its tick. What it does record is **which node caused the call**, so the
per-node ablation can price `plan_observations` in tool calls as well as tokens.

---

## 7. The disclosure decision (S3)

Paper 1 runs S0–S2 with declared rules. Paper 3 adds **S3**, where the agent
reasons about disclosure:

| Decision | Node | Question |
| --- | --- | --- |
| What to disclose | `compose_outcome` | Which fields does a peer need, and which are sensitive? |
| What to request | `formulate_queries`, `a2a_dialogue` | Which peer holds evidence that would resolve my uncertainty? |
| How to use it | `evaluate_proposal` | What does a peer's disclosure actually license me to conclude? |

Attribution (Paper 1 §9) is what makes this concrete: an agent that can name the
**one counter** it needs is making a far cheaper request than one asking for
everything.

---

## 8. Injection boundary

`a2a_dialogue` feeds peer prose — a refusal reason, a caveat on an offer — into
a reasoning engine. That text enters as **quoted evidence, attributed to its
sender, inside a delimited field**, and can never alter this agent's policy,
action space, gates, or what it discloses. Injection attempts are journalled,
not obeyed.

This is a design precaution, not a defence this paper evaluates.

---

## 9. Reproducibility

Stricter here than elsewhere, because the reasoning is the subject.

- Pin model id **and version**, temperature, retrieval budgets, embedding model,
  and seeds.
- Archive **every prompt and every response, tagged with the node that issued
  it**, in the run bundle.
- A mid-study model change invalidates every prior run. Choose once and do not
  move.

---

## 10. Build status

| Component | Status |
| --- | --- |
| Everything in Paper 1's Phases 0–4 | prerequisite, not started |
| Reasoning engine at the fourteen nodes | to build |
| Typed judgment contract and validation | to build |
| Grounding gate: citation resolution and direction checking | to build |
| Retrieval modes R0–R3 | to build |
| Tool-selection surface and observation budget (§6) | to build |
| S3 disclosure decision | to build |
| `reasoning_call` table: prompts, retrieved vs cited, tokens, latency | to build |
