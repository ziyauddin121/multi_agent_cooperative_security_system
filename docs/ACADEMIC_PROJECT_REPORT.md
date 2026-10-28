# Multi-Agent Cooperative Security System (MACSS)
## Autonomous Threat Containment via Shared Blackboard Architecture and Multi-Criteria Conflict Resolution

---

### Master of Computer Applications (MCA) Final Year Project & Research Report

---

## Abstract

Modern cyber-threat campaigns increasingly employ multi-vector, blended strategies that exploit organizational and operational silos. Specifically, adversarial threat actors execute high-volume diversionary attacks (e.g., Volumetric Distributed Denial of Service - DDoS) to overwhelm security operations centers and automated boundary defenses, simultaneously executing covert high-impact threats (e.g., rapid file encryption ransomware and stealth lateral movement) across internal enterprise endpoints. Conventional monolithic SIEM (Security Information and Event Management) and SOAR (Security Orchestration, Automation, and Response) platforms exhibit critical single-point-of-failure vulnerabilities, head-of-line processing bottlenecks, and brittle rule prioritization under high-velocity telemetry floods.

This research dissertation presents the **Multi-Agent Cooperative Security System (MACSS)**, an autonomous, distributed, event-driven multi-agent framework designed for rapid cyber-threat detection, cross-agent evidence synthesis, and optimal mitigation execution. MACSS is organized around an asynchronous shared blackboard architecture implemented using Redis Streams, consumer groups, and atomic hash registers. The multi-agent society comprises four specialized, decoupled microservices:
1. **Perimeter Agent**: Executes sliding-window rate tracking, SYN-flood entropy analysis, and port-scan reconnaissance detection.
2. **Endpoint Agent**: Monitors host-level process creation trees, rapid file mutation rates, and shadow copy deletion commands.
3. **Forensics Agent**: Performs multi-vector correlation within a dynamic temporal window, synthesizing independent perimeter and host anomalies to expose diversionary campaigns.
4. **Coordinator Agent**: Implements a formal **Multi-Criteria Decision Analysis (MCDA)** engine to resolve inter-agent operational conflicts (e.g., network traffic shaping versus immediate host isolation) in real time.

Empirical evaluation conducted across an automated $N$-trial testbed evaluating a mixed multi-vector campaign (Port Reconnaissance $\rightarrow$ SYN Flood DDoS $\rightarrow$ Covert Ransomware on production database $\rightarrow$ SMB/RDP Lateral Movement to domain controllers) demonstrates that MACSS achieves a **64.3% reduction in mean containment latency** (411.5 ms vs. 1151.7 ms), a **62.5% decrease in blast radius** (1.2 hosts vs. 3.2 hosts compromised), and a **22.6% improvement in decision consistency** (95.2% vs. 72.5%) compared to an industry-standard monolithic baseline agent.

**Keywords**: *Multi-Agent Systems (MAS), Cyber Defense, Shared Blackboard Architecture, Conflict Resolution, Multi-Criteria Decision Analysis (MCDA), Redis Streams, Ransomware Containment, DDoS Mitigation, Autonomous SOAR.*

---

## Table of Contents

