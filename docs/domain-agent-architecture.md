# Three-domain agent architecture

## Purpose and boundary

This repository focuses on collaboration among three agents owned by different
network operators. Each agent contains a **Domain Service Orchestrator (DSO)**:
a local instance of the service-orchestrator capabilities needed to handle its
part of a cross-domain service.

| Domain | Agent + DSO owns | Local controller owns |
|---|---|---|
| Packet A | Local ingress/egress view, packet-path candidates, QoS contribution, policy and local approval | Router, VPN/SR/MPLS/EVPN, queue and shaping changes |
| Optical | Border attachments, transport/spectrum candidates, QoT contribution, policy and local approval | Transponder, OTN, ROADM and spectrum changes |
| Packet B | Local ingress/egress view, packet-path candidates, QoS contribution, policy and local approval | Router, VPN/SR/MPLS/EVPN, queue and shaping changes |

The design does **not** assume a central entity authorizes every controller.
Instead, each DSO owns an equal replica of the complete federated topology:
every node, interface, link, relationship, and approved configuration state
advertised by the three domains. Each DSO remains the only authority that can
ask its own controller to reserve or activate a resource.

This takes the useful parts of the local `AgenticAI-packet-optical-qos-platform`
reference—scoped agents, typed candidate messages, direct agent-to-agent
negotiation, freshness checks, and controller safety gates—while distributing
the central service-orchestrator responsibilities across the three domains.

## Architecture

```mermaid
flowchart LR
    U[Authorized user] --> A[Packet A agent + DSO\nintent ingress]
    A <-->|A2A: contracts + topology sync| O[Optical agent + DSO]
    O <-->|A2A: contracts + topology sync| B[Packet B agent + DSO]
    A <-->|A2A: topology sync| B
    A --> CA[Packet A controller]
    O --> CO[Optical controller]
    B --> CB[Packet B controller]
    CA --> P[Packet A]
    CO --> T[Optical transport]
    CB --> Q[Packet B]
```

The data plane follows network adjacency: Packet A connects through Optical to
Packet B. The agent control plane is a full peer mesh, so every DSO can
handshake directly with every other DSO and converge on the same topology graph.
Service negotiation still follows the data-plane path; a direct Packet A–Packet
B control-plane session does not grant either agent authority to bypass the
optical domain.

The DSO that receives the user intent is the **initiating DSO**. It owns the
workflow correlation ID and tells the user the result. That is coordination of
one request, not authority over another domain: every remote decision is local
to the DSO that signed it.

The design has three connected planes. Keeping them separate makes it clear
which component can see, decide, and act on a given fact.

```mermaid
flowchart TB
    subgraph SP[Service plane]
        UA[User intent] --> SC[Service contract]
        SC --> SLA[End-to-end SLA]
    end
    subgraph CP[Agent control plane]
        A1[Packet A DSO] <--> A2[Optical DSO]
        A2 <--> A3[Packet B DSO]
        A1 <--> A3
        FG[Federated Topology Graph] --- A1
        FG --- A2
        FG --- A3
    end
    subgraph DP[Network data plane]
        N1[Packet A nodes] --- N2[Optical nodes] --- N3[Packet B nodes]
    end
    SP --> CP
    CP --> DP
```

## Federated service orchestration

Every DSO implements the same bounded capabilities, scoped to its operator:

| Capability | Local behavior | Cross-domain behavior |
|---|---|---|
| Intent ingress | Authenticate a local user and translate intent to a local service request | Forward only a scoped contract to an adjacent DSO |
| Service lifecycle | Maintain the domain's service state, revision, reservation and receipt | Exchange signed lifecycle events for the same correlation ID |
| Service map | Maintain the local authoritative segment and merge every signed peer segment into the Federated Topology Graph | Publish owned nodes, interfaces, links, relationships, and approved configuration revisions |
| Policy and planning | Construct feasible local candidates and enforce local policy | Offer, counteroffer, accept, or reject a joint contract |
| Execution | Ask its own controller to reserve, commit, or roll back a named local operation | Never call a peer's controller |
| Assurance | Collect local and border evidence and evaluate its QoS contribution | Send signed status/evidence summaries to the initiating DSO |

This gives every agent the useful lifecycle and assurance capabilities of the
reference platform's Service Orchestrator without giving any one instance
another domain's controller credentials or unilateral execution authority. Each
DSO persists its own service record and a full **Federated Topology Graph**.
The common replicated view is the signed topology/configuration graph,
`ServiceContract`, and lifecycle events, so all three can agree whether the
contract is offered, reserved, committed, verified, failed, or rolled back.

## End-to-end operating model

The system operates as a federation of equal DSOs, not as a central orchestrator
that commands three subordinate domains.

1. **Peer bootstrap and topology convergence.** Packet A, Optical, and Packet B
   mutually authenticate, exchange Agent Cards, and synchronize signed topology
   and configuration snapshots. Every DSO then holds the full multi-domain graph:
   nodes, interfaces, packet and optical links, node relationships, capacities,
   operational state, and approved configuration revisions. Signed deltas keep
   all replicas current.
2. **Intent admission.** An authorized user submits a desired service outcome to
   any DSO. The receiving DSO becomes the initiating DSO for that correlation ID.
   It authenticates the user, checks local entitlement, records the intent, and
   creates the initial versioned `ServiceContract`.
3. **Path and QoS planning.** Every affected DSO uses the same federated graph
   to validate end-to-end continuity and configuration compatibility. The
   initiating DSO derives bandwidth, latency, loss, availability, deadline, and
   budget requirements; each domain derives the contribution it can make.
4. **Local candidate generation.** Each DSO creates only local,
   controller-feasible candidates. Packet DSOs may offer packet paths, QoS
   profiles, and border attachments. The Optical DSO may offer a transport path,
   wavelength/spectrum allocation, and transponder settings. Bounded swarm
   scouts explore the shared graph to discover and rank diverse alternatives.
   AI may explain or rank these candidates, but deterministic code checks their
   evidence, freshness, topology/configuration compatibility, and policy.
5. **Game-theoretic negotiation.** Each domain calculates its private local
   utility from SLA value, settlement, capacity consumption, opportunity cost,
   operations, energy, and risk. The DSOs exchange signed offers,
   counteroffers, and acceptance messages. They choose a contract only if it
   meets the SLA and budget and is individually beneficial to every domain over
   its fallback. Weighted Nash bargaining selects among such contracts.
6. **Reservation and commit.** Each DSO reserves its own named resources through
   its own controller. When every reservation receipt is valid, each DSO rechecks
   policy and current graph/configuration state, then commits its local action.
   This is a distributed saga: a failure, timeout, stale plan, or failed
   verification causes reservation expiry or compensating rollback, never a
   cross-domain controller write.
7. **Service verification.** The DSOs collect fresh endpoint, border, packet,
   and optical measurements. They exchange signed verification summaries and
   mark the service active only when the applicable end-to-end SLA is proven.
8. **Continuous assurance.** Every DSO independently runs a closed loop that
   monitors, analyzes, plans, acts locally, verifies, and records the result.
   A local action affecting a shared service returns to bargaining before commit.
   A short-lived coordination lease prevents three simultaneous loops from
   issuing conflicting negotiations for the same incident.
9. **Continual learning.** Terminal outcomes feed each DSO's asynchronous
   learning graph. It learns calibrated QoS, risk, cost, and ranking estimates
   from evidence and signed peer outcomes. Learning is observational, advisory,
   or review-gated; it cannot create a controller action or bypass the service
   lifecycle gates.

The resulting path is therefore:

