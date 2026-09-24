# Inter-domain automated networking

A **federated agentic networking system**: three independently owned network
domains, each operated by an autonomous agent with its own reasoning engine and
context database. The agents retrieve over a shared topology graph and their own
history, negotiate one end-to-end service over **A2A**, and learn from verified
outcomes that only their peers can observe.

Start with the **[design](paper-1-federated-evidence/design.md)** — it is the build reference. The
**[research and build plan](paper-1-federated-evidence/plan.md)** says what to measure and in what
order. Those two documents are the current scope; everything in
[`docs/old/`](docs/old) is superseded source material.

```text
client-a
    |
 Packet A agent  <--A2A-->  Optical agent  <--A2A-->  Packet B agent
    |                       |                     |
 pe-a1 p-a1/p-a2 gw-a    r1 = r2 = r3 = r4    gw-b p-b1/p-b2 pe-b1
    |                                              |
    +------------ customer service path ----------> server-b
```

One agent per domain, and exactly one: each is the sole decision-making
authority inside its own borders. The agents cooperate on a user intent, but
every owner keeps its own credentials, policy and controller, and any owner may
refuse. No majority can authorize another domain's resources.

## Why federated

Ownership splits observation in a way that cannot be engineered away:

- **Packet A owns the sender.** It can prove packets left.
- **Packet B owns the receiver.** It alone can prove packets arrived.
- **Optical owns the line.** It sees margin, and nothing about delivery.

So no agent can independently observe the outcome of a decision it took part in.
Packet A can choose a path and never learn whether the service worked. Sharing
verified outcomes between owners is therefore the only way two of the three
agents learn at all — and whether that sharing pays for itself is the question
the study asks.

## What it does

| | Capability |
| --- | --- |
| **Provision** | Enumerate the eight joint configurations, negotiate over A2A, execute per owner — or refuse, honestly |
| **Assure** | A continuous loop per domain: attribute degradation to a path segment, act if it is yours, **refrain if it is not**, compensate by rate where a peer cannot repair itself |
| **Learn** | Predict how a configuration will perform — though two of the three owners can only learn if the third tells them what happened |
| **Disclose** | Decide what evidence a peer actually needs, rather than sharing everything or nothing |

Each agent is one process holding its own policy, predictor, context database,
journal, and the only credentials that reach its own devices. It **is** the
domain service orchestrator — there is no orchestration layer above it.

## Research question

> In a service crossing separately owned networks, the party that can measure the
> outcome is not the party that chose the configuration. What does sharing that
> outcome across an ownership boundary buy each owner, what does it cost in
> disclosure, and can agents decide what to share better than a fixed rule?

**Ownership separates features from labels.** Packet A and Optical hold local
telemetry and no delivery evidence whatsoever; Packet B holds every label and
only some features. Neither side can build a good predictor alone — and the
split follows from who owns the receiver, not from how a dataset was
partitioned.

The fixture sharpens this on purpose. Some impairments are **locally
invisible**: they degrade the service without appearing in any owner's own
counters, and only the receiver can see them. The optical agent's gOSNR is
**modelled-only** — a feature that looks informative and is not, because a
changed optical margin does not automatically change packet loss in this
emulator.

Each agent holds a **SIMAP** — a two-layer service–infrastructure map linking
services and their per-domain segments to the routers, interfaces, links and
channels that carry them. Each owner authors and signs only its own slice; the
union is what makes a peer's evidence mean anything, because "delivered ratio
0.94" is a number without a referent until the map says which segments the
service crossed and who owned each. Attribution and blast radius are traversals
of it, not hard-coded tables.

Agents retrieve over that map and their own history with vector search, graph
traversal and the hybrid of the two. Every claim an agent makes must cite what
it was shown; claims that cite nothing are rejected to a deterministic
fallback.

## The data plane

Implemented here, in **[`packet-network/`](packet-network)** and
**[`optical-network/`](optical-network)**: eight SR Linux routers across two
packet domains, a four-ROADM Mininet-Optical line carrying one of two
wavelengths, and the `client-a` → `server-b` UDP service. On a prepared machine:

```bash
sudo scripts/service-up.sh
```

Starting from a fresh Ubuntu VM, work through the
[installation guide](installation.md) first.

Each domain has a real provisioning choice — both packet domains can move the
service between a primary and a backup core router, and the optical domain can
carry it on either wavelength or refuse. That gives **eight joint
configurations**, small enough to enumerate exactly, which is why this design
needs no search algorithm. What no domain can do is reroute around an optical
cut: both wavelengths ride the same fibre chain, so a cut must be reported
honestly rather than repaired. Correct refusal and honest unresolved reporting
count as correct behaviour — reported separately from successful delivery.

