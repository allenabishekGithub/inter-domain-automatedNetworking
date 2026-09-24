# Inter-domain automated networking

A research testbed for managing a service across three independently owned
network domains: Packet A, Optical, and Packet B. The repository contains the
packet and optical data-plane components and adapters. The cross-domain
controllers, evidence scheduler, and research evaluation are proposed work.

**Recommended first paper:** *Recovery Under Limited Disclosure and Stale
Evidence in Multi-Domain Networks*, targeting **IEEE Transactions on Network
and Service Management (TNSM)**. The candidate contribution is an online method
that chooses which peer evidence to request, when to collect compatible
measurements, and whether they support a permitted recovery action at execution
time. Novelty and performance remain to be established.

Start with the [Paper 1 proposal](paper-1-federated-evidence/tnsm-proposal.md),
then the [validation and build plan](paper-1-federated-evidence/plan.md).
The [state-of-the-art assessment](paper-1-federated-evidence/state-of-the-art.md)
documents prior work and the limits on the novelty claim. The
[shared system design](paper-1-federated-evidence/design.md) specifies the
proposed implementation inherited by Papers 2 and 3.

```text
client-a
    |
 Packet A controller <--A2A--> Optical controller <--A2A--> Packet B controller
    |                         |                          |
 pe-a1 p-a1/p-a2 gw-a      r1 = r2 = r3 = r4       gw-b p-b1/p-b2 pe-b1
    |                                                    |
    +--------------- customer service path ------------> server-b
```

## Why federated

Owners control different resources and may restrict what they disclose. Packet A
measures sender-side traffic; Packet B measures receiver delivery; Optical
observes its line and modelled optical quality. Receiver feedback can be shared
when policy permits. Ownership alone does not prove that an owner cannot learn
or operate effectively from local information.

The proposed system gives each domain its own controller, credentials, policy,
and journal. An owner may refuse a request or action. Evidence about a resource
does not confer authority to change it; affected owners must approve execution.
Independent credential enforcement is implementation work, distinct from the
inventory scoping already present in the adapters.

## Research question

> Can a controller improve verified service recovery under a disclosure budget
> by scheduling compatible evidence for the anticipated execution time, compared
> with established active diagnosis using the same validity and authority checks?

The difficult case is evidence that arrives late or describes different traffic
cohorts, paths, or policy revisions. Collecting more records can consume the
budget while earlier observations become unsuitable for a pending action.

The method will be evaluated on service loss during the incident, time to verified
recovery, harmful actions, missed repairs, disclosure, and wasted or repeated
collection. Waiting and escalation retain their service-loss cost. A controller
that always abstains cannot pass on a low harmful-action rate alone.

Feature/label separation, cross-domain diagnosis, action-focused active testing,
and service–infrastructure maps have precedents. Merely adding timestamps,
agents, or a freshness gate is insufficient. The initial implementation will be
deterministic; learned action-effect models are optional and must be validated.
LLM reasoning and retrieval evaluation belong to Paper 3.

## The data plane

The components in [packet-network/](packet-network) and
[optical-network/](optical-network) describe eight SR Linux routers, a
four-ROADM Mininet-Optical line, two wavelength choices, and a
`client-a` → `server-b` UDP service. On a prepared validation host:

```bash
sudo scripts/service-up.sh
```

Use the [installation guide](installation.md) for a fresh Ubuntu VM and
[data-plane reference](data-plane.md) for topology and capability limits.

Two packet-path choices per packet domain and two optical choices give **eight
joint configurations**. Exact action enumeration is appropriate for this pilot;
the research problem concerns evidence collection under changing state.
Both wavelengths share the same fibre chain, so switching wavelength cannot
repair a fibre cut. Modelled optical margin does not itself cause packet loss in
this emulator. Those limits must remain explicit in experiments and claims.

## Status

The component adapters have unit tests; earlier local validation passed 86 tests.
This is not evidence of a successful live end-to-end deployment or research
results. The domain controllers, MCP servers, A2A workflow, context store, and
evidence scheduling method remain to be built and evaluated.

The shared design proposes two episode graphs with 25 nodes as a starting
implementation. Deterministic gates enforce specified checks; they are not a
proof of physical safety under arbitrary state changes or inaccurate telemetry.

Begin with a small offline comparison against fixed matched-counter collection
and strong adaptive diagnosis. In parallel, resolve the measurement and recovery
issues needed for live validation, especially F2, F3, F4, and F6 in the
[implementation prerequisites](paper-1-federated-evidence/plan.md#16-implementation-prerequisites-and-retained-findings).
Expand the runtime only if the pilot supports
the proposed contribution. See [build phases](paper-1-federated-evidence/plan.md#8-build-phases).

## Three papers — choose one

**Proceed with Paper 1 first, subject to its pilot go/no-go decision.** Papers 2
and 3 are separate extensions; their additional research claims need their own
validation and literature checks.

| Folder | Research scope | Build scope | Venue direction |
| --- | --- | --- | --- |
| [Paper 1](paper-1-federated-evidence/README.md) | Recovery under limited disclosure and stale evidence | Phases 0–4; deterministic algorithm first | IEEE TNSM |
| [Paper 2](paper-2-compensation/README.md) | Rate compensation and interacting continuous assurance loops | Phase 4b on the validated base | TNSM; assess other venues against results |
| [Paper 3](paper-3-grounded-reasoning/README.md) | Measured value of grounded LLM reasoning | Phase 5 on the validated deterministic base | TNSM or an appropriate agent venue |

TNSM is the recommended journal on topic fit. The Q1 requirement must be checked
against the ranking database, category, and edition required by the institution
when selecting the submission venue; this repository does not establish a
current quartile ranking. No acceptance or completion timeline is assumed.

All papers share implementation at the repository root. Paper folders hold
their research documents, experiment configurations, and results; they do not
fork the controller or data plane.

## Repository layout

```text
README.md                     programme overview and current direction
installation.md               prepare a validation host
data-plane.md                 topology, ownership, and capability limits
mcp-server-design.md          proposed local controller tool contract
related-work-and-novelty.md   historical literature catalogue and review links

packet-network/               packet topology, adapter, and traffic tools
optical-network/              optical topology and adapter
scripts/                      service lifecycle and component tests

paper-1-federated-evidence/   proposal, review, shared design, validation plan
paper-2-compensation/         continuous-control extension
paper-3-grounded-reasoning/   grounded-reasoning extension
```

The [proposal](paper-1-federated-evidence/tnsm-proposal.md) defines the current
research contribution; the [plan](paper-1-federated-evidence/plan.md) defines how
to test it and retains the implementation prerequisites; the [design](paper-1-federated-evidence/design.md) defines the shared
implementation. Historical ACO/PSO/Nash designs remain in git history at
`e317844` and earlier.

```bash
scripts/run-tests.sh
```