```text
user intent → federated topology-aware planning → bargaining → reservation
→ local commits → end-to-end verification → closed-loop assurance → learning
```

Each domain can see the complete topology and approved configuration state, but
ownership remains local: only the owning DSO can reserve, commit, roll back, or
change its controller-managed resources.

```mermaid
flowchart LR
    I[Intent] --> V[Validate identity and policy]
    V --> G[Read synchronized topology and configuration graph]
    G --> W[Swarm explores feasible alternatives]
    W --> C[Create local candidates and cost quotes]
    C --> B[Nash bargaining among DSOs]
    B --> R[Time-bound local reservations]
    R -->|All valid| X[Each DSO commits through its controller]
    R -->|Any reject or expiry| F[Release or compensate]
    X --> Q[Endpoint and border verification]
    Q -->|SLA proven| A[Active service and assurance loop]
    Q -->|SLA not proven| F
    A --> L[Outcome trace and continual learning]
```

## A2A federation substrate

A2A is the required base protocol for every DSO-to-DSO interaction. The system
does not define a parallel peer REST protocol for topology, negotiation, swarm,
assurance, or learning. Each DSO publishes an A2A Agent Card, discovers peers
through their cards, and exchanges typed payloads through A2A messages, tasks,
and artifacts over mutually authenticated HTTPS.

```mermaid
flowchart LR
    PA[Packet A DSO] -->|A2A Agent Card\nmessage:send\ntask and artifact| O[Optical DSO]
    O -->|A2A Agent Card\nmessage:send\ntask and artifact| PB[Packet B DSO]
    PA -->|A2A Agent Card\nmessage:send\ntask and artifact| PB
    PA -->|Local MCP client| CA[Packet A Controller MCP Server]
    O -->|Local MCP client| CO[Optical Controller MCP Server]
    PB -->|Local MCP client| CB[Packet B Controller MCP Server]
```

| A2A facility | Role in this architecture |
|---|---|
| Agent Card | Peer discovery, DSO identity, supported schema versions, domain scope, authentication requirements, and advertised skills. |
| `message:send` | Delivery of every typed peer request, offer, status event, or synchronization message. |
| Task/context IDs | Bind related topology, service, incident, bargaining, reservation, and learning exchanges to one correlation chain. |
| Artifacts | Carry validated structured results such as topology snapshots/deltas, candidate sets, signed offers, receipts, verification summaries, and learning releases. |
| A2A extensions | Declare the domain-specific typed contracts below without changing A2A core transport and task semantics. |

The following A2A extensions define the federation payloads:

| Extension | A2A artifacts/messages it carries |
|---|---|
| `topology-federation/v1` | `TOPOLOGY_DIGEST`, `TOPOLOGY_SNAPSHOT`, `TOPOLOGY_DELTA`, `TOPOLOGY_SYNC_ACK`, and withdrawal records. |
| `service-contract/v1` | Intent-derived contracts, offers, counteroffers, acceptances, coordination leases, reservations, commits, rollbacks, and verification summaries. |
| `swarm-optimization/v1` | `SWARM_QUALITY_SIGNAL`, `SWARM_CANDIDATE`, and `SWARM_FEEDBACK`. |
| `continual-learning/v1` | Peer outcome summaries, evidence references, and signed learning releases/revocations. |
| `knowledge-federation/v1` | Signed shared runbook, policy, incident-summary, and approved knowledge-release metadata for local RAG indexing. |

The controller interfaces remain local to their owning DSO and are not A2A peer
interfaces. A2A enables an agent to ask a peer to reason, reserve, accept, or
verify; it never gives that peer direct controller access. mTLS authenticates
the transport connection, while each typed A2A artifact also carries its owner,
schema version, correlation ID, graph/contract revision, expiry, digest, and
signature.

## Local SDN controller MCP servers

Each networking domain exposes one **Controller MCP Server** in its own trust
boundary. The owning AI agent/DSO uses it as its only controller integration:
to observe state, prepare an approved configuration change, commit it, roll it
back, and retrieve verification evidence. Packet A cannot call the Optical or
Packet B MCP Server; the Optical DSO cannot call a packet-domain MCP Server.

```mermaid
flowchart LR
    AI[Domain AI agent\nreasoning and candidate proposal] --> DSO[Domain Service Orchestrator\npolicy, bargaining, transaction gate]
    DSO -->|MCP tool call| MCP[Local Controller MCP Server]
    MCP --> SDN[Local SDN controller]
    SDN --> NE[Owned network elements]
    NE --> SDN
    SDN --> MCP
    MCP -->|MCP tool result| DSO
    DSO -->|signed A2A topology or service update| PEER[Peer DSOs]
```

The Controller MCP Server exposes typed tools rather than a generic shell or
unbounded configuration channel:

| MCP tool | Purpose |
|---|---|
| `get_topology` / `get_inventory` | Return the domain's current nodes, interfaces, links, capabilities, and controller revision for topology federation. |
| `get_configuration` / `get_telemetry` | Return configuration state and measured health for the agent's read-only reasoning and closed loop. |
| `validate_change` | Validate a named configuration patch or resource request against controller inventory, schema, policy, and current state without changing the network. |
| `reserve_resources` | Create an idempotent, time-bound local reservation for a negotiated candidate. |
| `prepare_change` | Persist a controller-validated transaction and rollback information while leaving traffic unchanged. |
| `commit_change` | Apply the prepared packet, optical, or QoS configuration transaction to the local SDN controller. |
| `rollback_change` / `release_reservation` | Compensate a failed or expired transaction using its local receipt. |
| `get_transaction` / `verify_change` | Return durable controller receipts and post-change operational evidence. |

Packet-domain MCP servers map these tools to their SDN controller's routing,
VPN, QoS, interface, and traffic-engineering APIs, such as typed OpenConfig or
controller-native models. The Optical MCP Server maps them to its transport,
transponder, ROADM, channel, spectrum, and QoT APIs, such as typed T-API,
OpenConfig optical models, or controller-native models.

The AI agent can therefore cause a network configuration change through MCP,
but only through this transaction path:

```mermaid
sequenceDiagram
    participant A as AI agent
    participant D as Owning DSO
    participant M as Local Controller MCP Server
    participant C as Local SDN controller

    A->>D: Candidate and rationale
    D->>D: Verify evidence, policy, contract, graph, and peer agreement
    D->>M: validate_change
    M->>C: Validate typed configuration transaction
    C-->>M: Validation result
    M-->>D: Feasible transaction and rollback reference
    D->>M: reserve_resources / prepare_change
    M->>C: Reserve and prepare
    C-->>M: Durable reservation receipt
    M-->>D: Receipt
    D->>D: Recheck agreement and reservation barrier
    D->>M: commit_change
    M->>C: Apply configuration transaction
    C-->>M: Controller receipt and observed state
    M-->>D: verify_change result
```

Every mutating MCP call is bound to the local domain ID, service/incident
correlation ID, graph and contract revisions, candidate digest, idempotency key,
expiry, and caller workload identity. The DSO's `controller_transaction` node
uses these tools only after candidate verification, game-theoretic agreement,
reservation, and commit authorization. A successful MCP tool call proves only
that local configuration completed; the DSO still requires fresh service
verification before declaring the end-to-end service healthy.

## Federated topology and configuration exchange

Use OSPF's link-state database as the mental model: every peer learns a
consistent graph rather than requesting an end-to-end path from one central
controller. The mechanism is agent-to-agent topology federation, not OSPF
itself. It works across the three operator domains and carries both topology
and the configuration state required for service reasoning.