## Status

Each agent is two LangGraphs over **25 nodes**: 14 reasoning nodes with the
engine behind them, 6 gates that are deterministic by construction, and 5
effectors. The gates are the whole safety argument — nothing reaches a device
without live-observation feasibility, declared policy and byte-identical
unanimity, and no rationale reaches a peer without resolving its citations.

The data plane, the ownership scoping and the device adapters exist and are
unit-tested. The agent runtime, A2A, the context store and retrieval, the
reasoning engine and the learning layer are designed and **not yet built**; see
the plan's [build phases](paper-1-federated-evidence/plan.md#8-build-phases).

## Three papers — choose one

This design contains more than one paper. Ten claims is two to three papers'
worth; a Q1 journal submission supports two to four claims well. **One must be
chosen before building past Phase 4.**

| Folder | Paper | Claims | Extra build | Venue |
| --- | --- | --- | --- | --- |
| [`paper-1-federated-evidence/`](paper-1-federated-evidence) | Federated outcome evidence and service attribution — **recommended first** | C1, C2, C4, C6, C7, C8 | Phases 0–4 | IEEE TNSM |
| [`paper-2-compensation/`](paper-2-compensation) | Cross-domain compensation and assurance-loop stability | C9, C10 | Phase 4b, on P1 | TNSM / JSAC |
| [`paper-3-grounded-reasoning/`](paper-3-grounded-reasoning) | Grounded agent reasoning for network operations | C3, C5, per-node value | Phase 5, on P1 | TNSM / agent venue |

**Paper 1 is the recommended first paper.** C1 establishes that the learning
floor is structural rather than imposed, and C7 is the same thesis expressed as
a mechanism — *the attribution method available to an agent depends on what its
peers disclose.* Those lock together, which is why federated learning and
service attribution do not separate cleanly.

**Paper 2 stands alone because of the separability argument:** it can prove no
compensation exists under the provisioning action space, then show exactly one
capability that breaks it — and that the capability is unusable without
cross-owner disclosure.

**Paper 3 is the most portable and the riskiest.** Faithfulness measured against
records that resolve or do not, decisions against packets that arrived or did
not. Its risk is C3, which may tie a good static rule; report it either way.

**A fourth option costs weeks and needs no results:** an architecture and
position piece for IEEE Network or Communications Magazine, staking the framing
while the system is built.

```text
now ──► position piece (weeks, no build)
    │
    └──► Phases 0–1 premise checks  ──►  everything gates here
              │
           Phases 2–4 ──► Paper 1  (~12 months)
              ├──► Phase 4b ──► Paper 2  (+4–6 months)
              └──► Phase 5  ──► Paper 3  (+4–6 months)
```

Papers 2 and 3 are independent of each other and both reuse Paper 1's system.

### The decision this forces

**Does Paper 1 need the reasoning engine?** None of its six claims requires one.
Deterministic agents drop Phase 5 — three to four months cheaper, far more
reproducible — but invite *"why is this agentic at all?"*. Running the engine
without evaluating it keeps the identity and makes Paper 3 a deepening rather
than a retrofit. **Decide before Phase 4 ends.**

**The code is shared.** The data plane, agents, MCP servers and SIMAP live at
the repository root and are built once. Paper folders hold each paper's
documentation, experiment configurations and results — never a fork of the
system.

## Repository layout

```text
README.md                     start here: what this is, and the three papers

installation.md               prepare a validation host from a fresh Ubuntu VM
data-plane.md                 exact topology, addressing, ownership, capability limits
known-issues.md               F1–F10; F2, F3 and F4 are on every paper's critical path
mcp-server-design.md          the controller tool contract
related-work-and-novelty.md   annotated literature, 24 references

packet-network/               8 SR Linux routers, gNMI adapter, traffic   (built, tested)
optical-network/              4-ROADM Mininet-Optical line                (built, tested)
scripts/                      service-up.sh, service-down.sh, run-tests.sh

paper-1-federated-evidence/   README + design + plan + experiments/ + results/
paper-2-compensation/         "
paper-3-grounded-reasoning/   "
```

**`paper-1-federated-evidence/design.md` is the canonical system design.**
Paper 1 is the base system, so everything Papers 2 and 3 inherit is specified
there; each of those documents is authoritative only for what it adds. The
superseded ACO/PSO/Nash architecture is in git history at `e317844` and earlier.

Two findings from the earlier assessment still block work and keep their
original IDs: **F4** (receiver samples cannot be proven fresh, which blocks
disruption measurement) and **F2** (repair requires the failed router to answer
gNMI). Detail in [`known-issues.md`](known-issues.md).

```bash
scripts/run-tests.sh       # 86 unit tests, both components
```
