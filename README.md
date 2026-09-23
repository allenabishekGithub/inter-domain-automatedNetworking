# Inter-domain automated networking

A **federated agentic networking system**: three independently owned network
domains, each operated by an autonomous agent with its own reasoning engine and
context database. The agents retrieve over a shared topology graph and their own
history, negotiate one end-to-end service over **A2A**, and learn from verified
outcomes that only their peers can observe.

Start with the **[design](docs/design.md)** — it is the build reference. The
**[research and build plan](docs/plan.md)** says what to measure and in what
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
| **Assure** | Attribute degradation to a path segment: act if it is yours, **refrain if it is not**, escalate if nothing can fix it |
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

Each agent holds a **context database**: the federated topology of all three
domains, its own history, and its owner's policy. It retrieves over that with
vector search, graph traversal and the hybrid of the two — needed because a
peer's outcome is a number without a referent until you know which resources it
traversed. Every claim an agent makes must cite what it was shown; claims that
cite nothing are rejected to a deterministic fallback.

## The data plane

Implemented here, in **[`packet-network/`](packet-network)** and
**[`optical-network/`](optical-network)**: eight SR Linux routers across two
packet domains, a four-ROADM Mininet-Optical line carrying one of two
wavelengths, and the `client-a` → `server-b` UDP service. On a prepared machine:

```bash
sudo scripts/service-up.sh
```

Starting from a fresh Ubuntu VM, work through the
[installation guide](docs/installation.md) first.

Each domain has a real provisioning choice — both packet domains can move the
service between a primary and a backup core router, and the optical domain can
carry it on either wavelength or refuse. That gives **eight joint
configurations**, small enough to enumerate exactly, which is why this design
needs no search algorithm. What no domain can do is reroute around an optical
cut: both wavelengths ride the same fibre chain, so a cut must be reported
honestly rather than repaired. Correct refusal and honest unresolved reporting
count as correct behaviour — reported separately from successful delivery.

## Status

Each agent is two LangGraphs over **21 nodes**: 13 reasoning nodes with the
engine behind them, 4 gates that are deterministic by construction, and 4
effectors. The gates are the whole safety argument — nothing reaches a device
without live-observation feasibility, declared policy and byte-identical
unanimity, and no rationale reaches a peer without resolving its citations.

The data plane, the ownership scoping and the device adapters exist and are
unit-tested. The agent runtime, A2A, the context store and retrieval, the
reasoning engine and the learning layer are designed and **not yet built**; see
the plan's [build phases](docs/plan.md#6-build-phases).

Two findings from the earlier assessment still block work and keep their
original IDs: **F4** (receiver samples cannot be proven fresh, which blocks
disruption measurement) and **F2** (repair requires the failed router to answer
gNMI). Detail in [`docs/old/known-issues.md`](docs/old/known-issues.md).

```bash
scripts/run-tests.sh       # 86 unit tests, both components
```