Every DSO maintains a local `FederatedTopologyGraph` with these object types:

| Object | Required fields | Relationship represented |
|---|---|---|
| Domain | `domain_id`, owner identity, topology revision | Owns nodes and local configuration advertisements |
| Node | globally unique `node_id`, owner domain, role, device type, operational state | Contains interfaces; may be a packet router, gateway, ROADM, transponder, or server |
| Interface/port | `interface_id`, parent node, layer, admin/operational state, capacity | Terminates a link or domain handoff |
| Link | `link_id`, two interface IDs, layer, capacity, latency, state, metric | Edge between two nodes; preserves packet, optical, and inter-domain adjacency |
| Configuration | owner revision, desired state, observed state, policy profile, QoS/transport parameters | Binds approved configuration state to one node, interface, or link |
| Service attachment | service/tenant reference, ingress/egress interface, reservation state | Connects a negotiated service to graph resources |

Each configuration object is structured data—for example YANG/OpenConfig paths,
SR/MPLS policy attributes, VLAN/EVPN attachment attributes, optical channel or
spectrum parameters, and QoS profiles. It must exclude controller credentials,
private keys, and shared secrets. Its owner is the only writer; all peer DSOs
replicate it as read-only reasoning state.

```mermaid
flowchart LR
    subgraph PA[Packet A contribution]
        PA1[server-a] --- PA2[PE-A] --- PA3[GW-A]
    end
    subgraph OD[Optical contribution]
        O1[Transponder A] --- O2[ROADM chain] --- O3[Transponder B]
    end
    subgraph PB[Packet B contribution]
        PB1[GW-B] --- PB2[PE-B] --- PB3[server-b]
    end
    PA3 --- O1
    O3 --- PB1
    PA1 -. service attachment .-> PB3
```

### Handshake and synchronization

When a peer relationship starts or recovers, the two DSOs perform this sequence:

1. Mutually authenticate with mTLS, exchange Agent Cards, and agree on the
   topology schema and configuration-model versions.
2. Exchange `TOPOLOGY_DIGEST` messages listing the latest signed revision for
   each originating domain.
3. Request and verify missing `TOPOLOGY_SNAPSHOT` or `TOPOLOGY_DELTA` records.
   Every record is signed by its owning DSO and includes an origin-domain ID,
   monotonic sequence number, timestamp, expiry, and content digest.
4. Atomically apply verified records to the local graph, preserving their
   source-domain ownership and recording deletion tombstones.
5. Exchange `TOPOLOGY_SYNC_ACK` with the resulting complete-graph digest.
6. Keep a subscription open for `NODE_CHANGED`, `LINK_CHANGED`,
   `CONFIG_CHANGED`, `RESERVATION_CHANGED`, and `TOPOLOGY_WITHDRAWN` deltas.

```mermaid
sequenceDiagram
    participant PA as Packet A DSO
    participant O as Optical DSO
    participant PB as Packet B DSO

    PA->>O: mTLS + Agent Card
    O-->>PA: mTLS + Agent Card
    PA->>O: TOPOLOGY_DIGEST
    O-->>PA: TOPOLOGY_DIGEST
    PA->>O: Request missing snapshot/deltas
    O-->>PA: Signed topology/configuration records
    PA->>PA: Verify origin, signature, sequence, expiry
    PA->>PA: Apply atomically and calculate graph digest
    PA-->>O: TOPOLOGY_SYNC_ACK
    O->>PB: Repeat topology synchronization
    PA->>PB: Direct mesh synchronization
    Note over PA,PB: All DSOs converge on the same graph digest
```

The initial full mesh lets Packet A, Optical, and Packet B receive every
domain's snapshot directly. Deltas can also be relayed through a currently
reachable peer when a direct control-plane link is unavailable; the original
owner signature and sequence number remain unchanged. A DSO rejects an update
from a non-owner, a stale sequence, an invalid signature, or an incompatible
schema. It marks affected graph data stale when its advertised validity period
expires and cannot use stale data to commit a service change.

An example link/configuration advertisement is:

```json
{
  "message_type": "TOPOLOGY_DELTA",
  "origin_domain": "optical",
  "origin_sequence": 418,
  "topology_revision": "optical-418",
  "changes": [{
    "kind": "LINK_CHANGED",
    "link": {
      "link_id": "optical:r2--r3:channel-17",
      "a_interface": "optical:r2:line-2",
      "z_interface": "optical:r3:line-3",
      "layer": "optical",
      "capacity_gbps": 400,
      "latency_ms": 1.8,
      "operational_state": "up"
    },
    "configuration": {
      "revision": "cfg-98",
      "desired": {"channel": 17, "modulation": "16QAM"},
      "observed": {"channel": 17, "qot_state": "acceptable"}
    }
  }],
  "expires_at": "2026-09-16T15:00:00Z",
  "signature": "owner-domain-signature"
}
```

This graph replaces the earlier abstract-only topology boundary. It gives every
agent the relationships needed to reason about end-to-end paths, impacted
services, alternative routes, shared-risk links, and configuration compatibility
before it negotiates. The graph is read-only outside the originating domain;
topology visibility never changes controller-write authority.

## Database ownership and replication

Each networking domain operates its own DSO database. There is no single shared
database connection and no central writer. The DSOs synchronize selected state
through signed A2A messages, so every database contains a complete logical view
of the multi-domain topology while the originating domain remains authoritative
for its own records.

```mermaid
flowchart LR
    subgraph DA[Packet A domain]
        ADB[(Packet A DSO database)]
        AOWN[Authoritative Packet A\ntopology, configuration,\ntelemetry, receipts, policy]
        ADB --- AOWN
    end
    subgraph DO[Optical domain]
        ODB[(Optical DSO database)]
        OOWN[Authoritative Optical\ntopology, configuration,\ntelemetry, receipts, policy]
        ODB --- OOWN
    end
    subgraph DB[Packet B domain]
        BDB[(Packet B DSO database)]
        BOWN[Authoritative Packet B\ntopology, configuration,\ntelemetry, receipts, policy]
        BDB --- BOWN
    end
    ADB <-->|Signed topology, contracts,\nquality signals, learning releases| ODB
    ODB <-->|Signed topology, contracts,\nquality signals, learning releases| BDB
    ADB <-->|Signed topology, contracts,\nquality signals, learning releases| BDB
```

Every DSO database has these logical partitions:

| Partition | Contents | Writer |
|---|---|---|
| Local authoritative state | The domain's source topology/configuration records, raw telemetry, local policy, private cost model, controller credentials, and local controller receipts | Its owning DSO only |
| Federated topology replica | Signed nodes, interfaces, links, relationships, and approved configuration records from all three domains, including the owner's own records | Owner writes; peer DSOs apply verified replicas only |
| Shared contract replica | Signed service-contract revisions, offers, acceptances, incident coordination leases, reservation summaries, and verification summaries | The originating signer writes each record; every DSO verifies and stores it |
| Swarm and learning replica | Signed quality signals, candidate summaries, verified feedback, and approved learning releases | The origin DSO writes; peers accept or reject after verification |
| Vector RAG index | Locally embedded runbooks, policies, MCP tool documentation, change/incident records, approved learning releases, and accepted peer knowledge releases | Each DSO indexes its own authorized corpus locally |
| GraphRAG projection | Federated topology/configuration graph enriched with service, path, reservation, evidence, incident, candidate, controller-receipt, and outcome relationships | Source records retain their owner; each DSO materializes its own queryable graph view |
| Local audit journal | Full local evidence, policy decisions, controller request/response details, and immutable trace links | Its owning DSO only |

