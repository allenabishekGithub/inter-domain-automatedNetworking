# Paper 3 — Research and validation plan

**Companion to** [`design.md`](design.md).
**Prerequisite:** [Paper 1](../paper-1-federated-evidence) Phases 0–4 complete.
**Target:** IEEE TNSM (Q1), or an agent/AI venue where the ground-truth angle lands harder.
Nothing here is a measured result.

> **Base-system update, 24 September 2026:** Paper 1 now targets
> [recovery under limited disclosure and stale evidence](../paper-1-federated-evidence/tnsm-proposal.md)
> with deterministic evidence scheduling. That adaptive method is a required
> comparator and fallback here. Hold acquisition policy constant when isolating
> reasoning value; evaluate any LLM change to acquisition separately.
> Freeze the inherited graph/schema version before comparison. The claims below
> remain proposals and need their own literature and empirical validation.


---

## 1. The question

> Does retrieval-grounded LLM reasoning improve multi-domain network decisions,
> is its justification faithful, and which reasoning steps actually earn their
> tokens?

## 2. What is new

**1. Faithfulness with an external referent.** Most work on grounding evaluates
text against text, where "supported" is itself a judgment. Here a citation
either resolves to a record the agent holds or it does not, and either supports
the claim's direction or it does not. Binary, checkable, automatable.

**2. Decision quality against physical ground truth.** The receiver either got
the packets or it did not. No LLM judge, no human rater.

**3. Per-node accounting.** Fourteen reasoning nodes, ablated one at a time.
Which steps carry the benefit and which could be rules is a question the field
mostly avoids, and answering it is more useful than "agents work".

**4. A gate that makes an LLM admissible in a control path.** *It may reason,
but it may not assert* — stated as a design rule and measured as a rate.

---

## 3. Claims

| # | Claim | Evidence |
| --- | --- | --- |
| **C5** | Reasoning is faithful because it is **gated**, not because it is trusted | Ungrounded-assertion rate with the gate off; firing and fallback rate with it on; decision quality unharmed |
| **C3** | Agents reasoning about what to share approach full-disclosure quality at materially lower disclosure | S3 versus Paper 1's adaptive scheduler, S1, and S2: recovery/risk/coverage within declared margins at lower disclosure |
| — | Per-node reasoning value | Fourteen single-node ablations: marginal decision quality, fallback rate, divergence from rule |

**Honest risk, stated up front.** C3 is the most likely null result in the
programme: with eight configurations and a modest episode count, a good static
disclosure rule may tie or beat a reasoned one. **Build the paper's spine on C5
and the per-node ablation**, where a negative result is still a contribution.

---

## 4. Experiments

**E5 — Grounding and faithfulness.** Gate on versus off.

With it **off**, measure the rate of load-bearing claims that cite nothing, cite
a record the agent does not hold, or contradict the record they cite. With it
**on**, measure firing rate, fallback rate, and whether decision quality
suffers.

Include **adversarially ambiguous evidence** where a plausible-but-wrong story
is available, and episodes where a peer's disclosure is stale or partial.
*C5.*

**E6 — Retrieval ablation.** R0 / R1 / R2 / R3 on the same decisions. Score on
decision quality **and retrieved-context precision** — what fraction of what was
retrieved was actually cited.

Run over both provisioning and diagnosis. The modes are expected to separate
mainly on diagnosis, because provisioning has only eight candidates to choose
among. If R3 does not beat R1 on diagnosis, say so — GraphRAG is a cost as well
as a capability.

**E7 — Per-node ablation.** Disable the engine at one reasoning node at a time,
falling back to that node's deterministic rule while the other thirteen keep
reasoning. Fourteen runs over identical fixtures.

Expected shape: a few nodes carry most of the benefit — likely `diagnose`,
`plan_observations`, `select_candidate` — and several could be rules. **Saying
which is the contribution.**

**E8 — Disclosure decision.** Compare S3 with Paper 1's deterministic adaptive
scheduler, S2 (good static rule), and S1 (full permitted disclosure). Use the
same validity/authority checks, budgets, model access, and recovery/risk/coverage
metrics. The deterministic fallback includes Paper 1's acquisition method.
Any gain from changing acquisition must be distinguished from reasoning over a
fixed evidence set. *C3.*

---

## 5. Baselines and ablations

| Condition | What changes |
| --- | --- |
| **A0** — rules only | Engine disabled throughout; Paper 1's deterministic adaptive scheduler and controller |
| **A1** — engine, no retrieval | R0. Isolates what context contributes |
| **A2** — engine, gate off | Isolates the grounding gate |
| **A3** — full system | Engine + R3 + gate |
| **A4** — oracle | Retrospectively best decision per episode. Upper bound |

A0 vs A3 is the headline. A2 vs A3 is C5. A1 vs A3 says whether retrieval earns
its tokens.

---

## 6. Metrics

| Group | Measures |
| --- | --- |
| Faithfulness | Ungrounded-claim rate; gate firing rate; fallback rate; citation resolution failures |
| Decision | Regret vs A4; refusal correctness; divergence from the deterministic rule |
| Diagnosis | Cause correctness; next-observation usefulness; time to correct diagnosis |
| Retrieval | Retrieved-context precision; recall of the resource actually at fault; records per decision |
| Per-node | Marginal decision quality, fallback rate and token cost for each of the 14 nodes |
| Tool use | Read-only MCP calls per decision; budget utilisation; observations requested but never cited |
| Cost | Tokens and latency **per node**; disclosure volume; A2A messages |