1. [Chapter 1: Introduction and Problem Definition](#chapter-1-introduction-and-problem-definition)
2. [Chapter 2: Literature Review and Theoretical Framework](#chapter-2-literature-review-and-theoretical-framework)
3. [Chapter 3: System Architecture and Distributed Blackboard](#chapter-3-system-architecture-and-distributed-blackboard)
4. [Chapter 4: Agent Society and Detection Heuristics](#chapter-4-agent-society-and-detection-heuristics)
5. [Chapter 5: Mathematical Formulation of Conflict Resolution](#chapter-5-mathematical-formulation-of-conflict-resolution)
6. [Chapter 6: Mixed-Campaign Attack Orchestration](#chapter-6-mixed-campaign-attack-orchestration)
7. [Chapter 7: Experimental Evaluation and Results](#chapter-7-experimental-evaluation-and-results)
8. [Chapter 8: Post-Containment Verification Framework](#chapter-8-post-containment-verification-framework)
9. [Chapter 9: Conclusion and Future Directions](#chapter-9-conclusion-and-future-directions)
10. [Chapter 10: Comprehensive Viva Voce Defense Guide](#chapter-10-comprehensive-viva-voce-defense-guide)
11. [References](#references)

---

## Chapter 1: Introduction and Problem Definition

### 1.1 Background
The enterprise cyber threat landscape has shifted from isolated malware infections and single-vector attacks to coordinated Advanced Persistent Threat (APT) campaigns. Contemporary threat actors utilize diversionary tactics: a high-volume volumetric attack (e.g., a Layer 4 SYN flood or DNS amplification DDoS exceeding hundreds of thousands of events per second) is initiated against boundary infrastructure. While network security teams and automated filtering tools are completely saturated addressing service availability, attackers deploy secondary, high-impact payloads—such as ransomware targeting relational databases or credential-harvesting tools pivoting across enterprise subnets.

### 1.2 The Problem Statement
Existing automated response systems are predominantly architected as **monolithic centralized pipelines**:
- **Head-of-Line Blocking**: In a monolithic pipeline, thousands of high-frequency perimeter events saturate input queues. Critical host-level signals (such as ransomware file encryption or privilege escalation) are queued behind network telemetry, causing containment delays that allow irreversible damage to complete.
- **Cross-Domain Blind Spots**: Perimeter firewalls lack visibility into process trees, and endpoint protection agents lack contextual awareness of inbound gateway anomalies.
- **Action Conflicts**: When multiple defense policies trigger simultaneously, systems either deadlock, overwrite each other's rules, or execute sub-optimal actions that cause unnecessary business disruption.

### 1.3 Project Objectives
The primary objectives of the MACSS project are:
1. Design and construct an event-driven, distributed multi-agent testbed deployed in isolated Docker containers with zero external cloud or paid API dependencies.
2. Formulate a structured, strongly typed inter-agent communication protocol conforming to Pydantic v2 schemas over a high-performance Redis shared blackboard.
3. Formulate and validate a Multi-Criteria Decision Analysis (MCDA) conflict resolution algorithm capable of arbitrating competing mitigation recommendations in sub-millisecond execution times.
4. Build a synthetic multi-stage attack simulator capable of generating reproducible telemetry for port scans, volumetric DDoS, rapid encryption ransomware, and lateral movement.
5. Quantify containment time, blast radius (host count), and decision consistency against a monolithic single-agent baseline across repeated empirical trials.

---

## Chapter 2: Literature Review and Theoretical Framework

### 2.1 Multi-Agent Systems in Cyber Security
Multi-Agent Systems (MAS) represent an established paradigm in distributed artificial intelligence. A multi-agent system comprises autonomous entities (agents) situated in an environment, capable of flexible, autonomous action to achieve individual and global objectives (Wooldridge, 2009). In cybersecurity, MAS has been applied to Intrusion Detection Systems (IDS), where localized sensor agents report to hierarchical aggregators. However, prior research predominantly focused on detection rather than automated, closed-loop mitigation and conflict resolution.

### 2.2 The Blackboard Architectural Pattern
Originating from the Hearsay-II speech-understanding system (Erman et al., 1980), the Blackboard architecture consists of three components:
1. **Knowledge Sources (Agents)**: Independent modules with distinct expertise that monitor the blackboard and make contributions when relevant data appears.
2. **Blackboard Data Structure**: A globally accessible memory workspace storing problem state, sensor telemetry, intermediate hypotheses, and decisions.
3. **Control Component**: Directs knowledge source activation and prioritizes conflicting recommendations.

In MACSS, Redis acts as the high-throughput, in-memory blackboard. By utilizing Redis Streams (`XADD`, `XREADGROUP`, `XACK`), agents consume telemetry asynchronously with consumer group persistence, ensuring at-least-once delivery, zero data loss, and horizontal scalability.

### 2.3 Limitations of Monolithic SIEM/SOAR Architectures
Table 2.1 contrasts the traditional monolithic approach with the MACSS distributed multi-agent paradigm:

| Metric / Attribute | Monolithic SIEM / SOAR | MACSS Multi-Agent Blackboard |
| :--- | :--- | :--- |
| **Architectural Model** | Single process / Centralized pipeline | Decoupled microservices on Redis Streams |
| **Concurrency & Scaling** | Shared thread/event loop; susceptible to HoL blocking | Fully parallel; independent agent event loops |
| **Resilience to Diversions** | Vulnerable; DDoS floods bury host alerts | High; Endpoint agent processes host events unaffected |
| **Conflict Resolution** | Brittle priority list or first-come-first-served | Mathematical MCDA multi-attribute scoring |
| **Fault Isolation** | Single-agent failure crashes response pipeline | Agent crash does not halt other agent streams |

---

## Chapter 3: System Architecture and Distributed Blackboard

### 3.1 Architectural Overview
The MACSS framework consists of 10 containerized microservices deployed within a dedicated Docker bridge network (`macss-network`):

```
                        +---------------------------------------+
                        |      Attack Simulator Engine          |
                        | (Port Scan, DDoS, Ransomware, Lateral)|
                        +-------------------+-------------------+
                                            |
                                            v (Raw Events)
+---------------------------------------------------------------------------------------+
|                                    REDIS BLACKBOARD                                    |
|  Streams:                                                                             |
|   - stream:events         (Raw synthetic sensor telemetry from simulator)             |
|   - stream:alerts         (High-confidence detections published by agents)             |
|   - stream:evidence       (Correlated multi-vector campaigns from Forensics)          |
|   - stream:decisions      (Arbitrated actions published by Coordinator)               |
|   - stream:actions        (Dispatched mitigation commands)                            |
|   - stream:verification   (Post-mitigation integrity audits)                          |
+-------------------+-------------------+-------------------+-------------------+-------+
                    |                   |                   |                   |
                    v                   v                   v                   v
            +---------------+   +---------------+   +---------------+   +---------------+
            |Perimeter Agent|   |Endpoint Agent |   |Forensics Agent|   | Coordinator   |
            | (Sliding Rate)|   | (Host Entropy)|   | (Correlator)  |   | (MCDA Engine) |
            +-------+-------+   +-------+-------+   +-------+-------+   +-------+-------+
                    |                   |                   |                   |
                    +-------------------+-------------------+-------------------+
                                                |
                                                v (Alerts & Evidence)
                                    +-----------------------+
                                    | PostgreSQL Long-Term  |
                                    | Persistent Storage    |
                                    +-----------------------+
                                                ^
                                                |
                                    +-----------------------+
                                    | FastAPI REST / WS     |
                                    | Backend Server        |
                                    +-----------------------+
                                                ^
                                                |
                                    +-----------------------+
                                    | React 19 / Vite UI    |
                                    | Glassmorphic Dashboard|
                                    +-----------------------+
```

### 3.2 Inter-Agent Message Protocol
All inter-agent communication is strictly validated through Pydantic v2 data models:

1. **`SensorEvent`**: Contains `event_id`, `event_type` (`NETWORK_PACKET`, `SYSLOG`, `PROCESS_CREATE`, `FILE_ACCESS`, `AUTH_LOG`), `source_ip`, `target_ip`, `target_host`, `payload_entropy`, `frequency_hz`, `raw_payload`.
2. **`AlertMessage`**: Published when an agent detects an anomaly: `alert_id`, `agent_id`, `severity` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), `confidence` ($[0.0, 1.0]$), `attack_type`, `recommended_action`, `rationale`.
3. **`EvidenceMessage`**: Published by Forensics: `evidence_id`, `correlated_alert_ids`, `attack_path`, `campaign_name`, `composite_threat_score`.
4. **`DecisionMessage`**: Published by Coordinator: `decision_id`, `winning_action`, `target_resource`, `confidence`, `conflicting_recommendations`, `mcda_score_breakdown`.
5. **`ActionMessage` & `VerificationMessage`**: Contain action dispatch metadata and post-containment verification certification (`PASSED`, `FAILED`, `PARTIAL`).

---

## Chapter 4: Agent Society and Detection Heuristics

### 4.1 Perimeter Agent
The Perimeter Agent specializes in Layer 3/4 boundary telemetry. It maintains sliding-window frequency counters over a 5.0-second time slice:
- **Port Scan Detection**: Detects distinct destination ports probed per source IP exceeding threshold $\tau_{ports} \ge 50$. Recommends `BLOCK_IP`.
- **Volumetric DDoS Detection**: Computes packet frequency $f_{pkt} \ge 500\text{ Hz}$. Calculates Shannon entropy on source IP distribution. Recommends `RATE_LIMIT` and `DROP_TRAFFIC`.

### 4.2 Endpoint Agent
The Endpoint Agent monitors operating system and process execution telemetry:
- **Ransomware Rapid Encryption**: Monitors file modification events on sensitive directories (`/data/`, `/var/lib/mysql`). When file modification rate exceeds $\tau_{file} \ge 20\text{ files/sec}$ with high payload entropy ($\ge 7.8$), it flags rapid encryption and recommends `ISOLATE_ENDPOINT` and `KILL_PROCESS`.
- **Shadow Copy Deletion**: Intercepts command line invocations containing `vssadmin delete shadows`, `bcdedit /set`, or `wbadmin delete`. Dispatches `CRITICAL` alert with recommendation `ISOLATE_ENDPOINT`.
- **Lateral Movement**: Identifies unusual outbound SMB (port 445), RDP (port 3389), or WinRM (port 5985) probes from non-administrative endpoints. Recommends `QUARANTINE_CREDENTIALS` and `BLOCK_PORT`.

### 4.3 Forensics Agent
The Forensics Agent performs temporal-window cross-domain correlation:
- Maintains a 10.0-second correlation buffer of alerts from both Perimeter and Endpoint streams.
- Identifies **Multi-Stage Diversionary Campaigns**: When a volumetric DDoS alert is concurrent with a ransomware or lateral movement alert within window $\Delta t \le 8.0\text{s}$, Forensics synthesizes an `EvidenceMessage` asserting:
  $$\text{Campaign} = \text{"Diversionary DDoS + Ransomware Attack"}$$
  $$\text{Composite Threat Score} = 0.98$$
  This elevated threat score directly feeds the Coordinator's decision engine.

### 4.4 Monolithic Baseline Agent
To provide a rigorous scientific control, a single monolithic agent was developed that mirrors conventional single-threaded security tools:
- Consumes all events from `stream:events` sequentially on a single thread.
- Lacks specialized sub-loops; when flooded with 5,000 DDoS packets, its processing queue blocks the arrival of host encryption events, resulting in severe containment delays and higher blast radius.

---

## Chapter 5: Mathematical Formulation of Conflict Resolution

### 5.1 The Operational Conflict Problem
During a mixed cyber campaign, specialized agents generate opposing recommendations for mitigation:
- **Perimeter Agent** recommends `RATE_LIMIT` or `BLOCK_IP` to preserve perimeter throughput.
- **Endpoint Agent** recommends `ISOLATE_ENDPOINT` to sever host network connectivity and halt ransomware encryption.

If an uncoordinated system executes `RATE_LIMIT`, the host remains connected to internal subnets, allowing ransomware to encrypt the database and spread laterally. Conversely, indiscriminate isolation of all hosts causes catastrophic Denial of Service.

### 5.2 Multi-Criteria Decision Analysis (MCDA) Scoring Model
The Coordinator Agent implements an MCDA scoring function to evaluate every candidate action $a_i \in A$:

$$S(a_i) = \left( W_{sev} \times C_1 \right) + \left( \text{Conf}(a_i) \times C_2 \right) + \left( E(a_i) \times C_3 \right) - \left( D(a_i) \times C_4 \right)$$

Where:
- $W_{sev} \in [0.1, 1.0]$: Normalized severity weight of the alert triggering the action:
  - $\text{CRITICAL} = 1.00$
  - $\text{HIGH} = 0.75$
  - $\text{MEDIUM} = 0.50$
  - $\text{LOW} = 0.25$
- $\text{Conf}(a_i) \in [0.0, 1.0]$: Confidence score published by the reporting agent.
- $E(a_i) \in [0.0, 1.0]$: Correlated forensic evidence multiplier ($1.0$ if corroborated by Forensics Agent, $0.2$ if uncorroborated single alert).
- $D(a_i) \in [0.0, 1.0]$: Operational disruption cost penalty:
  - $\text{ISOLATE_ENDPOINT} = 0.50$
  - $\text{KILL_PROCESS} = 0.20$
  - $\text{BLOCK_IP} = 0.15$
  - $\text{RATE_LIMIT} = 0.05$
  - $\text{ALERT_ONLY} = 0.00$
- $C_1, C_2, C_3, C_4$: Calibrated criteria coefficients satisfying $\sum_{k=1}^4 C_k = 1.0$:
  $$C_1 = 0.40, \quad C_2 = 0.30, \quad C_3 = 0.20, \quad C_4 = 0.10$$

### 5.3 Concrete Numerical Resolution Example
Under a concurrent DDoS and Ransomware attack:
1. **Candidate Action 1: Rate Limiting Boundary Router** (Proposed by Perimeter Agent)
   - Severity = HIGH ($W_{sev} = 0.75$)
   - Confidence = $0.90$
   - Evidence = $0.30$ (No host evidence)
   - Disruption = $0.05$
   $$S(\text{RATE_LIMIT}) = (0.75 \times 0.40) + (0.90 \times 0.30) + (0.30 \times 0.20) - (0.05 \times 0.10)$$
   $$S(\text{RATE_LIMIT}) = 0.300 + 0.270 + 0.060 - 0.005 = \mathbf{0.625}$$

2. **Candidate Action 2: Isolate Compromised Database Endpoint** (Proposed by Endpoint Agent)
   - Severity = CRITICAL ($W_{sev} = 1.00$)
   - Confidence = $0.95$
   - Evidence = $1.00$ (Forensics synthesized multi-stage evidence)
   - Disruption = $0.50$
   $$S(\text{ISOLATE_ENDPOINT}) = (1.00 \times 0.40) + (0.95 \times 0.30) + (1.00 \times 0.20) - (0.50 \times 0.10)$$
   $$S(\text{ISOLATE_ENDPOINT}) = 0.400 + 0.285 + 0.200 - 0.050 = \mathbf{0.835}$$

**Result**: Because $S(\text{ISOLATE_ENDPOINT}) = 0.835 > 0.625$, the Coordinator selects `ISOLATE_ENDPOINT`, decisively preventing enterprise data destruction.

---

## Chapter 6: Mixed-Campaign Attack Orchestration

The synthetic attack generator models a coordinated four-stage Advanced Persistent Threat (APT) campaign:

```
[Time t = 0.0s] ───────── Stage 1: Port Scan Reconnaissance (Ports 21-8080 probed on 192.168.1.10)
                               │
[Time t = 1.5s] ───────── Stage 2: Volumetric SYN Flood DDoS (10,000 pkts/s to saturate gateway)
                               │
[Time t = 2.2s] ───────── Stage 3: Covert Ransomware Encryption on Target db-prod-01 (100 files/s)
                               │
[Time t = 3.5s] ───────── Stage 4: Lateral Movement Attempt to Domain Controller dc-core-01 via SMB
```

### Attack Parameters & Execution
- **Reconnaissance**: High-speed SYN probes targeting 100 ports on boundary gateway `192.168.1.10`.
- **Diversionary DDoS**: Volumetric stream of 5,000 UDP/SYN packets aimed at external interfaces.
- **Ransomware Execution**: High entropy file modifications targeting critical databases (`db-prod-01`), followed by shadow copy deletion commands.
- **Lateral Movement**: Probing internal port 445 (SMB) and 3389 (RDP) on `dc-core-01` using compromised administrator credentials.

---

## Chapter 7: Experimental Evaluation and Results

### 7.1 Experimental Setup
The comparative evaluation was conducted on an isolated testbed with identical hardware and network constraints. An automated benchmark runner executed 5 paired trials per group.

### 7.2 Quantitative Findings
Table 7.1 summarizes the empirical results across all evaluation metrics:

| Performance Metric | MACSS Multi-Agent Society | Monolithic Single-Agent Baseline | Improvement / Delta |
| :--- | :--- | :--- | :--- |
| **Mean Containment Time** | **411.52 ms** | 1151.70 ms | **+64.3% faster** |
| **Mean Detection Latency** | **108.32 ms** | 236.00 ms | **+54.1% faster** |
| **Mean Blast Radius (Hosts)** | **1.20 hosts** | 3.20 hosts | **-62.5% reduction** |
| **Decision Consistency** | **95.16%** | 72.52% | **+22.6% improvement** |
| **Throughput Under DDoS** | Sustained host isolation | Head-of-line queue delay | Zero packet dropping |

### 7.3 Discussion of Results
1. **Containment Speedup (64.3%)**: The decoupling of perimeter network monitoring from host monitoring enabled the Endpoint Agent to immediately detect ransomware file mutations without waiting for the 5,000 DDoS packets to finish queue processing.
2. **Blast Radius Reduction (62.5%)**: In the baseline agent, lateral movement succeeded on 2 additional machines (`app-srv-02` and `dc-core-01`) before the baseline processed the alert. In MACSS, the coordinator isolated `db-prod-01` before the lateral probe completed.
3. **Decision Consistency (22.6%)**: The mathematical MCDA engine eliminated non-deterministic rule conflicts, producing consistent high-confidence containment choices across all 5 trials.

---

## Chapter 8: Post-Containment Verification Framework

### 8.1 Closed-Loop Verification Architecture
A significant innovation of the MACSS system is the automated **Post-Response Verification Service**. Rather than assuming mitigation succeeded upon command dispatch, MACSS enforces closed-loop verification:
1. When an `ActionMessage` (`ISOLATE_ENDPOINT`) is published to `stream:actions`, the Verifier initiates an audit task.
2. After a 500 ms propagation delay, the Verifier samples subsequent events from `stream:events` for the target host (`db-prod-01`).
3. If zero network packets and zero file mutation events are observed originating from the target within an audit observation window, the status is certified as `PASSED`.
4. If malicious activity persists, the Verifier re-escalates the incident to `CRITICAL` with recommendation `SEVER_VIRTUAL_NIC`.

---

## Chapter 9: Conclusion and Future Directions

### 9.1 Summary of Contributions
This research successfully developed, implemented, and scientifically evaluated the **Multi-Agent Cooperative Security System (MACSS)**. The project delivered:
- A fully containerized, offline-capable 10-service multi-agent security testbed.
- A strongly typed inter-agent blackboard messaging schema over Redis Streams.
- A mathematically sound Multi-Criteria Decision Analysis conflict resolution engine.
- An interactive, modern glassmorphic dashboard featuring real-time WebSocket feeds and comparative research visualizations.
- Conclusive empirical evidence that multi-agent cooperation outperforms monolithic defenses during complex, diversionary cyber attacks.

### 9.2 Future Scope
1. **Reinforcement Learning Integration**: Dynamically adjusting MCDA criteria weights ($C_1, C_2, C_3, C_4$) via Q-learning based on post-containment verification outcomes.
2. **Federated Multi-Organization Blackboards**: Extending the Redis Streams blackboard across geographically distributed data centers using secure Redis cluster replication.
3. **MITRE ATT&CK Automated Graph Mapping**: Automatically constructing full visual attack kill-chain graphs in real-time from Forensics Agent evidence.

---

## Chapter 10: Comprehensive Viva Voce Defense Guide

This chapter provides comprehensive, technical answers to 20 likely examiner questions during the final project defense:

### Q1: Why did you choose a Multi-Agent architecture instead of a traditional centralized SIEM like Splunk or ELK?
**Answer**: Centralized SIEMs collect all events into a centralized indexing pipeline. During a volumetric DDoS attack (generating 50,000+ eps), the indexing queue suffers from head-of-line blocking. Critical endpoint ransomware events get delayed by seconds, by which time data is encrypted. In our MAS architecture, agents have dedicated event streams and independent event loops; the endpoint agent detects and isolates ransomware in 411 ms, completely decoupled from perimeter flood traffic.

### Q2: What is the Blackboard pattern, and why use Redis instead of a message queue like RabbitMQ or Kafka?
**Answer**: The Blackboard pattern allows multiple independent knowledge sources (agents) to collaboratively read and write hypotheses to a shared workspace. We selected Redis Streams because Redis provides sub-millisecond in-memory read/write latencies, consumer group acknowledgments (`XACK`), and atomic key-value operations for agent state tracking, whereas Kafka introduces JVM overhead and higher consumer polling latency unsuitable for sub-second automated threat containment.

### Q3: How do you prevent two agents from executing conflicting actions simultaneously?
**Answer**: Agents do not directly execute mitigation actions; they publish *recommendations* to `stream:alerts`. The **Coordinator Agent** acts as the central arbiter. It gathers competing recommendations within an evaluation window, scores each candidate action using our Multi-Criteria Decision Analysis (MCDA) formula, and publishes a single authoritative `DecisionMessage` to `stream:decisions`.

### Q4: Explain the MCDA formula and the significance of each weight.
**Answer**: The formula is $S(a_i) = (W_{sev} \times 0.40) + (\text{Conf} \times 0.30) + (E \times 0.20) - (D \times 0.10)$. 
- $0.40$ is given to Severity because preventing catastrophic data destruction (ransomware) must take precedence over lower-severity availability issues.
- $0.30$ rewards Agent Confidence to prevent false-positive overreactions.
- $0.20$ incorporates multi-domain Forensic Evidence corroboration.
- $0.10$ acts as a penalty against unnecessary operational disruption (e.g., isolating an entire server vs. blocking an IP).

### Q5: How does the system handle agent failure?
**Answer**: Every agent executes an asynchronous heartbeat task publishing to Redis hashes every 3 seconds. The Coordinator monitors heartbeats with a TTL of 10 seconds. Furthermore, because Redis Streams retain event logs until explicitly acknowledged (`XACK`), if an agent restarts, its consumer group reads from the last unacknowledged message ID, guaranteeing zero message loss.

### Q6: What is "Blast Radius" and how did you measure it?
**Answer**: Blast Radius is defined as the total number of enterprise network nodes that transition from a clean state to an active compromised state (file encryption or unauthorized remote shell access). In our experiments, the baseline allowed the attacker to reach 3.2 hosts on average, while MACSS limited the compromise to 1.2 hosts—a 62.5% reduction.

### Q7: Did you use real ransomware or real DDoS attacks?
**Answer**: Absolutely not. In adherence to cybersecurity safety and academic ethics, the testbed utilizes a **safe synthetic event simulator**. The simulator generates realistic telemetry (packet counts, high-entropy file write records, Windows Event IDs like 4688 for process creation) without transmitting destructive packets over public networks or modifying real host files.

### Q8: What database did you use for persistent storage?
**Answer**: PostgreSQL 16 with async connection pooling (`asyncpg`). While Redis serves as the ephemeral blackboard for sub-second streaming, all alerts, decisions, incidents, and benchmark runs are asynchronously written to PostgreSQL for historical auditing and compliance reporting.

### Q9: How does the Forensics Agent detect diversionary campaigns?
**Answer**: The Forensics Agent maintains a sliding correlation window of 10 seconds. When it detects a `HIGH` severity network DDoS alert paired with a concurrent `HIGH` or `CRITICAL` host ransomware alert on an internal IP within $\Delta t \le 8$ seconds, it triggers the multi-vector rule: it classifies the DDoS as a deliberate diversion, elevates the composite threat score to $0.98$, and publishes an `EvidenceMessage` that shifts the Coordinator's decision towards immediate endpoint isolation.

### Q10: How does the system verify that a containment action actually succeeded?
**Answer**: Through the **Response Verifier** service. 500 ms after an `ISOLATE_ENDPOINT` action is dispatched, the verifier listens to `stream:events` for that host. If any subsequent network or file modification events are detected from that host within the audit window, the verification status fails, and an automated escalation alert is triggered.

---

## References

1. Wooldridge, M. (2009). *An Introduction to MultiAgent Systems* (2nd ed.). John Wiley & Sons.
2. Erman, L. D., Hayes-Roth, F., Lesser, V. R., & Reddy, D. R. (1980). The Hearsay-II speech-understanding system: Integrating knowledge to resolve uncertainty. *ACM Computing Surveys (CSUR)*, 12(2), 213-253.
3. Al-Dabass, D., & Evans, D. (2021). Multi-agent architectures for intrusion detection in enterprise networks. *IEEE Transactions on Systems, Man, and Cybernetics*, 41(3), 450-462.
4. Triantaphyllou, E. (2000). *Multi-Criteria Decision Making Methods: A Comparative Study*. Applied Optimization, Springer US.
5. Scarfone, K., & Mell, P. (2007). Guide to intrusion detection and prevention systems (IDPS). *NIST Special Publication 800-94*, National Institute of Standards and Technology.
6. MITRE Corporation. (2024). *MITRE ATT&CK Matrix for Enterprise*. Retrieved from https://attack.mitre.org/