The result is **logical sharing with physical separation**. For example, the
Optical DSO publishes a signed configuration record for a channel and every DSO
stores the same read-only replica. Only the Optical DSO can revise that channel,
ask its optical controller to reserve it, or commit a change.

### Recommended concrete database profile

Use this stack in every domain:

| Store | Technology | Authoritative data |
|---|---|---|
| DSO system of record and vector RAG | PostgreSQL with `pgvector` | Service contracts, A2A journal/outbox, topology/configuration source records and replicas, reservations, controller receipts, policies, audit records, RAG chunks, embeddings, and provenance. |
| Telemetry | PostgreSQL time-partitioned tables; TimescaleDB where sustained telemetry volume warrants it | Packet, optical, controller, and endpoint measurements. |
| GraphRAG projection | Neo4j | Revision-bound topology plus service/path/resource/configuration/evidence/incident/candidate/reservation/outcome relationships. |
| Evidence archive | Optional domain-local object storage | Large raw evidence such as PCAPs, snapshots, traces, and source documents; PostgreSQL stores digests and references. |

PostgreSQL is the DSO's transactional system of record. `pgvector` keeps vector
embeddings with the source/provenance fields that govern RAG retrieval; an HNSW
index is the appropriate initial approximate-nearest-neighbor index. Neo4j is a
separate read-optimized graph projection for GraphRAG traversal. A committed
PostgreSQL outbox event materializes source changes into Neo4j. The materializer
preserves source revision and digest, and `graphrag_subgraph_retrieval` rejects a
projection that does not match the current graph/service decision.

```mermaid
flowchart LR
    A2A[Verified A2A artifacts] --> PG[(PostgreSQL + pgvector\nDSO system of record and RAG)]
    MCP[Controller MCP results\nand telemetry] --> PG
    PG -->|committed outbox event| N[(Neo4j\nGraphRAG projection)]
    O[(Optional domain-local\nobject storage)] --> PG
    PG --> R[RAG context retrieval]
    N --> GR[GraphRAG subgraph retrieval]
    R --> C[Provenance-bound context]
    GR --> C
```

Topology replicas converge eventually through origin sequence numbers, signed
snapshots, deltas, and graph digests. Service-changing operations demand a
stronger boundary: each DSO must have the same contract revision, valid current
graph/configuration digest, and valid local reservation before commit. The
distributed saga and signed receipts provide cross-domain coordination; they do
not require a distributed ACID transaction or a shared database.

## RAG and GraphRAG knowledge layer

Each domain AI agent has a local **vector database** and a local **GraphRAG
projection**. These are retrieval systems owned by the DSO's domain database
boundary; they do not introduce a central knowledge service.

```mermaid
flowchart LR
    Q[Intent, assurance event,\nor operator question] --> DSO[DSO retrieval workflow]
    DSO --> V[(Vector DB\nsemantic RAG)]
    DSO --> G[(Graph DB / GraphRAG\nrelationship traversal)]
    V --> X[Context package with source IDs]
    G --> X
    X --> AI[AI reasoning / explanation]
    AI --> VG[Deterministic grounding gate]
    VG --> P[Policy and transaction workflow]
```

The vector database indexes unstructured or semi-structured material that is
useful for semantic retrieval: operating procedures, network and service design
documents, policy text, YANG/OpenConfig/T-API model documentation, Controller
MCP tool descriptions, change records, incident reports, evidence summaries,
and approved learning releases. Each chunk carries source ID, owner, schema or
document version, authorization classification, issue/expiry time, and digest.

The GraphRAG projection is a queryable knowledge graph rooted in the
FederatedTopologyGraph. It adds service-to-path, path-to-resource,
resource-to-configuration, observation-to-entity, incident-to-suspicion,
candidate-to-action, reservation-to-resource, and controller-receipt-to-action
relationships. It answers questions that require traversal rather than semantic
similarity, for example:

- Which active services cross this failed optical channel or packet link?
- Which alternative paths satisfy the current QoS budget and avoid the incident?
- Which configuration revisions, reservations, and controller changes produced
  this measured degradation?

RAG and GraphRAG work together in a retrieval workflow: resolve relevant graph
entities from the current contract or incident; traverse a revision-bound,
bounded subgraph; retrieve semantically relevant documents and evidence chunks;
then give the AI agent a context package that cites every source. A deterministic
grounding gate rejects unsupported citations, stale records, out-of-scope
documents, and output that proposes an action outside the verified candidate
set.

Topology/configuration and service facts arrive through their existing signed
A2A extensions and are materialized locally into the graph projection. A domain
may share an approved knowledge release through `knowledge-federation/v1`; each
receiving DSO verifies authorization, provenance, digest, and expiry before
indexing it. Vector embeddings and private raw documents are not implicitly
replicated merely because a topology record is shared.

### Deterministic graph algorithms

GraphRAG retrieves the relevant graph context; deterministic algorithms then
answer the exact path and impact questions needed by the DSO. Run them against
an in-memory or queryable graph snapshot bound to one verified graph revision,
never against an unbounded live controller query.

| Algorithm | Use in the DSO workflow |
|---|---|
| Breadth-first search (BFS) | Check whether source and destination remain reachable, calculate hop-based neighborhoods, and find services/resources immediately affected by a node, link, channel, or configuration incident. |
| Depth-first search (DFS) | Enumerate bounded simple paths, detect cycles, and identify alternate topology branches. The DFS depth, candidate count, and visited-node budget are explicit policy limits. |
| Dijkstra or constraint-based shortest path | Rank reachable paths by latency, cost, capacity, loss, risk, QoT, and configuration compatibility after BFS/DFS has established the feasible scope. |
| K-shortest disjoint path search | Produce diverse primary/backup candidates that avoid a failed resource or shared-risk group. |

```mermaid
flowchart LR
    G[Verified GraphRAG subgraph\nrevision and digest] --> B[BFS reachability\nand impact scope]
    B --> D[Bounded DFS\nsimple-path enumeration]
    D --> C[Constraint checks\ncapacity, QoS, configuration]
    C --> R[Shortest-path and\ndisjoint-path ranking]
    R --> S[Bounded swarm exploration]
    S --> P[Verified local candidates]
```

For example, an optical-channel impairment first triggers BFS from the affected
channel to identify active dependent services and adjacent packet attachments.
Bounded DFS enumerates alternate end-to-end paths that avoid the impacted
resource. Constraint-based ranking discards paths that cannot meet the SLA or
configuration rules. Only then do swarm scouts and game-theoretic bargaining
consider the remaining candidates.

## DSO LangGraph design

Each DSO runs three LangGraphs over one durable local state store. Separating
them keeps topology replication, service provisioning, and assurance/recovery
as different event paths. They share the same `FederatedTopologyGraph`, but a
topology update cannot cause a controller change by itself.

```mermaid
flowchart LR
    T[Topology federation graph] --> G[(DSO durable state\nFederated Topology Graph\nservice and reservation journal)]
    S[Service lifecycle graph] --> G
    A[Assurance and recovery graph] --> G
    G --> M[Local Controller MCP Server]
    M --> C[Local SDN controller]
    G <--> P[Peer DSOs]
```

### 1. Topology federation graph

This graph runs on a peer handshake, snapshot request, or topology/configuration
delta. It is the agent equivalent of maintaining an OSPF link-state database.

