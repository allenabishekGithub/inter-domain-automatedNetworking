# Paper 1 — State of the art and novelty assessment

**Search and assessment date:** 24 September 2026.

**Scope:** federated outcome evidence, cross-domain fault diagnosis, selective
disclosure, and recovery decisions in the pre-review Paper 1 design and plan.
The linked [design](design.md) and [research plan](plan.md) now implement the
revised direction.

**Status:** literature assessment and proposed research direction, not measured
results or a claim that a new method has already been established. The follow-up
[TNSM proposal](tnsm-proposal.md) narrows the candidate contribution further.

**Assessment basis:** §§3 and 7 retain the earlier claim set to explain why it
was revised. Those claims are not the current H1–H3 hypotheses. The follow-up
proposal and plan govern current work; this review remains the literature basis.

## 1. Verdict

**Yes, closely related work already exists. The pre-review broad novelty argument
is not defensible.** There are direct precedents for diagnosis across separately
administered networks, hiding internal state while exchanging useful evidence,
domain agents reaching diagnostic conclusions, and collaborative learning from
features held by different optical-network operators. Recent work also addresses
the validity of evidence used to authorize operational actions.

The strongest overlaps are [S01](#s01), [S02](#s02), [S07](#s07), and
[S16–S18](#s16). These are more consequential than papers that merely use the
same agent framework or messaging protocol. In particular, the earlier statement
that federated learning does not cover one party holding labels and another
holding features is contradicted by vertical federated learning [S04](#s04).

**Recommendation: continue Paper 1 only after reframing its contribution and
passing a small comparison experiment.** Investigate a specific method for
requesting sufficient, current evidence to choose a permitted recovery action
or abstain, with explicit costs for disclosure, delay, and wrong actions.
Treat that as a research hypothesis. Neither “minimum evidence” nor “safe
recovery” is automatically new.

I did not establish that another publication implements every detail of this
repository's proposed system. That does not establish novelty: an exact match
of topology, libraries, and protocols is not required for prior work to undermine
a contribution claim. This review narrows the opportunity; it does not certify it.

## 2. Search scope and evidence quality

This is a focused scoping review using public web searches, primary publisher
records, author and university manuscripts, arXiv, IETF, ETSI, and an original
industry demonstration account. It covers foundational work and recent records
available through the assessment date. It contains 25 selected records, including
related papers from the same research family; they are not 25 independent systems.

Representative queries actually used include:

| Search family | Queries |
| --- | --- |
| Administrative boundaries | `multi domain network root cause diagnosis selective evidence sharing 2024 2025 2026`; `cross-domain fault diagnosis 2026 network agents` |
| Learning and optical faults | `Vertical Federated Learning for Failure Localization optical HPSR 2024`; `On Cooperative Fault Management in Multi-Domain Optical Networks Using Hybrid Learning` |
| Evidence acquisition | `network fault diagnosis active probing information gain Rish Brodie 2004 adaptive diagnosis` |
| Agent coordination | `EDAIR Efficient Distributed AI Agent Architecture Multi-Domain Intent Resolution NICT 2025` |
| Recovery and assurance | `network automated remediation uncertainty evidence multi-domain`; `cross-domain evidence recovery network diagnosis`; `SIMAP Service 2026 IETF` |
| Follow-up decision-theory check | `Using action-based hierarchies for real-time diagnosis`; `decision test selection equivalence class active learning diagnosis`; `decision region determination overlapping active learning` |

Title searches and references in retrieved papers extended these searches. In
particular, the 2025 optical work led back to the 2022 cooperative fault-management
paper. Results about rotating machinery were excluded when “domain” meant a
different data distribution or operating condition rather than a network owner.

**Text** means relevant accessible manuscript sections were inspected.
**Abstract** limits the comparison to primary metadata and abstract.
**Mixed** means metadata plus selected indexed manuscript passages; full-text
access was incomplete. A missing feature in an abstract is not evidence that the
paper lacks it. Preprints, Internet-Drafts, a non-normative ETSI Group Report,
and a vendor demonstration are distinguished from peer-reviewed publications.

This is not an exhaustive Scopus/Web of Science systematic review. No invented
screening counts, acceptance probabilities, or completeness percentages are used.
Before submission, extend citation tracing around the closest papers and refresh
the 2026 records. Reported performance numbers are not comparable across datasets,
so this assessment does not rank papers by their headline accuracy.

## 3. What the pre-review proposal claimed

The pre-review system proposed three domain agents, eight joint configurations, local
predictors, a replicated service–infrastructure map, four disclosure conditions,
and receiver outcomes held initially by Packet B. It would diagnose loss and
choose per-owner actions. Its central experiments compare no sharing against
sharing, with local visibility and drift varied.

The implemented packet and optical adapters are a starting point. The domain
agents, disclosure-policy comparison, learning system, and experimental results
are still proposed. This review does not turn those plans into implemented
capabilities. A healthy fixture and unit tests also cannot establish a research
contribution.

Three distinctions matter throughout the comparison:

- **Evidence federation versus federated learning.** Exchanging receiver outcomes
  and fitting independent local predictors is a distributed learning workflow;
  it is not automatically a new VFL algorithm or privacy-preserving training
  protocol. Define exactly what crosses each boundary.
- **Detection, localization, and recovery.** Knowing delivery degraded does not
  identify the faulty segment, and identifying a segment does not prove that a
  particular configuration change will help.
- **Observation versus authority.** Being allowed to see an outcome does not
  authorize changing its owner's equipment. Conversely, owning equipment does
  not guarantee a useful observation or a beneficial action.

## 4. Closest prior work

<a id="s01"></a>
### S01 — Graph digests for cross-domain diagnosis, 2008

William D. Fischer, Geoffrey G. Xie, and Joel D. Young, **Cross-Domain Fault
Localization: A Case for a Graph Digest Approach**, IEEE INM 2008.
**Evidence: Text**, especially Sections III–IV.
[Author manuscript](https://faculty.nps.edu/xie/papers/graph_digest-inm08.pdf).

Domains exchange reduced causal graphs to retain diagnostic value while hiding
internal information. The paper explicitly models inference preservation and
privacy. Its illustrative scenario has a packet customer and optical provider:
local views fail to isolate a service problem, while combined evidence helps.
The evaluation is an algorithm and hypothetical scenario, not a demonstrated
large deployment of autonomous repair.

**Implication:** limited disclosure, complementary local observations, and even
the packet/optical setting already have direct precedent. Our fully replicated
topology also discloses information that this work tries to hide. A new paper
must state which information its confidentiality model actually protects.

<a id="s02"></a>
### S02 — Bayesian agents in federated network domains, 2019

Álvaro Carrera, Eduardo Alonso, and Carlos A. Iglesias, **A Bayesian
Argumentation Framework for Distributed Fault Diagnosis in Telecommunication
Networks**, *Sensors* 19(15), 3408. DOI: 10.3390/s19153408.
**Evidence: Text**, Sections 3–6.
[University manuscript](https://openaccess.city.ac.uk/id/eprint/22656/1/sensors-19-03408-v3.pdf).

Domain agents use local Bayesian models and exchange arguments under information
access restrictions. A manager forms coalitions and resolves conclusions. The
evaluation includes public classification datasets and a private telecom dataset
from 18 months of an earlier operational system. The proposed federation was
evaluated as distributed classification; the earlier deployment should not be
presented as deployment of the new method. [BARMAS source](https://github.com/gsi-upm/BARMAS)
is available, although it was not built or reproduced during this review.

**Implication:** per-domain agents, local knowledge, selective information
exchange, uncertainty, and coordinated diagnosis are established. The manager
role differs from our proposed authority model; that difference alone is not a
sufficient contribution.

<a id="s03"></a>
### S03 — Distributed diagnosis across administrative domains, 2007

Malgorzata Steinder and Adarshpal S. Sethi, **Multidomain Diagnosis of End-to-End
Service Failures in Hierarchically Routed Networks**, *IEEE Transactions on
Parallel and Distributed Systems*, 2007. **Evidence: Abstract**.
[IBM author record](https://research.ibm.com/publications/multidomain-diagnosis-of-end-to-end-service-failures-in-hierarchically-routed-networks).

Hierarchically organized managers diagnose failures using local domain knowledge
and distributed coordination. The reported evaluation uses simulation. A 2004
conference predecessor belongs to the same research family.

**Implication:** end-to-end diagnosis without giving every manager complete
internal network knowledge is an old problem. Our non-hierarchical control
arrangement needs an operational advantage, not just a different diagram.

<a id="s04"></a>
### S04 — One label owner is already part of VFL, 2019

Qiang Yang, Yang Liu, Tianjian Chen, and Yongxin Tong, **Federated Machine
Learning: Concept and Applications**, *ACM TIST* 10(2), Article 12, 2019.
**Evidence: Text**, Section 2.4.2.
[Author manuscript](https://arxiv.org/pdf/1902.04885).

The vertical-learning formulation explicitly considers separate feature owners
with label data held by company B. It describes joint training while protecting
data, including a linear-regression example.

**Implication:** “one owner has labels, others only features” cannot be our novelty.
Receiver ownership provides a useful networking motivation for that known
partition. Our independent predictors and online action choices are different
design objectives, which should be specified and evaluated rather than used to
dismiss VFL.

<a id="s05"></a>
### S05 — Cooperative optical fault management, 2022

Xiaoliang Chen et al., **On Cooperative Fault Management in Multi-Domain Optical
Networks Using Hybrid Learning**, *IEEE JSTQE* 28(4), 2022.
DOI: 10.1109/JSTQE.2022.3151878. **Evidence: Abstract and indexed manuscript**.
[University record](https://iris.polito.it/handle/11583/2971919).

This broker-based approach combines self-supervised soft-failure detection,
uncertainty estimation, federated learning, and localization. It explicitly
studies highly uneven training data, including two domains with no abnormal
training samples.

**Implication:** cooperation benefiting poorly informed optical domains is
already demonstrated. Lack of abnormal samples differs from lack of receiver
outcome labels, but the general “weak local knowledge benefits from peers”
argument is insufficient.

<a id="s06"></a>
### S06 — Vertical FL for optical failure localization, 2024

Memedhe Ibrahimi, Fatih Temiz, Francesco Musumeci, and Massimo Tornatore,
**Vertical Federated Learning for Failure Localization in Partially
Disaggregated Optical Networks**, IEEE HPSR 2024.
DOI: 10.1109/HPSR62440.2024.10635921. **Evidence: Mixed**.
[Author metadata](https://fatihsaysthat.owlstown.net/publications/46136-vertical-federated-learning-for-failure-localization-in-partially-disaggregated-optical-networks)
and [indexed university manuscript](https://re.public.polimi.it/bitstream/11311/1287086/1/_HPSR_workshop__VFL_for_failure_management.pdf).

SplitNN combines separately held optical measurements for localization, with
two- and three-operator scenarios and real NICT testbed OSNR data. Direct PDF
access failed during this review; selected indexed passages and author metadata
support this limited comparison.

**Implication:** VFL is not merely a conceptual analogy from another field. It
has been applied to this networking problem. Read this alongside its later
research-family contribution below.

<a id="s07"></a>
### S07 — Heterogeneous optical data and stronger baselines, 2025

Memedhe Ibrahimi et al., **Failure Localization in Disaggregated Optical
Networks: Application of Vertical Federated Learning on Heterogeneous Data**,
IEEE ICMLCN 2025. **Evidence: Text**, Sections III–VI.
[University record](https://re.public.polimi.it/handle/11311/1299104) and
[author manuscript](https://re.public.polimi.it/retrieve/a034c86a-f5e4-4c13-aefa-475103122d09/pre_print_ICMLCN_Ibrahimi.pdf).

The study evaluates SplitNN and gradient-boosted-tree VFL using two optical
testbed datasets, with centralized and non-collaborative alternatives. A strong
local tree model substantially narrows the collaboration advantage in one
scenario compared with the neural-network baseline.

**Implication:** this is a particularly important current empirical comparator.
Our conclusions must survive competent local baselines. Comparing only an
uninformed local learner against fully informed peers risks overstating the
value of the proposed federation.

<a id="s08"></a>
### S08 — VFL in disaggregated microwave networks, 2025

Fatih Temiz et al., **Vertical Federated Learning for Failure-Cause
Identification in Disaggregated Microwave Networks**, IEEE ICC 2025.
DOI: 10.1109/ICC52391.2025.11161708. **Evidence: Text**.
[Publication record](https://arxiv.org/abs/2502.02874) and
[manuscript](https://arxiv.org/html/2502.02874v1).

SplitNN and FedTree are evaluated on real hardware-failure observations, dividing
alarm features among vendor roles. The dataset has 1,669 observations and four
failure classes. Centralized classification provides a reference.

**Implication:** collaborative fault inference from heterogeneous owners is
established beyond optical systems. This is a classifier comparison, so adapting
it to our online recovery objective requires a clearly described action layer.

<a id="s09"></a>
### S09 — Generalization without raw carrier-data sharing, 2025

Forough Shirin Abkenar et al., **Federated Privacy-Preserving Strategy for
Generalizing Soft-Failure Localization in Multi-Carrier Optical Networks**,
ONDM 2025. **Evidence: Text**.
[Conference manuscript](https://opendl.ifip-tc6.org/db/conf/ondm2025/ondm2025/1571116948.pdf).

The approach combines self-supervised processing, domain adaptation, and
teacher/student learning with federated updates. Testbed-derived data evaluate
localization across attenuation conditions without centralizing raw carrier
records.

**Implication:** varying impairment severity and reducing shared data are active
research topics with experimental precedents. This does not by itself establish
our sequential drift-and-recurrence experiment, but it raises the required
comparison beyond a single static impairment.

<a id="s10"></a>
### S10 — Adaptive acquisition of diagnostic evidence, 2004

Irina Rish et al., **Real-Time Problem Determination in Distributed Systems
Using Active Probing**, IEEE/IFIP NOMS 2004. **Evidence: Abstract**.
[IBM author record](https://research.ibm.com/publications/real-time-problem-determination-in-distributed-systems-using-active-probing).

The method selects informative probes online, updates beliefs from their results,
and continues until diagnosis. Analysis and simulation compare it with
non-adaptive probing.

**Implication:** “ask for the next useful observation” is established. An adaptive
disclosure policy should be compared against information-gain or value-of-
information selection. Querying stored peer evidence and acquiring a fresh probe
have different costs and must not be conflated.

<a id="s11"></a>
### S11 — Domain agents for intent resolution, 2025

Pedro Martinez-Julia, Ved P. Kafle, and Hitoshi Asaeda, **EDAIR: An Efficient
Distributed AI Agent Architecture for Multi-Domain Intent Resolution**, NOMS
2025. DOI: 10.1109/NOMS57970.2025.11073742. **Evidence: Abstract**.
[IEEE record](https://ieeexplore.ieee.org/document/11073742/).

An intelligent agent represents each domain; only relevant agents participate,
and intent resolution stops when a suitable solution is found.

**Implication:** one agent per domain and selective collaboration are architectural
precedents. Intent resolution differs from our diagnostic decision problem;
detailed transaction or recovery distinctions require full-text inspection.

<a id="s12"></a>
### S12 — Model-based end-to-end network diagnosis, 2025

Changrong Wu et al., **Model-Based Diagnosis: Automating End-to-End Diagnosis
of Network Failures**, NetDx, arXiv:2506.23083v2, July 2025.
**Evidence: Abstract and indexed author manuscript; preprint version assessed**.
[Record](https://arxiv.org/abs/2506.23083) and
[author manuscript](https://web.cs.ucla.edu/~tamir/papers/mbnd_arxiv.pdf).

NetDx derives diagnostic procedures from forwarding and routing models. Its
evaluation uses a P4 network emulator and fault cases from a cloud provider.

**Implication:** dependency-aware diagnosis from end-to-end symptoms has strong
non-LLM comparators. Its enterprise-network access assumptions differ from
independent-owner disclosure policies. Do not assume those assumptions can be
transferred unchanged to our evaluation.

## 5. Measurement and service-assurance foundations

<a id="s13"></a>
### S13 — Counter-based segment measurement is standardized

**RFC 9341, Alternate-Marking Method**, 2022.
**Evidence: Text**, Sections 2, 3, 4.3, and 5.
[RFC](https://www.rfc-editor.org/rfc/rfc9341.html).

The method measures loss across selected network segments by comparing packet
counts for corresponding marked blocks. It explains why counters must refer to
the same packet cohort, and discusses collection, correlation, and timing.

**Implication:** subtracting cross-boundary counts is not a new localization
algorithm. The proposed measurement must establish matching traffic scope and
intervals, including resets, delays, and background traffic. RFC 9341 is scoped
to controlled domains; it does not automatically solve the commercial or
authorization problem between unrelated operators.

<a id="s14"></a>
### S14 — Service dependency graphs and health aggregation

**RFC 9417, Service Assurance for Intent-Based Networking Architecture**, 2023.
**Evidence: Text**, Sections 2–3.
[RFC](https://www.rfc-editor.org/rfc/rfc9417.html).

The architecture decomposes service instances into subservices and dependency
graphs, with metrics and computations that produce health status and symptoms.

**Implication:** connecting service-level evidence to underlying resources is
established architecture. A graph implementation using NetworkX or retrieval
does not itself distinguish Paper 1. The research issue is what inference or
decision the map enables under restricted information.

<a id="s15"></a>
### S15 — SIMAP is existing IETF work

Olga Havel et al., **SIMAP: Concept, Requirements, and Use Cases**,
`draft-ietf-nmop-simap-concept-13`, 4 September 2026.
**Evidence: Text; active Internet-Draft, not an RFC at this assessment date**.
[Versioned draft](https://datatracker.ietf.org/doc/html/draft-ietf-nmop-simap-concept-13).

The draft specifies the Service & Infrastructure Maps concept and its operational
requirements and use cases.

**Implication:** cite SIMAP as a foundation. Our signed owner-authored slices are
a proposed implementation choice, not an invention of service–infrastructure
mapping. Replicated topology must be included in the disclosure accounting or
explicitly declared public to the participating owners.

## 6. Recent agents, evidence validity, and recovery

<a id="s16"></a>
### S16 — ETSI already describes cross-domain fault agents

**ETSI GR ZSM 020 V1.1.1, Study on the Utilization of Agents in Autonomous
Networks**, January 2026. **Evidence: Text**, Sections 5.2–5.3.
[ETSI report](https://www.etsi.org/deliver/etsi_gr/ZSM/001_099/020/01.01.01_60/gr_ZSM020v010101p.pdf).

The report describes agents forming a cross-domain fault investigation and
negotiating for missing task information. It discusses discovery, communication,
and coordination in ZSM. This is a Group Report and use-case study, not a
measured algorithm benchmark or proof of production performance.

**Implication:** an A2A-like exchange among fault agents is insufficient as a
research contribution. The paper should position its specific method within
these operational use cases.

<a id="s17"></a>
### S17 — Scoped, fresh, auditable evidence is already proposed

Yong Cui et al., **Operational Requirements for Network State Exchange in
Agent-Assisted Network Operations**, `draft-cui-nmop-agent-sketch-com-00`,
4 July 2026. **Evidence: Text; individual Internet-Draft, work in progress**.
[IETF archive](https://www.ietf.org/archive/id/draft-cui-nmop-agent-sketch-com-00.html).

Requirements include compact summaries, source and query scope, error metadata,
freshness, time alignment, cross-domain merging, privacy, and auditability.
Section 5.10 separates exchanging state from permission to take operational
actions. It does not define a new protocol or wire format.

**Implication:** timestamps, provenance, and authorization separation should be
engineering foundations. A new evidence envelope listing these fields is not
enough. A contribution would need a particular inference or acquisition method,
with a defensible property or operational advantage.

<a id="s18"></a>
### S18 — Reliability Assurance Intelligence, 2026

Bilgehan Erman, Andrea Francini, and Nikos Papadis, **Assurance-Scoped
Reliability for Agentic Networks: Capturing the State That Matters**,
arXiv:2607.26953v1, 29 July 2026. **Evidence: Text; preprint**.
[Manuscript](https://arxiv.org/html/2607.26953v1).

RAI proposes per-service assurance profiles and adaptive retention of evidence
needed for accountable execution and recovery. It covers stale context,
duplicate effects, partial changes, and authority boundaries. Section VI
explicitly presents an architectural proposal and validation methodology,
including full, fixed-minimal, and adaptive recording comparisons.

**Implication:** this also overlaps the narrower recovery direction. Our study
could investigate acquisition of peer evidence for an operational decision,
where RAI discusses assurance and retained state; that distinction needs a
method and experiment. “Adaptive evidence plus recovery” is not an untouched gap.

<a id="s19"></a>
### S19 — Evidence sufficiency and abstention, 2026

Yuxuan Zhu and Peng Pu, **TelemetrySuffBench: Is Agent Telemetry Sufficient for
Failure-Origin Diagnosis?**, arXiv:2608.07899v1, 8 August 2026.
**Evidence: Abstract; preprint**.
[Record](https://arxiv.org/abs/2608.07899).

The benchmark distinguishes detection, origin localization, and abstention using
controlled agent-execution traces, including ambiguous cases with identical
visible evidence. It evaluates several LLMs.

**Implication:** ambiguity and abstention are established evaluation concerns.
These are synthetic software-agent traces, not a telecom forwarding testbed;
do not transfer its reported performance to our network. Borrow the discipline
of including genuinely indistinguishable cases.

<a id="s20"></a>
### S20 — Evidence-grounded telecom RCA, September 2026

Hao Zhou et al., **Large Language Models (LLMs) for Telecom Root Cause Analysis
(RCA): A Structured Reasoning Framework for Evidence-Grounded Diagnosis**,
arXiv:2609.02805v1, 2 September 2026. **Evidence: Abstract; preprint**.
[Record](https://arxiv.org/abs/2609.02805).

The proposed framework organizes telemetry into canonical contexts and constrains
diagnostic reasoning, evaluated on TeleLogs and TelecomTS.

**Implication:** adding an LLM or evidence-grounded explanation does not rescue
Paper 1's novelty. This is more directly relevant to Paper 3, but belongs in the
watch list if Paper 1 retains an LLM.

<a id="s21"></a>
### S21 — A multivendor industry demonstration, May 2026

Ericsson, **Multivendor Agentic AI Solution for Cloud RAN**, 11 May 2026.
**Evidence: Original vendor account; demonstration, not peer-reviewed evaluation**.
[Ericsson account](https://www.ericsson.com/en/blog/2026/5/multivendor-agentic-ai-solution-for-cloud-ran).

Ericsson describes collaboration with Red Hat and Intel agents for diagnosis
across RAN, platform, and hardware layers, including a simulated timing fault.

**Implication:** industry is demonstrating the general concept. Distinct vendors
and technical layers do not necessarily mean independent network owners with
our assumed policies. The account is evidence of a demonstration, not an
independently verified performance comparison.

<a id="s22"></a>
### S22 — Cross-organizational trust evidence, September 2026

Huafu Li and Jia Xia, **When Agentic Trust Crosses Organizational Boundaries:
Structural Externalization and a Reference Model for Trust Evidence**,
arXiv:2609.22961v1, 19 September 2026. **Evidence: Abstract; preprint**.
[Record](https://arxiv.org/abs/2609.22961).

This reference model describes action-scoped evidence, authority, provenance,
validity, disclosure, and recovery across organizations, with analytical
scenarios and a proposed evaluation protocol.

**Implication:** signed evidence and authority-bound actions also have adjacent
conceptual precedents. The abstract supports conceptual overlap, not a claim
that the authors implemented our packet/optical recovery system.

<a id="s23"></a>
### S23 — Acting before complete diagnosis, 1996

David Ash and Barbara Hayes-Roth, **Using Action-Based Hierarchies for Real-Time
Diagnosis**, *Artificial Intelligence* 88(1–2), 317–347, 1996.
DOI: 10.1016/S0004-3702(96)00024-0. **Evidence: Publisher abstract**.
[Publisher record](https://www.sciencedirect.com/science/article/pii/S0004370296000240).

The approach attaches useful actions to partial diagnoses and considers action
utility when a deadline prevents completing the diagnostic process.

**Implication:** choosing a useful response before uniquely identifying a fault,
including under a deadline, is not a new idea. Our recovery formulation must
identify and evaluate its additional network-specific mechanism.

<a id="s24"></a>
### S24 — Equivalence-class determination and costly tests, 2010

Daniel Golovin, Andreas Krause, and Debajyoti Ray, **Near-Optimal Bayesian Active
Learning with Noisy Observations**, NIPS 2010. **Evidence: Text**, Sections 2–3;
the accessible arXiv manuscript is a later revision.
[Proceedings](https://proceedings.neurips.cc/paper/2010/hash/1e6e0a04d20f50967c64dac2d639a577-Abstract.html)
and [manuscript](https://arxiv.org/pdf/1010.3091).

EC2 selects costly tests to determine an equivalence class under a probabilistic
model, with theoretical guarantees under stated assumptions. The work already
compares alternatives such as information gain and value of information.

**Implication:** an acquisition comparison limited to information gain can miss a
stronger baseline. Do not import the paper's guarantees into a changing network
without establishing that its assumptions still hold.

<a id="s25"></a>
### S25 — Sufficient evidence for overlapping decisions, 2014

Shervin Javdani et al., **Near Optimal Bayesian Active Learning for Decision
Making**, AISTATS 2014, PMLR 33:430–438. **Evidence: Abstract**.
[Primary proceedings](https://proceedings.mlr.press/v33/javdani14.html).

The HEC method considers overlapping decision regions and collecting observations
until all remaining hypotheses lie in a sufficient region. It gives conditions
for determining such a region and an algorithm with a competitiveness result.

**Implication:** the distinction between information sufficient for a decision and
information sufficient for a unique diagnosis is established. It is a foundation
and baseline, not our proposed invention. The narrower [proposal](tnsm-proposal.md)
therefore examines evidence scheduling and validity across network owners.

## 7. Assessment of the pre-review claims

The judgments below are this review's analysis of the repository, not claims
made by the cited authors.

| Current claim or ingredient | Assessment | Required change |
| --- | --- | --- |
| Ownership splits features and labels | Known learning formulation; [S04](#s04), with network applications [S06–S08](#s06) | Present as the problem setting. Compare evidence exchange with appropriate collaborative learning. |
| C1: owners without receiver labels cannot learn “at all” | Too broad; no labels blocks a specified supervised update, not all learning, inference, or prior knowledge | Define the permitted observations, initial knowledge, training data, and all feedback channels. |
| C2: sharing improves predictions and decisions | Useful empirical question; improvement from added information alone is weak novelty | Separate prediction gains from better operational choices, and compare at equal information/cost budgets. |
| C4: sharing matters most when local telemetry is blind | Plausible but closely related to [S01](#s01), [S02](#s02), [S05](#s05) | Use naturally motivated visibility limits and strong local models; do not manufacture the whole benefit by disabling telemetry. |
| C6: cross-owner counter subtraction detects/localizes loss | Established measurement principle; [S13](#s13) | Treat as instrumentation. Establish packet-cohort validity and distinguish detection from localization. |
| C7: attribution quality depends on disclosed information | Central theme of prior distributed diagnosis | A method needs an explicit criterion for requesting evidence and knowing when the remaining ambiguity matters. |
| C8: act appropriately and avoid unnecessary changes | Operationally valuable but under-specified | Measure wrong-action harm, avoidable abstention, missed repairs, and realized service outcomes. |
| SIMAP and dependency traversal | Existing architectural foundations; [S14–S15](#s14) | Cite and use them. Evaluate what your method adds on top. |
| One domain agent, A2A, MCP, local models | Implementation/coordination choices; [S02](#s02), [S11](#s11), [S16](#s16) | Keep them out of the headline novelty claim. |
| Selective, timestamped, signed evidence | Existing concepts; [S17–S18](#s17), [S22](#s22) | Specify the additional algorithm or established property; signatures authenticate origin, not measurement truth. |

### Problems identified in the pre-review experiments

1. **Frozen predictors do not imply flat prediction error.** Their weights can
   stay constant while inputs and outcomes change. S0 should test whether an
   outcome-dependent update occurred, not require a horizontal MAE curve.
2. **Receiver ownership is not an information-theoretic isolation proof.** Define
   whether transport/application feedback, endpoint reports, historical labels,
   or active probes are available. Packet B can observe the receiver outcome;
   the blanket statement that no domain observes an outcome is inaccurate.
3. **Counter conservation alone is not independent validation.** For adjacent
   values, `(A-B)+(B-C)+(C-D)+(D-R)=A-R` telescopes. Use an independent packet
   trace or known packet identifiers to validate segment attribution, along with
   comparable windows and counting semantics. Do not sum loss percentages with
   different denominators as though they were packet counts.
4. **A prediction coefficient is not causal responsibility.** Correlated load,
   coordinated configuration changes, and delayed effects confound attribution.
   Use controlled interventions and separate fault injection truth from agent
   inputs. Label statistical attribution honestly.
5. **Owner of a faulty segment need not be owner of the best remedy.** A healthy
   domain might reroute around a peer's failure; the fault owner might have no
   repair available. Score whether an authorized action helps under the declared
   action model, not simply whether the fault owner acts. Keep rate compensation
   and asynchronous-loop stability in Paper 2 unless scope is explicitly changed.
6. **The optical model limitation cannot carry the physical-network claim.** A
   gOSNR feature disconnected from packet delivery is a useful negative control.
   It does not establish how a physical optical impairment affects a real service.
7. **Disclosure volume is not a privacy guarantee.** Count bytes/fields as cost.
   If claiming privacy, state the hidden property, adversary knowledge, and
   leakage criterion. Include what replicated topology already reveals.

## 8. Recommended revised research question

> Under independent domain authority and delayed or incomplete observations,
> which peer evidence should a domain request before choosing a recovery action,
> and when should it abstain because the evidence cannot justify that action?

A possible working title is **Selective Evidence Acquisition for Recovery in
Multi-Domain Packet–Optical Networks**. This is a proposal, not an assertion of
priority over the literature above.

The useful distinction to investigate is **evidence needed for a decision**, not
necessarily evidence needed to name one unique root cause. Several plausible
causes may permit the same beneficial action; a confident cause estimate may
still leave the effect of an action uncertain. A method that exploits this
distinction could reduce disclosure or delay while controlling harmful changes.
This distinction is already formalized in decision-oriented diagnosis and
decision-region determination [S23–S25](#s23). It is not a novelty claim.
The follow-up [TNSM proposal](tnsm-proposal.md) instead investigates scheduling
compatible evidence that remains useful through network execution, under owner
disclosure policies. Its advantage over existing methods with freshness checks
still needs to be established.

### A concrete candidate formulation

Let `E` be evidence already available, `Q` a set of allowable requests, and
`A_i` the actions owner `i` is authorized to perform, including abstention.
Evidence carries service/path version, observation interval, traffic scope,
provenance, and measurement uncertainty. Requests have declared disclosure
costs and response delays. These fields support the method; they are not its
claimed invention.

Maintain a set of network/fault states consistent with valid evidence and a
declared model. An action is admissible only if its predicted harm stays within
a specified bound over that set, or under a separately calibrated probabilistic
criterion. Request further evidence when it can change admissibility or improve
the choice sufficiently to justify its cost. Revalidate relevant state before
execution; abstain when the budget or deadline prevents a justified choice.

This is a starting formulation, not a completed algorithm or guarantee. The
important technical work is constructing useful uncertainty sets or calibrated
risks, selecting requests efficiently, handling changes during collection, and
showing how the rule differs from standard value-of-information policies.
Model mismatch must be tested rather than hidden behind the formalism.

Evaluate a vector of outcomes first: harmful-action rate, repair latency,
service loss, abstention coverage, and disclosure cost. A weighted objective can
be secondary, with sensitivity analysis; a convenient choice of weights must
not create the claimed advantage.

### Three candidate contributions, conditional on results

1. A precise model of evidence sufficiency for named, owner-authorized recovery
   actions, including cases in which extra observations cannot resolve the
   relevant decision before its deadline.
2. An acquisition and stopping algorithm that improves a measurable tradeoff
   over fixed sharing and competent adaptive diagnosis. A bounded guarantee
   under explicit assumptions, or convincing generalization across scenarios,
   would make this stronger.
3. A reproducible evaluation with controlled faults, stale and missing evidence,
   real execution outcomes, and disclosure accounting. Dataset or benchmark
   value requires representative scenarios and reusable artifacts, not just
   logging one small topology.

None is established by the current code. Implementing a list of known
requirements, without the method or substantive empirical finding, remains an
engineering integration exercise.

## 9. Comparisons and experiments that could support the paper

### Baselines

| Baseline | What it tests |
| --- | --- |
| Local-only deterministic diagnosis with all policy-permitted local signals | Whether local reasoning already solves the cases; disclose any denied feedback. |
| Receiver-outcome-only sharing plus a strong local predictor | Whether inexpensive labels explain the entire benefit. Include EWMA and a suitable tabular model. |
| Fixed boundary-counter or event-triggered sharing | Whether a simple operational rule matches adaptive selection. |
| Full permitted evidence with the same decision procedure | The information-rich reference; separate centralized analysis from centralized authority. |
| Distributed Bayesian diagnosis / graph-digest adaptation | Direct comparison with the ideas in [S01–S03](#s01); document all implementation departures. |
| Greedy information-gain or value-of-information requests | Whether the acquisition policy adds anything beyond active diagnosis [S10](#s10). |
| EC2 or HEC with the same evidence-validity checks | Whether the method adds anything beyond established decision-oriented acquisition [S24–S25](#s24). |
| Suitable VFL implementation, if prediction remains a principal claim | Whether raw evidence exchange is preferable to model/intermediate exchange for the stated task. |
| Proposed method without freshness or stopping logic | Whether those mechanisms, rather than extra information or tuning, cause any advantage. |
| Offline oracle | Bounds achievable choices in controlled experiments; never expose its future knowledge to agents. |

Start with local-only, receiver-only, fixed-counter, full-evidence, and greedy
acquisition baselines. Reproduce at least one closest distributed-diagnosis
method before claiming a comparative advance. A requirements document is a
conceptual comparator, not an algorithm that can meaningfully be “beaten.”

Use the same fault cases, permitted measurements, training budgets, and action
sets. Count communication during training and inference for learning baselines.
If a method requires a server, distinguish a computation coordinator from an
entity allowed to operate every owner's devices. Do not quietly grant one
method privileged oracle data or deny another its essential inputs.

### Experimental conditions

- Include single faults, concurrent faults, benign load changes, missing peer
  responses, delayed reports, counter resets, and a path change during evidence
  collection. Use both identifiable and deliberately ambiguous cases.
- Include faults with no feasible repair and cases in which a wrong change makes
  service worse. Test abstention alongside missed opportunities and its delay;
  a system that always refuses must not appear optimal.
- Use fresh receiver measurements to verify consequences. Validate the packet
  measurement pipeline and partial-write handling before running recovery trials.
- The present eight-configuration fixture is suitable for a pilot and an
  enumerable oracle. Add independent topologies, more services or paths, and
  different fault/traffic regimes before making broad scalability claims.
- Use paired schedules, independent runs, confidence intervals, and a blind
  holdout by topology or fault regime. Avoid leakage through overlapping time
  windows, repeated episode identifiers, or tuning on the final test scenarios.
- Report where each baseline wins. Separate physical optical observations from
  emulator-imposed packet impairment and model-only negative controls.

**Primary figure:** harmful actions and recovery delay versus disclosure budget,
with abstention/coverage visible. Per-agent prediction error can remain a
secondary diagnostic. Reducing MAE is not enough if action quality is unchanged.

## 10. Go/no-go decision and publication direction

My assessment is a **conditional go for a narrower Paper 1, and a no-go for the
pre-review novelty wording**. IEEE TNSM remains a sensible subject-matter target
for a completed service-management contribution; journal suitability does not
make the present proposal ready for submission. This report does not re-audit
journal quartiles, which should be checked against the institution's required
database and year when preparing the submission.

Run a small deterministic pilot before investing in the complete agent stack.
Use realistic faults to compare receiver-only, fixed-counter, full-evidence,
and adaptive acquisition. Determine whether less disclosure can retain useful
recovery performance, and whether the adaptive rule improves on a strong fixed
rule at comparable delay and action risk. Establish these decision criteria
before inspecting the final test set.

Proceed if there is a repeatable, practically meaningful advantage and an
explainable mechanism. Reframe as a benchmark or systems study only if the
artifact and empirical findings support that contribution on their own. If
receiver-only or fixed-counter sharing performs just as well, publish that
finding honestly or reconsider the direction; adding more agents or an LLM
does not resolve a missing research contribution.

The first reading set is S01, S02, S04, S07, S13, S17, and S18. Together they
cover the main novelty challenges: existing distributed inference, the known
learning partition, credible networking baselines, measurement validity, and
recent evidence/assurance architecture.