---

## 7. Build phase

**Phase 5**, on top of Paper 1's Phases 0–4: the engine at its fourteen nodes,
the typed judgment contract, the grounding gate, retrieval modes R0–R3, the S3
disclosure decision, and prompt/response archiving.

Indicative effort: **four to six months** after Paper 1's system is running.

---

## 8. Threats to validity

| Threat | Mitigation |
| --- | --- |
| **Trivial decision space** — eight candidates | Lean on diagnosis, where ambiguity is real; state the limit for provisioning |
| **Prompt tuning masquerading as capability** | Freeze prompts before the evaluation grid; report any change as a new run |
| **Model version drift** | Pin id and version; a change invalidates prior runs |
| **Cherry-picked ambiguity** | Predeclare the ambiguous scenarios and their discriminating observations |
| **Grounding gate scores itself** | The gate is deterministic code, never a model call; its checks are citation resolution and direction only |
| **Tool selection confounded with reasoning quality** | `plan_observations` is ablated separately (E7); tool calls are recorded per node so observation cost is attributable |
| **Retrieval precision gamed by retrieving less** | Report precision **and** recall of the resource actually at fault |
| **Single model does not generalise** | Scope every claim to the pinned model; a second model is a separate study |

---

## 9. Not tested in this paper

- **Recovery under disclosure budgets and evidence-validity constraints.** Paper 1.
- **Compensation and loop stability.** Paper 2.
- **Model comparison or fine-tuning.** One pinned model.
- **Prompt injection as an attack.** The boundary is a design precaution
  ([design §8](design.md#8-injection-boundary)), not an evaluated defence.
- **Natural-language intent from real operators.** Intents are structured or
  templated; conversational intake is a separate study.
- **Scale.** Three agents, eight configurations, fourteen infrastructure nodes.

---

## 10. Statistical design

**The independent unit is a complete chronological stream**, matched across
conditions on seeds and schedule. Reasoning calls within a stream are dependent:
the context store grows as episodes accumulate.

- **Model non-determinism is a variance source, not noise to average away.** Run
  each condition at n ≥ 5 streams and report the spread across streams
  separately from the spread within.
- Temperature is pinned. If it is non-zero, repeat identical inputs to
  characterise call-level variance before attributing differences to conditions.
- For the per-node ablation, the contrast is **one node disabled against all
  fourteen enabled**, on identical streams — a paired comparison, not fourteen
  independent experiments.
- Adjust for fourteen confirmatory contrasts in the node ablation, or declare it
  exploratory and say so.
- **Report the negative results prominently.** A node whose ablation changes
  nothing is a finding.

---

## 11. Run bundle

Paper 1's structure, plus everything needed to replay a reasoning decision:

```text
run-<id>/
  manifest.json              + model id, version, temperature, embedding model
  prompts/frozen/            the exact prompt assemblers used, hashed
  agents/agent-*/reasoning_call.jsonl   per call: node, mode, prompt, response,
                                        retrieved, cited, grounded, fell_back, tokens, latency
  analysis/per_node.parquet  one row per call
```

**A reasoning result that cannot be replayed from `reasoning_call.jsonl` is not
a result.** That table is why the per-node ablation can be analysed after the
fact rather than needing fourteen instrumented builds.

---

## 12. Figures and tables

| # | Figure | Shows |
| --- | --- | --- |
| **F1** | Ungrounded-claim rate, gate off vs on, by node | **The headline for C5** |
| F2 | Decision quality against gate state | That gating costs little or nothing |
| F3 | Retrieved-context precision and fault recall, R0–R3 | Whether GraphRAG earns its tokens |
| F4 | Per-node marginal decision quality vs token cost | Which of the fourteen earn their call |
| F5 | Disclosure volume vs quality, S1/S2/S3 | C3 — including a null |
| F6 | Fallback rate by trigger, per node | Where the engine is unreliable |

| # | Table | Shows |
| --- | --- | --- |
| T1 | Divergence from the deterministic rule, per node, and whether divergence helped | The most direct evidence reasoning adds anything |
| T2 | Tokens and latency per node per episode | The cost of being agentic |
| T3 | Diagnosis correctness by retrieval mode | Where the modes actually separate |

---

## 13. Claim-to-evidence release criteria

| Claim | Release criterion |
| --- | --- |
| **C5** | Ungrounded-claim rate with the gate off is materially above zero, and with the gate on no ungrounded claim reaches a peer, with decision quality not significantly worse |
| **C3** | S3 achieves quality within the declared margin of S1 at significantly lower disclosed volume, and improves on both S2 and Paper 1's adaptive scheduler. **Report ties or regressions** |
| Per-node | Each of the fourteen nodes is classified as *earns its call*, *no measurable effect*, or *harmful*, with the effect size for each |

**If C3 is null, the paper's framing shifts to C5 plus the per-node
classification** — which was always the more defensible spine. Decide that
before running the grid, not after seeing it.

---

## 14. Open decisions

| Decision | Deadline | Default if unmade |
| --- | --- | --- |
| Which model, and pinned version | Phase 5 start | Latest available at freeze; **never changed mid-study** |
| Temperature | Phase 5 start | 0, with a variance check at the chosen value |
| Confidence floor per node | Phase 5 start | Uniform, calibrated on the pilot |
| Is S3 evaluated here or dropped? | before the grid | Evaluated, reported, not claimed |
| Streams per condition | after the pilot | n ≥ 5, set by observed cross-stream variance |