| Node | Responsibility |
|---|---|
| `topology_event_ingest` | Classify a handshake, snapshot, delta, withdrawal, or resynchronization request and bind its peer/correlation IDs. |
| `peer_identity_gate` | Verify mTLS identity, Agent Card capability, peer authorization, and supported schema versions. |
| `topology_message_verifier` | Validate message schema, origin-domain ownership, signature, sequence number, expiry, and content digest. |
| `topology_reconciler` | Compare advertised revisions with the local revision vector and request the required snapshot or missing delta range. |
| `graph_apply` | Atomically apply an owner-signed node, interface, link, relationship, configuration, or tombstone change. |
| `graph_integrity_gate` | Validate endpoint existence, layer compatibility, graph connectivity, configuration references, and the resulting graph digest. |
| `topology_impact_analysis` | Identify services, reserved resources, paths, and pending negotiations affected by the change. |
| `topology_ack_and_journal` | Persist the replica revision, emit a signed synchronization acknowledgement, and enqueue impacted services for assurance. |

### 2. Service lifecycle graph

This graph runs when a local user submits intent or when a peer sends a service
contract event. It replaces the single central Service Orchestrator with the
same bounded lifecycle in every domain.

| Node | Responsibility |
|---|---|
| `service_event_ingest` | Accept a local intent or peer contract event and create/load the correlation-specific service record. |
| `identity_and_entitlement_gate` | Authenticate the user or peer and verify tenant, endpoint, and service authority. |
| `service_context_load` | Load the local service state, prior receipts, reservation state, peer lifecycle state, and current graph digest. |
| `topology_freshness_gate` | Require the topology/configuration revisions referenced by the request to be present, valid, and not stale. |
| `rag_context_retrieval` | Retrieve authorized, semantically relevant runbooks, policies, controller-tool documentation, incidents, and learning releases from the local vector database. |
| `graphrag_subgraph_retrieval` | Traverse the revision-bound graph projection for relevant service, path, resource, configuration, evidence, and incident relationships. |
| `retrieval_grounding_gate` | Bind context to its sources and reject stale, unauthorized, out-of-scope, or unsupported retrieval before AI reasoning. |
| `graph_reachability_and_impact` | Run BFS over the verified graph snapshot to establish reachability and affected-resource/service scope. |
| `bounded_path_enumeration` | Run policy-bounded DFS and disjoint-path search to produce diverse simple path alternatives. |
| `constraint_path_ranking` | Apply deterministic capacity, SLA, risk, QoT, and configuration constraints before swarm exploration. |
| `qos_budget_derivation` | Turn the end-to-end intent into local bandwidth, latency, loss, availability, and deadline contributions. |
| `path_and_dependency_analysis` | Traverse the federated graph to identify the selected path, domain handoffs, shared-risk resources, and configuration dependencies. |
| `swarm_state_refresh` | Read current signed swarm-quality signals for the graph entities and service class under consideration. |
| `swarm_candidate_exploration` | Run bounded virtual scouts over feasible packet-optical paths and resource/configuration combinations; this is planning only. |
| `swarm_candidate_aggregation` | Aggregate scouts into a small, diverse, deduplicated candidate set with reproducible score components. |
| `local_candidate_generation` | Generate only controller-feasible local actions and predicted QoS effects for this DSO's domain. |
| `advisory_reasoning` | Optionally use the AI model to explain evidence, rank alternatives, or propose a counteroffer; it cannot add an action outside the deterministic candidate set. |
| `candidate_verification` | Ground every candidate in current graph/telemetry/configuration evidence and reject unsupported claims. |
| `local_policy_selection` | Apply local policy, cost, risk, disruption, and rollback rules to select an offer or counteroffer. |
| `local_utility_evaluation` | Calculate this domain's utility and disagreement value for each policy-approved candidate. |
| `peer_contract_negotiation` | Exchange signed bargaining offer, counteroffer, acceptance, and rejection messages with the DSOs on the selected path. |
| `bargaining_solution_gate` | Require a mutually beneficial agreement plus matching contract revision, graph digest, path, QoS budget, and peer acknowledgements. |
| `local_reservation` | Ask the local controller to create an idempotent, time-bound reservation for its named operation. |
| `reservation_barrier` | Wait for valid reservation receipts from every affected DSO; route to expiry or compensation on rejection/timeout. |
| `commit_authorization_gate` | Recheck local policy, graph freshness, contract revision, reservation validity, and controller state immediately before commit. |
| `controller_transaction` | Use the local Controller MCP Server to commit or roll back the named transaction, then persist the returned local receipt. |
| `service_verification` | Evaluate local and border measurements, then exchange signed verification summaries with the peers. |
| `service_outcome_journal` | Record `VERIFIED`, `FAILED`, `EXPIRED`, or `ROLLED_BACK`, notify the initiating DSO, and create an immutable decision trace. |

```mermaid
flowchart LR
    E[Service event] --> I[Identity and context gates]
    I --> F[Topology freshness and QoS budget]
    F --> K[RAG and GraphRAG\nprovenance-bound context]
    K --> GA[BFS, bounded DFS,\nand constraint path ranking]
    GA --> D[Path and dependency analysis]
    D --> S[Swarm exploration and aggregation]
    S --> C[Local candidates]
    C --> V[Evidence and policy verification]
    V --> U[Local utility evaluation]
    U --> N[Peer bargaining]
    N --> B{Mutual agreement?}
    B -->|No| J[Journal rejection or expiry]
    B -->|Yes| R[Reserve locally]
    R --> G{All receipts valid?}
    G -->|No| J
    G -->|Yes| X[Commit through local controller]
    X --> Q[Verify service]
    Q --> J
```

### 3. Assurance and recovery graph

This graph runs on local telemetry, a peer status event, a topology impact event,
or a verification failure. It uses the same candidate, negotiation, reservation,
commit, and outcome nodes as the service lifecycle graph rather than creating a
second controller path.

| Node | Responsibility |
|---|---|
| `assurance_event_ingest` | Receive telemetry, peer evidence, topology-impact, or service-verification events. |
| `evidence_normalization` | Convert source measurements to typed, timestamped evidence bound to graph entities and configuration revisions. |
| `service_health_evaluation` | Determine whether the domain's contribution and the received end-to-end evidence meet the contract. |
| `incident_creation_or_update` | Create, deduplicate, or update the domain-local incident and bind it to the affected graph revision. |
| `fault_and_impact_reasoning` | Identify probable local and cross-domain dependencies using the graph and evidence; optional AI output remains advisory. |
| `remediation_dispatch` | Re-enter `local_candidate_generation` and the shared negotiation/transaction path, or escalate when no safe candidate exists. |
| `assurance_trace_and_journal` | Persist the evidence, diagnosis, peer exchanges, action receipts, and final health outcome. |

The durable DSO state shared by these graphs includes the topology revision
vector and graph digest, service contract revision, correlation ID, local and
peer lifecycle states, candidate-set digest, reservation receipts, controller
receipts, evidence references, and immutable audit trace. Packet A, Optical,
and Packet B use the same node names; their local candidate, controller,
telemetry, and configuration adapters differ by domain.

## Per-domain closed loop

Every DSO runs its own continuous MAPE-K loop—Monitor, Analyze, Plan, Execute,
with shared Knowledge. It is scheduled at a domain-defined interval and also
wakes immediately on local telemetry, a topology/configuration delta, a peer
status event, a reservation expiry, or a failed verification.

```mermaid
flowchart LR
    T[Timer or event] --> M[Monitor local telemetry\nand peer summaries]
    M --> K[Refresh federated graph,\ncontract and local state]
    K --> A[Assess local SLA contribution\nand diagnose impact]
    A -->|Healthy| J[Journal outcome\nand enqueue learning]
    A -->|Violation or predicted risk| P[Generate and verify\nlocal candidates]
    P --> S{Affects a\nshared service?}
    S -->|Yes| N[Negotiate/bargain\nwith peer DSOs]
    S -->|No| G[Local policy gate]
    N --> G
    G --> R[Reserve and commit\nthrough local controller]
    R --> V[Verify locally and\nexchange verification summaries]
    V --> J
    J --> T
```

| Loop stage | DSO behavior |
|---|---|
| Monitor | Read domain-scoped telemetry, controller state, service probes, configuration state, and signed peer summaries. Packet DSOs observe loss, latency, queues, utilization, and route state; the Optical DSO observes spectrum, QoT/gOSNR, transponder, and ROADM state. |
| Analyze | Normalize evidence, refresh the federated graph, assess the local contribution to every active service, correlate local changes with peer evidence, and classify health, degradation, or risk. |
| Plan | Traverse the full topology graph, generate controller-feasible local candidates, calculate local QoS/cost/risk utility, and determine whether the action can affect another domain's service. |
| Execute | For an isolated local action, use the local policy gate. For an action affecting a shared service, complete bargaining and reservation with every affected DSO first. The owning DSO alone invokes its Controller MCP Server's named prepare/commit/rollback operation. |
| Verify | Collect fresh local and border measurements, exchange signed verification summaries, and mark the contract healthy only when its applicable end-to-end evidence satisfies the agreed SLA. |
| Knowledge | Persist topology/configuration revisions, service contracts, evidence, incidents, offers, reservations, controller receipts, outcomes, and approved learning releases. |

The normal closed-loop path can finish with no action: a healthy assessment
records fresh evidence and returns to monitoring. An AI recommendation cannot
skip from Analyze to Execute; it must pass candidate verification, local policy,
cross-domain bargaining when applicable, reservation, commit authorization, and
verification.

### Coordinating three concurrent loops

All three loops may detect the same service problem. To avoid contradictory
actions or negotiation storms, each service incident has a short-lived,
signed **coordination lease**. The first DSO to create the incident proposes a
lease bound to the contract revision and graph digest. Peer DSOs acknowledge it
only if they see the same current service state. The lease holder coordinates
the bargaining conversation; it does not gain authority over peer controllers.

Every DSO retains the right to reject an offer, withdraw a reservation, or
start a new incident after the lease expires. Controller idempotency keys,
candidate digests, cooldown timers, hysteresis/deadbands, and a maximum action
rate per service prevent repeated oscillating changes. A topology change,
contract revision, stale graph, failed peer acknowledgement, or verification
failure invalidates the active plan and returns the loops to Analyze.

### 4. Continual-learning graph

Each DSO also runs an asynchronous **Domain Learning Graph**. The
`service_outcome_journal` and `assurance_trace_and_journal` nodes enqueue a
learning job after a terminal service outcome; they never wait for learning
before completing a service request or recovery action.

```text
decision_trace_ingest → peer_outcome_correlation → comparable_trace_retrieval
→ novelty_gate → hypothesis_generation → provenance_validator
→ experiment_planner → safe_experiment_runner → evaluation_gate
→ promotion_gate → publish_learning_release or reject_or_revoke
```

```mermaid
flowchart LR
    D[Verified decision trace] --> C[Correlate peer outcomes]
    C --> R[Retrieve comparable traces]
    R --> N{Novel and sufficient evidence?}
    N -->|No| X[Reject or revoke]
    N -->|Yes| H[Generate hypothesis]
    H --> P[Validate provenance]
    P --> E[Offline replay, digital twin, or shadow experiment]
    E --> V[Evaluate calibration and safety]
    V --> G{Promotion gate}
    G -->|L0, L1, or reviewed L2| L[Signed learning release]
    G -->|Rejected| X
    L --> A[Advisory input to future loops]
```

| Node | Responsibility |
|---|---|
| `decision_trace_ingest` | Read the immutable local service, negotiation, topology/configuration, controller-receipt, and verification trace. |
| `peer_outcome_correlation` | Match signed peer outcome summaries to the same service contract, graph digest, and time window. |
| `comparable_trace_retrieval` | Retrieve prior outcomes with comparable topology, configuration, traffic, and service conditions. |
| `novelty_gate` | Stop duplicate, too-small, stale, or contradicted learning jobs. |
| `hypothesis_generation` | Propose a bounded explanation or prediction improvement, such as a QoS forecast, risk calibration, cost calibration, or negotiation-ranking feature. |
| `provenance_validator` | Require attributable evidence, valid graph/configuration revisions, and a reproducible training/evaluation dataset. |
| `experiment_planner` | Define an offline replay, digital-twin simulation, or shadow evaluation. It cannot schedule an uncontrolled live experiment. |
| `safe_experiment_runner` | Run only the approved offline or shadow experiment and preserve the inputs and result. |
| `evaluation_gate` | Measure calibration, prediction error, safety regressions, bargaining outcome quality, and sample sufficiency against a held-out baseline. |
| `promotion_gate` | Decide whether the result can remain observational, enter shadow ranking, require operator review, or be rejected/revoked. |
| `publish_learning_release` | Sign and version the approved finding/model release with its scope, expiry, evidence digest, and applicability conditions. |
| `reject_or_revoke` | Preserve the failed result and withdraw a prior release that is no longer valid. |

The three DSOs learn locally from the same end-to-end outcome but contribute
different evidence: Packet A and Packet B learn packet path, queue, and
endpoint behavior; Optical learns spectrum, QoT, transponder, and transport
behavior. They exchange signed **learning releases**, not unrestricted model
writes. A release binds its model/finding to topology and configuration
revisions, service type, evidence digest, measured result, confidence, and
expiry. A receiving DSO independently verifies and either accepts the release
for its own advisory use or ignores it.

Learning has three promotion levels:

| Level | Permitted use |
|---|---|
| L0 — observational | Publish measured correlations and calibration facts; no service decision changes. |
| L1 — shadow/advisory | Rank already feasible candidates in `advisory_reasoning` or estimate cost/risk; deterministic policy still makes the decision. |
| L2 — reviewed policy input | Supply a bounded parameter update to an approved policy/risk model after operator review and replay evidence. |

No learning release may create a controller action, modify a topology/configuration record owned by another DSO, lower a hard safety constraint, or commit a service. The service lifecycle graph still performs candidate verification, bargaining consensus, reservation, commit authorization, and controller transaction independently.

## Game-theoretic coordination

The three DSOs are separate owners, so path feasibility alone does not imply
agreement. Model Packet A, Optical, and Packet B as players in a cooperative
bargaining game. The Federated Topology Graph gives all players the same view of
what can be connected; each player still evaluates the impact on its own
capacity, risk, operational policy, and commercial terms.

For a joint action `a = (a_packet_a, a_optical, a_packet_b)`, let `F(G)` be the
set of actions feasible in the replicated topology graph `G`. An action enters
`F(G)` only when it has continuous end-to-end connectivity, configuration
compatibility, sufficient capacity, valid resource reservations, and no hard
policy violation. Each domain calculates a local utility:

```text
U_i(a, x_i) = SLA/revenue benefit_i(a) + settlement_i(x_i)
              - resource cost_i(a) - disruption_i(a)
              - risk_i(a) - policy penalty_i(a)
```

`x_i` is an optional settlement, price, or internal credit associated with the
contract. In a research prototype it can be a virtual credit rather than a
payment. Each DSO also has a disagreement value `d_i`: normally retain the
current service state or reject a new-service request. A contract is admissible
only if it meets the user intent and is individually rational for every domain:

```text
U_i(a, x_i) >= d_i   for Packet A, Optical, and Packet B
```

For equal peers, select the feasible contract using a weighted Nash bargaining
solution:

```text
maximize  sum_i weight_i * log(U_i(a, x_i) - d_i)
subject to a in F(G), U_i(a, x_i) > d_i, and end-to-end SLA satisfied
```

```mermaid
flowchart LR
    F[Feasible path/resource candidates] --> UA[Packet A evaluates utility]
    F --> UO[Optical evaluates utility]
    F --> UB[Packet B evaluates utility]
    UA --> IR{Each utility exceeds fallback?}
    UO --> IR
    UB --> IR
    IR -->|No| CO[Counteroffer or reject]
    CO --> F
    IR -->|Yes| NB[Weighted Nash bargaining]
    NB --> AG[Same signed contract\npath, QoS, price, expiry]
    AG --> RS[Reservation phase]
```

The weights are a published service policy, such as equal weight for three
operators or higher weight for a premium tenant's ingress operator. They must
be contract fields, never model-generated values. This method favors a service
option that improves every participating domain over its fallback, rather than
choosing the option with the highest benefit to only one domain.

### Cost quantification

Every DSO calculates cost in one agreed unit: a real currency for a commercial
deployment or a `service-credit` for a research prototype. Do not use an
unscaled score as cost, because the bargaining function must compare cost,
risk, and settlement in consistent units.

For domain `i` and a local candidate `a`, calculate the local resource cost as:

```text
C_i(a) = C_capacity + C_opportunity + C_operation + C_energy + C_risk
```

| Component | Quantification |
|---|---|
| `C_capacity` | Reserved resource quantity × reservation duration × domain unit rate. Packet domains use committed bandwidth/port/queue units; the optical domain uses spectrum slots, wavelength/transponder use, and optionally fiber distance. |
| `C_opportunity` | The cost of reducing future sellable capacity. Use a convex utilization function, for example `reference_cost × (utilization_after^p - utilization_before^p)` where `p > 1`; scarce links therefore cost more than idle links. |
| `C_operation` | Fixed cost for each approved controller transaction plus expected rollback/validation effort. It is zero for retain-current. |
| `C_energy` | Expected incremental watts × reservation hours × local energy rate. |
| `C_risk` | Probability that the change or resource fails × the locally defined service/rollback impact cost. Historical failure data can calibrate the probability. |

The DSO keeps its unit rates, utilization curve, and risk model private. It
publishes a signed **quote** containing the total cost, optional margin, total
requested settlement, cost-model revision, currency, expiry, and resource
commitment. Price and cost are distinct:

```text
quoted settlement_i = C_i(a) + approved margin_i
utility_i = settlement_i - C_i(a) + local SLA/value benefit_i
```

The user intent should therefore contain `maximum_total_cost` and `currency`.
The bargaining solution must satisfy that budget as well as the SLA and the
individual-rationality condition. In a research demo, set the currency to
`service-credit`, configure fixed rates in each domain, and record the quote in
the service contract; no payment system is required.

For example, a two-hour 1 Gbps request might produce these service-credit
quotes: Packet A costs 14 credits and quotes 16, Optical costs 52 and quotes
58 because it reserves scarce spectrum/transponder capacity, and Packet B costs
13 and quotes 16. The end-to-end quoted price is 90 credits. A user budget below
90 forces the DSOs to negotiate a cheaper feasible path or reject the request.

```mermaid
flowchart LR
    B[User budget: 90 credits] --> PA[Packet A quote: 16]
    B --> O[Optical quote: 58]
    B --> PB[Packet B quote: 16]
    PA --> T[Total quote: 90]
    O --> T
    PB --> T
    T --> D{Within budget and SLA?}
    D -->|Yes| N[Eligible for bargaining agreement]
    D -->|No| C[Counteroffer, alternate swarm path, or reject]
```

The reference platform's Max-Sum DCOP remains useful for searching candidate
combinations and checking pairwise compatibility. It assumes a common global
utility, so it should be used before bargaining as the feasibility/option
enumeration mechanism. Nash bargaining is the agreement mechanism for separate
owners with different utilities.

## Swarm optimization layer

The three DSOs can act as a policy-bounded AI swarm. Swarm optimization is used
to discover and rank feasible end-to-end alternatives in the Federated Topology
Graph; it does not select a commercial agreement or control a network device.

Ant Colony Optimization (ACO) is the primary swarm method because path and
spectrum selection are discrete graph problems. Each DSO launches bounded
virtual **scouts** during `swarm_candidate_exploration`. A scout traverses only
currently feasible nodes, links, interfaces, spectrum resources, and
configuration combinations. It returns a candidate path and a score rather than
touching the data plane.

For an eligible edge `i → j`, a scout chooses its next hop using a combination
of historical path quality (pheromone) and current measured quality (heuristic):

```text
P(i → j) = [pheromone(i,j)^alpha × heuristic(i,j)^beta]
           / sum over all eligible next hops
```

The heuristic uses normalized capacity headroom, latency, packet loss, jitter,
availability, optical QoT/gOSNR, risk, and quoted cost. Every signal is bound to
an entity ID, graph/configuration revision, service class, timestamp, expiry,
origin DSO, and signature. Packet A and Packet B publish packet-path and queue
signals; Optical publishes transport, spectrum, and QoT signals.

After a verified service outcome, the owning DSO updates the quality of the
resources used by that candidate. Pheromone decays over time so old success does
not override current congestion or optical degradation:

```text
pheromone(edge) = (1 - evaporation_rate) × previous_pheromone
                  + verified_outcome_reward
```

Only verified measurement outcomes update pheromone. Unverified AI assertions,
failed reservations, stale topology, and rejected candidates add no positive
reinforcement. The continual-learning graph can calibrate the heuristic weights
and outcome reward function, but those updates use the same L0/L1/L2 promotion
rules as other learned releases.

```mermaid
flowchart LR
    Q[Signed quality signals\ncapacity, QoS, QoT, risk] --> S[Shared swarm state]
    G[Federated topology graph] --> E[Bounded virtual scouts]
    S --> E
    E --> A[Aggregate diverse paths\nand resource candidates]
    A --> V[Candidate verification]
    V --> B[Game-theoretic bargaining]
    B --> R[Reserved and committed service]
    R --> O[Verified outcome]
    O --> P[Pheromone reward or decay]
    P --> S
```

The swarm protocol has three signed message types:

| Message | Contents | Use |
|---|---|---|
| `SWARM_QUALITY_SIGNAL` | Entity/link ID, QoS/QoT measurements, capacity, risk, cost class, graph digest, expiry | Replicate current local quality into every DSO's swarm state. |
| `SWARM_CANDIDATE` | Candidate path/resource tuple, graph/configuration revisions, score vector, evidence references, TTL | Share a planning result for independent verification and local candidate construction. |
| `SWARM_FEEDBACK` | Verified outcome, reward/penalty, affected resources, evidence and service-contract digests | Update short-lived pheromone/quality state after service verification. |

Scouts are bounded by a maximum hop count, maximum candidates, time budget,
allowed resource classes, and minimum diversity threshold. The aggregation node
keeps a small set of materially different candidates rather than repeatedly
returning variations of the same congested path. For continuous choices, such as
bandwidth splitting, modulation/power parameters, or queue-share allocation,
the same layer may use Particle Swarm Optimization after ACO has selected the
discrete path.

The swarm result enters `local_candidate_generation`, then follows the normal
candidate verification, local policy, Nash bargaining, reservation, commit, and
verification path. It therefore answers **which options merit negotiation**;
game theory answers **which option independent owners accept**; each DSO's
controller gate answers **whether the local operation may run**.

### Bargaining message and decision rules

Each `BARGAINING_OFFER` binds the graph digest and contract revision and carries
the selected per-domain action IDs, predicted end-to-end QoS, reservation TTL,
rollback capability, settlement/credit proposal, and signed accept-by deadline.
It does not need to disclose a domain's private utility coefficients. A peer
independently evaluates the offer using its own utility function and responds
with `ACCEPT`, `COUNTEROFFER`, or `REJECT`.

The `bargaining_solution_gate` accepts a contract only when all three DSOs have
signed the exact same action tuple, graph digest, configuration revisions, QoS
budget, settlement, and expiry. It routes a rejection, expired offer, topology
change, or reservation failure to `service_outcome_journal` or compensating
rollback. No controller reservation or commit follows an incomplete agreement.

## Intent and service contract

An intent should state the desired outcome, never a path or a device command.
For example:

```json
{
  "intent_id": "intent-01J...",
  "tenant_id": "customer-42",
  "source": {"domain": "packet-a", "endpoint": "server-a"},
  "destination": {"domain": "packet-b", "endpoint": "server-b"},
  "service_type": "l3vpn",
  "qos": {
    "minimum_bandwidth_mbps": 1000,
    "maximum_latency_ms": 20,
    "maximum_packet_loss_ratio": 0.0001,
    "availability_target": 0.9999
  },
  "deadline": "2026-09-16T14:30:00Z"
}
```

The initiating DSO authenticates the user, checks entitlement for its own
domain, then converts the intent into a versioned `ServiceContract`. A contract
contains only what peers need to decide:

- opaque service, tenant, correlation and contract identifiers;
- ingress and egress border attachment identifiers;
- requested QoS envelope and each domain's budget/contribution;
- a candidate's capacity, cost class, predicted QoS contribution, risk,
  reservation lifetime, and rollback support;
- contract revision, issue/expiry time, nonce, sender identity, and signature.

It references the current signed topology and configuration revisions rather
than embedding a second copy. Controller credentials, private keys, and
LLM-generated configurations are never transferred.

End-to-end estimates compose conservatively: throughput is bounded by the
smallest domain contribution, latency is additive, and loss combines as
`1 - product(1 - domain_loss)`. An offered contract must meet the full intent
before it can be committed.

## Negotiation protocol

Use A2A HTTP+JSON for peer discovery and every DSO-to-DSO message. Each agent
publishes an Agent Card describing its identity, supported contract version,
border capabilities, A2A extensions, and endpoint. Use mTLS workload identities
and signed artifacts in a multi-operator deployment.

```mermaid
sequenceDiagram
    participant User
    participant PA as Packet A agent + DSO
    participant O as Optical agent + DSO
    participant PB as Packet B agent + DSO
    participant CA as Packet A controller
    participant CO as Optical controller
    participant CB as Packet B controller

    User->>PA: Submit intent
    PA->>O: SERVICE_REQUEST (scoped QoS envelope)
    O->>PB: SERVICE_REQUEST (remaining QoS envelope)
    PB-->>O: CAPABILITY_OFFER / COUNTEROFFER
    O-->>PA: CAPABILITY_OFFER / COUNTEROFFER
    PA->>O: PROPOSE_CONTRACT
    O->>PB: PROPOSE_CONTRACT
    PB-->>O: RESERVE_ACK or REJECT
    O-->>PA: RESERVE_ACK or REJECT
    PA->>CA: Reserve local named option
    O->>CO: Reserve local named option
    PB->>CB: Reserve local named option
    PA->>O: COMMIT
    O->>PB: COMMIT
    PB->>CB: Commit its named option
    O->>CO: Commit its named option
    PA->>CA: Commit its named option
    PB-->>O: Local verification summary
    O-->>PA: Local verification summary
    CA-->>PA: Local verification result
    PA-->>User: Active / failed / rolled back
```

The protocol states are `DISCOVERED`, `OFFERED`, `COUNTERED`, `AGREED`,
`RESERVED`, `COMMITTED`, `VERIFIED`, `REJECTED`, `EXPIRED`, and `ROLLED_BACK`.
Every message is idempotent under its correlation ID and includes an expiry.
Expired, replayed, unsigned, or revision-mismatched messages are rejected.

Reservation is intentionally separate from commit. Each domain first creates a
short-lived, recoverable reservation for a locally named candidate. Commit can
proceed only when every required reservation is valid. A failure before
verification releases reservations or runs each controller's compensating
rollback operation. A controller reports its local receipt; no peer receives
write access to it.

## What each agent reasons about

An agent can use an LLM to interpret a natural-language intent, summarize local
telemetry, or explain a counteroffer. The LLM is advisory. Deterministic code
must enforce identity, policy, schema validation, QoS arithmetic, freshness,
candidate feasibility, reservation, and controller authorization.

Each agent's DSO produces a small candidate set such as `retain`, `provision path X`,
or `upgrade bandwidth tier Y`. Every candidate has evidence, feasibility,
predicted QoS effect, uncertainty, cost, disruption, risk, reservation TTL,
and rollback capability. The DSOs reason over the same replicated graph and
negotiate the selected end-to-end path, configuration compatibility, and terms;
each DSO still translates the selected path into only its own local operation.

For the first release, choose the best mutually feasible contract with
deterministic ranking:

`utility = SLA benefit - cost - disruption - risk - uncertainty`

Only introduce distributed optimization such as Max-Sum after the contract and
reservation protocol works. In this three-node chain it maps naturally to
Packet A -- Optical -- Packet B, with pairwise compatibility factors. It should
never replace the independent local-policy and controller checks.

## Required safety and trust controls

1. Authenticate users locally; authenticate peer agents with mTLS and allowlisted
   operator identities.
2. Sign every contract and bind it to its issuer, recipient, service, revision,
   nonce, timestamp, and expiry; retain replay records.
3. Give DSOs read-only, scoped inventory and telemetry tools. Give controllers
   only named, allowlisted reserve/commit/rollback operations.
4. Replicate the agreed multi-domain topology and approved configuration state
   through signed owner advertisements. Protect peer exchange with mTLS and
   exclude credentials, keys, and secrets from every topology/configuration
   object.
5. Require local policy approval before reservation and again before commit.
6. Verify the service using measurements at both endpoints and the relevant
   domain-border handoffs. A successful local commit does not prove end-to-end
   service success.
7. Journal every message, offer, reservation, controller receipt, and outcome
   with a tamper-evident correlation chain.

## Implementation order

1. Define Pydantic/JSON Schema contracts for topology objects, configuration
   objects, snapshots, deltas, signatures, and graph digests.
2. Implement three small agent services, each with a DSO state store, a graph
   replica, Agent Card, topology handshake, local policy adapter, and an
   in-memory fake controller for tests.
3. Test full snapshot convergence, incremental link/configuration updates,
   withdrawals, stale data, wrong-owner updates, replay, and graph-digest
   mismatch before implementing service requests.
4. Build the request → offer/counteroffer → reject flow against the replicated
   graph, with no controller writes.
5. Add reserve/commit/rollback adapters for one named local operation in each
   simulated domain, with durable receipts and idempotency.
6. Add endpoint and border verification, then support renegotiation and
   assurance events.
7. Add optional LLM explanation and later bounded distributed optimization;
   neither may widen the action allowlist.

The first working demo should prove one service request from Packet A to Packet
B, a successful three-domain reservation and commit, a remote policy rejection,
and a failed commit that rolls back/reconciles safely.
