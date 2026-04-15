# Synthetic Test Suite — Human Q&A Validation Guide

> **Purpose:** For each synthetic test case, this document provides a structured Q&A
> that a human reviewer can use to validate whether the agent reaches the correct
> root cause analysis. Run a scenario with `opensre tests synthetic --scenario <id>`
> and then walk through the corresponding checklist below.
>
> **How to use:**
> 1. Run the scenario: `opensre tests synthetic --scenario <scenario-id>`
> 2. Read the agent's output (root cause, category, validated claims, causal chain)
> 3. Walk through each question below and mark Pass/Fail
> 4. If you find a bug, open a GitHub issue with the scenario ID and failing question

---

## Table of Contents

| ID | Scenario | Difficulty | Quick Link |
|----|----------|------------|------------|
| 000 | [healthy](#000-healthy) | 1 | Level 1 |
| 001 | [replication-lag](#001-replication-lag) | 1 | Level 1 |
| 002 | [connection-exhaustion](#002-connection-exhaustion) | 1 | Level 1 |
| 003 | [storage-full](#003-storage-full) | 1 | Level 1 |
| 004 | [cpu-saturation-bad-query](#004-cpu-saturation-bad-query) | 1 | Level 1 |
| 005 | [failover](#005-failover) | 1 | Level 1 |
| 006 | [replication-lag-cpu-redherring](#006-replication-lag-cpu-redherring) | 2 | Level 2 |
| 007 | [connection-pressure-noisy-healthy](#007-connection-pressure-noisy-healthy) | 2 | Level 2 |
| 008 | [storage-full-missing-metric](#008-storage-full-missing-metric) | 3 | Level 3 |
| 009 | [dual-fault-connection-cpu](#009-dual-fault-connection-cpu) | 4 | Level 4 |
| 010 | [replication-lag-missing-metric](#010-replication-lag-missing-metric) | 3 | Level 3 |
| 011 | [cpu-storage-compositional](#011-cpu-storage-compositional) | 4 | Level 4 (Axis 2) |
| 012 | [replication-lag-misleading-events](#012-replication-lag-misleading-events) | 3 | Level 3 (Axis 2) |
| 013 | [storage-recovery-false-alert](#013-storage-recovery-false-alert) | 3 | Level 3 (Axis 2) |
| 014 | [checkpoint-storm-cpu-saturation](#014-checkpoint-storm-cpu-saturation) | 4 | Level 4 (Axis 2) |

---

## 000-healthy

**Run:** `opensre tests synthetic --scenario 000-healthy`

**Scenario:** Periodic health check — all RDS metrics are within normal operating bounds.
No actual failure exists.

**Alert summary:** _"Periodic health check passed. All RDS metrics within normal operating bounds."_

### Q&A Checklist

| # | Question | Expected Answer | Pass/Fail |
|---|----------|-----------------|-----------|
| 1 | Did the agent return a non-empty root cause? | Yes — should state the database is healthy/normal | |
| 2 | Is `ROOT_CAUSE_CATEGORY` set to `healthy`? | Yes | |
| 3 | Does the output mention "normal bounds"? | Yes — required keyword | |
| 4 | Does the output mention "no failure"? | Yes — required keyword | |
| 5 | Does the agent avoid diagnosing `resource_exhaustion`? | Yes — forbidden category | |
| 6 | Did the agent complete in ≤ 1 investigation loop? | Yes — max 1 loop | |
| 7 | Did the agent query metrics, logs, and alert rules? | Yes — expected trajectory: `query_grafana_metrics`, `query_grafana_logs`, `query_grafana_alert_rules` | |
| 8 | Does the causal chain correctly state no failure exists? | Yes — should be a "no failure" chain | |

### Known Pitfalls
- Agent should NOT infer a problem from low-variance metrics
- Agent should NOT flag the routine automated backup event as suspicious

---

## 001-replication-lag

**Run:** `opensre tests synthetic --scenario 001-replication-lag`

**Scenario:** Write-heavy workload on the primary generates WAL faster than the read
replica can replay, causing replication lag above 900 seconds.

**Alert summary:** _"Read replica lag exceeded 900 seconds on payments-prod-replica-1 while primary write throughput remained elevated."_

### Q&A Checklist

| # | Question | Expected Answer | Pass/Fail |
|---|----------|-----------------|-----------|
| 1 | Did the agent return a non-empty root cause? | Yes | |
| 2 | Is `ROOT_CAUSE_CATEGORY` set to `resource_exhaustion`? | Yes | |
| 3 | Does the output mention "replication lag"? | Yes — required keyword | |
| 4 | Does the output mention "write-heavy workload"? | Yes — required keyword | |
| 5 | Does the output mention "replica"? | Yes — required keyword | |
| 6 | Does the output mention "WAL"? | Yes — required keyword | |
| 7 | Does the agent avoid diagnosing `cpu_saturation`? | Yes — forbidden category | |
| 8 | Does the causal chain explain: write burst → WAL generation → replica can't keep up → lag? | Yes | |
| 9 | Did the agent complete in ≤ 3 investigation loops? | Yes | |
| 10 | Did the agent query metrics, logs, and alert rules? | Yes | |

### Known Pitfalls
- Agent should NOT blame CPU for the replication lag
- Agent should identify WAL generation rate as the bottleneck mechanism

---

## 002-connection-exhaustion

**Run:** `opensre tests synthetic --scenario 002-connection-exhaustion`

**Scenario:** Leaked client sessions consumed nearly all available `max_connections`.
CPUUtilization elevation (35-50%) is a secondary symptom of accumulated idle sessions,
not an independent problem.

**Alert summary:** _"DatabaseConnections reached 98% of max_connections and application traffic started receiving too many clients errors."_

### Q&A Checklist

| # | Question | Expected Answer | Pass/Fail |
|---|----------|-----------------|-----------|
| 1 | Did the agent return a non-empty root cause? | Yes | |
| 2 | Is `ROOT_CAUSE_CATEGORY` set to `resource_exhaustion`? | Yes | |
| 3 | Does the output mention "connection"? | Yes — required keyword | |
| 4 | Does the output mention "max_connections"? | Yes — required keyword | |
| 5 | Does the output mention "idle"? | Yes — required keyword | |
| 6 | Does the output mention "client sessions"? | Yes — required keyword | |
| 7 | Does the agent avoid diagnosing `cpu_saturation`? | Yes — forbidden category | |
| 8 | Does the agent explain CPU elevation as a secondary symptom of connection pressure? | Yes — CPU is not independent | |
| 9 | Does the agent reference Performance Insights showing `Client:ClientRead` as the dominant wait? | Ideally yes | |
| 10 | Did the agent complete in ≤ 3 investigation loops? | Yes | |

### Known Pitfalls
- Agent must NOT treat the 35-50% CPU as an independent cpu_saturation finding
- Agent should identify the connection pool leak pattern, not just the symptom

---

## 003-storage-full

**Run:** `opensre tests synthetic --scenario 003-storage-full`

**Scenario:** The RDS instance ran out of storage space during a bulk INSERT archival job.
FreeStorageSpace collapsed from 15 GB to 0 in 15 minutes.

**Alert summary:** _"FreeStorageSpace on orders-prod dropped from 15 GB to under 500 MB in 15 minutes during a bulk insert workload."_

### Q&A Checklist

| # | Question | Expected Answer | Pass/Fail |
|---|----------|-----------------|-----------|
| 1 | Did the agent return a non-empty root cause? | Yes | |
| 2 | Is `ROOT_CAUSE_CATEGORY` set to `resource_exhaustion`? | Yes | |
| 3 | Does the output mention "storage"? | Yes — required keyword | |
| 4 | Does the output mention "FreeStorageSpace"? | Yes — required keyword | |
| 5 | Did the agent consult RDS events evidence? | Yes — required evidence source: `aws_rds_events` | |
| 6 | Does the agent cite the RDS event confirming "ran out of storage space"? | Ideally yes | |
| 7 | Does the causal chain explain: bulk INSERT → WriteIOPS spike → storage exhausted → writes blocked? | Yes | |
| 8 | Did the agent complete in ≤ 3 investigation loops? | Yes | |

### Known Pitfalls
- Agent should cite the RDS event as definitive confirmation, not just the metric trend
- WriteIOPS collapsing to zero is the telltale sign of writes being blocked by full disk

---

## 004-cpu-saturation-bad-query

**Run:** `opensre tests synthetic --scenario 004-cpu-saturation-bad-query`

**Scenario:** A full table scan query (`SELECT * FROM orders WHERE status = ?`)
with no index on the status column saturated CPU at 88-97%.

**Alert summary:** _"CPUUtilization on catalog-prod has been above 88% for 20 minutes. Database response times are degraded."_

### Q&A Checklist

| # | Question | Expected Answer | Pass/Fail |
|---|----------|-----------------|-----------|
| 1 | Did the agent return a non-empty root cause? | Yes | |
| 2 | Is `ROOT_CAUSE_CATEGORY` set to `resource_exhaustion`? | Yes | |
| 3 | Does the output mention "CPU"? | Yes — required keyword | |
| 4 | Does the output mention "query"? | Yes — required keyword | |
| 5 | Does the output mention "Performance Insights"? | Yes — required keyword | |
| 6 | Did the agent consult Performance Insights evidence? | Yes — required evidence source | |
| 7 | Does the agent avoid diagnosing `connection_exhaustion`? | Yes — forbidden category | |
| 8 | Does the agent identify the specific bad query (full table scan on orders)? | Ideally yes | |
| 9 | Does the agent note that connections are stable (ruling out connection exhaustion)? | Ideally yes | |
| 10 | Did the agent complete in ≤ 3 investigation loops? | Yes | |

### Known Pitfalls
- Agent should use Performance Insights to identify the specific query, not just note "CPU is high"
- Connections are stable at ~160 — agent should not confuse this with connection exhaustion

---

## 005-failover

**Run:** `opensre tests synthetic --scenario 005-failover`

**Scenario:** A Multi-AZ automatic failover occurred on payments-prod due to a
health check failure. Connection drop lasted ~45 seconds.

**Alert summary:** _"DatabaseConnections on payments-prod dropped to 0 for approximately 45 seconds before recovering. Payment processing was interrupted."_

### Q&A Checklist

| # | Question | Expected Answer | Pass/Fail |
|---|----------|-----------------|-----------|
| 1 | Did the agent return a non-empty root cause? | Yes | |
| 2 | Is `ROOT_CAUSE_CATEGORY` set to `infrastructure`? | Yes | |
| 3 | Does the output mention "failover"? | Yes — required keyword | |
| 4 | Does the output mention "Multi-AZ"? | Yes — required keyword | |
| 5 | Did the agent consult RDS events evidence? | Yes — required evidence source | |
| 6 | Does the agent cite the RDS failover event sequence (initiated → in progress → completed → available)? | Ideally yes | |
| 7 | Does the causal chain explain: health check failure → failover initiated → DNS update → brief outage → recovery? | Yes | |
| 8 | Does the agent note that the workload resumed normally after failover? | Ideally yes | |
| 9 | Did the agent complete in ≤ 3 investigation loops? | Yes | |

### Known Pitfalls
- **This is an `infrastructure` root cause, not `resource_exhaustion`** — connections dropping to 0 is caused by the failover, not by connection exhaustion
- The agent must use the RDS event timeline as the decisive signal, not just the metric dip

---

## 006-replication-lag-cpu-redherring

**Run:** `opensre tests synthetic --scenario 006-replication-lag-cpu-redherring`

**Scenario:** Replication lag caused by a write-heavy batch UPDATE job generating WAL
faster than the replica can replay. CPUUtilization at 70-85% is a **red herring** —
it comes from an unrelated analytics SELECT query running concurrently.

**Alert summary:** _"ReplicaLag on analytics-prod-replica-1 exceeded 1000 seconds. CPUUtilization is also elevated at 75–85%, suggesting potential resource contention."_

### Q&A Checklist

| # | Question | Expected Answer | Pass/Fail |
|---|----------|-----------------|-----------|
| 1 | Did the agent return a non-empty root cause? | Yes | |
| 2 | Is `ROOT_CAUSE_CATEGORY` set to `resource_exhaustion`? | Yes | |
| 3 | Does the output mention "replication"? | Yes — required keyword | |
| 4 | Does the output mention "WAL"? | Yes — required keyword | |
| 5 | Does the output mention "replica"? | Yes — required keyword | |
| 6 | Does the agent avoid diagnosing `cpu_saturation`? | Yes — **forbidden category** | |
| 7 | Did the agent consult Performance Insights? | Yes — required evidence source | |
| 8 | Does the agent explain that the CPU elevation is from a **separate, unrelated** analytics query? | Yes — this is the key adversarial test | |
| 9 | Does the agent distinguish the two workloads (bulk UPDATE vs analytics SELECT) as causally independent? | Ideally yes | |
| 10 | Did the agent complete in ≤ 3 investigation loops? | Yes | |

### Known Pitfalls
- **Critical adversarial test:** The alert mentions both replication lag AND high CPU — a naive agent will blame CPU
- Agent MUST use Performance Insights to separate the two independent workloads
- The CPU elevation started AFTER the lag was already accumulating — timeline matters

---

## 007-connection-pressure-noisy-healthy

**Run:** `opensre tests synthetic --scenario 007-connection-pressure-noisy-healthy`

**Scenario:** All metrics are oscillating near warning thresholds but within normal bounds
for this instance class and traffic pattern. No actual failure exists.

**Alert summary:** _"DatabaseConnections on users-prod oscillating between 55-65% of maximum over the past 20 minutes. No errors reported. Alert fired on warning threshold."_

### Q&A Checklist

| # | Question | Expected Answer | Pass/Fail |
|---|----------|-----------------|-----------|
| 1 | Did the agent return a non-empty root cause? | Yes — should state "healthy" / no failure | |
| 2 | Is `ROOT_CAUSE_CATEGORY` set to `healthy`? | Yes | |
| 3 | Does the output mention "operating bounds"? | Yes — required keyword | |
| 4 | Does the output mention "no failure"? | Yes — required keyword | |
| 5 | Does the agent avoid diagnosing `resource_exhaustion`? | Yes — forbidden category | |
| 6 | Does the agent avoid diagnosing `infrastructure`? | Yes — forbidden category | |
| 7 | Does the agent note that connection count is 55-62% of max (not near exhaustion)? | Ideally yes | |
| 8 | Does the agent note that CPU oscillation (41-72%) is normal load variation? | Ideally yes | |
| 9 | Did the agent complete in ≤ 3 investigation loops? | Yes | |

### Known Pitfalls
- **Adversarial test:** Multiple metrics oscillate near thresholds — agent must resist diagnosing a problem
- Depends on `HEALTHY_SHORT_CIRCUIT=true` (default) for deterministic results
- The alert itself says "No errors reported" — agent should take this signal seriously

---

## 008-storage-full-missing-metric

**Run:** `opensre tests synthetic --scenario 008-storage-full-missing-metric`

**Scenario:** Same root cause as 003 (storage full) but **FreeStorageSpace metric is
absent** from the CloudWatch fixture, simulating a collection gap. The agent must infer
storage exhaustion from indirect evidence.

**Alert summary:** _"WriteLatency on billing-prod has risen to 30+ seconds and WriteIOPS dropped to zero. CloudWatch storage metric collection appears to have a gap."_

### Q&A Checklist

| # | Question | Expected Answer | Pass/Fail |
|---|----------|-----------------|-----------|
| 1 | Did the agent return a non-empty root cause? | Yes | |
| 2 | Is `ROOT_CAUSE_CATEGORY` set to `resource_exhaustion`? | Yes | |
| 3 | Does the output mention "storage"? | Yes — required keyword | |
| 4 | Does the output mention "storage space"? | Yes — required keyword | |
| 5 | Did the agent consult RDS events? | Yes — required evidence source | |
| 6 | Does the agent cite the RDS event "DB instance ran out of storage space"? | Ideally yes — this is the key indirect evidence | |
| 7 | Does the agent note that FreeStorageSpace is absent/missing? | Ideally yes — the agent should acknowledge the collection gap | |
| 8 | Does the agent use WriteIOPS collapsing to 0 and WriteLatency spiking as indirect evidence? | Yes — these are the observable symptoms when the metric is missing | |
| 9 | Did the agent complete in ≤ 3 investigation loops? | Yes | |

### Known Pitfalls
- **Difficulty 3 test:** The primary metric (FreeStorageSpace) is missing — agent must reason from indirect signals
- Agent should NOT conclude "unknown" just because the key metric is absent
- The RDS event at 03:08:44Z is definitive confirmation

---

## 009-dual-fault-connection-cpu

**Run:** `opensre tests synthetic --scenario 009-dual-fault-connection-cpu`

**Scenario:** Connections and CPU are both critical, but they share a **single causal root** —
a connection pool leak. Leaked connections hold open scan-heavy queries that consume CPU.
This is NOT two independent problems.

**Alert summary:** _"search-prod is approaching connection limit (95%+ of max) while CPUUtilization is simultaneously at 88-94%. Both metrics crossed critical thresholds."_

### Q&A Checklist

| # | Question | Expected Answer | Pass/Fail |
|---|----------|-----------------|-----------|
| 1 | Did the agent return a non-empty root cause? | Yes | |
| 2 | Is `ROOT_CAUSE_CATEGORY` set to `resource_exhaustion`? | Yes | |
| 3 | Does the output mention "connection"? | Yes — required keyword | |
| 4 | Does the output mention "CPU"? | Yes — required keyword | |
| 5 | Does the output mention "idle"? | Yes — required keyword | |
| 6 | Does the output mention "query"? | Yes — required keyword | |
| 7 | Did the agent consult Performance Insights? | Yes — required evidence source | |
| 8 | Does the agent identify the **connection pool leak** as the single shared root cause? | Yes — this is the key insight | |
| 9 | Does the agent explain that CPU saturation is **caused by** the leaked connections holding scan-heavy queries? | Yes — they are NOT independent faults | |
| 10 | Does the agent avoid mentioning "storage" or "replication" as causes? | Yes — forbidden keywords | |
| 11 | Does the agent reference `Client:ClientRead` as the dominant wait event? | Ideally yes | |
| 12 | Did the agent complete in ≤ 3 investigation loops? | Yes | |

### Known Pitfalls
- **Difficulty 4 (hardest):** Agent must identify the causal link between connections and CPU
- A naive agent will diagnose "two independent problems" — the correct answer is ONE shared root
- `Client:ClientRead` in PI proves the connections are idle (server finished, client not reading)

---

## 010-replication-lag-missing-metric

**Run:** `opensre tests synthetic --scenario 010-replication-lag-missing-metric`

**Scenario:** Same root cause as 001 (replication lag from WAL) but **ReplicaLag metric
is absent** from CloudWatch (recently provisioned replica). Agent must infer from RDS
events and Performance Insights.

**Alert summary:** _"Read replica reporting-prod-replica-1 is returning stale data. ReplicaLag CloudWatch metric is not publishing."_

### Q&A Checklist

| # | Question | Expected Answer | Pass/Fail |
|---|----------|-----------------|-----------|
| 1 | Did the agent return a non-empty root cause? | Yes | |
| 2 | Is `ROOT_CAUSE_CATEGORY` set to `resource_exhaustion`? | Yes | |
| 3 | Does the output mention "replication"? | Yes — required keyword | |
| 4 | Does the output mention "WAL"? | Yes — required keyword | |
| 5 | Does the output mention "replica"? | Yes — required keyword | |
| 6 | Did the agent consult RDS events? | Yes — required evidence source | |
| 7 | Did the agent consult Performance Insights? | Yes — required evidence source | |
| 8 | Does the agent cite RDS events showing lag exceeded 900s then 1800s? | Ideally yes | |
| 9 | Does the agent note ReplicaLag metric is absent/missing? | Ideally yes | |
| 10 | Does the agent identify WAL:Lock as the dominant wait event from PI? | Ideally yes | |
| 11 | Did the agent complete in ≤ 3 investigation loops? | Yes | |

### Known Pitfalls
- **Difficulty 3 test:** Like 008, the primary diagnostic metric is absent
- Agent must NOT conclude "unknown" — there are two strong indirect signals (RDS events + PI)
- TransactionLogsGeneration at ~195 MB/s is a key corroborating metric

---

## 011-cpu-storage-compositional

**Run:** `opensre tests synthetic --scenario 011-cpu-storage-compositional`

> **Axis 2 scenario** — uses `SelectiveGrafanaBackend`; agent must request the right
> metrics and explicitly rule out alternatives.

**Scenario:** **Two independent faults** are active simultaneously: (1) CPU saturation from
an analytics aggregation query, and (2) storage exhaustion from an audit_log INSERT job.
Connection growth and ReplicaLag elevation are **symptoms**, not independent faults.

**Alert summary:** _"analytics-prod is showing simultaneous high CPU (91%) and rapidly declining FreeStorageSpace (8 GB remaining)."_

### Q&A Checklist

| # | Question | Expected Answer | Pass/Fail |
|---|----------|-----------------|-----------|
| 1 | Did the agent return a non-empty root cause? | Yes | |
| 2 | Is `ROOT_CAUSE_CATEGORY` set to `resource_exhaustion`? | Yes | |
| 3 | Does the output mention "CPU"? | Yes — required keyword | |
| 4 | Does the output mention "storage"? | Yes — required keyword | |
| 5 | Does the output mention "analytics"? | Yes — required keyword | |
| 6 | Does the output mention "audit_log"? | Yes — required keyword | |
| 7 | Does the agent avoid diagnosing `connection_exhaustion`? | Yes — forbidden category | |
| 8 | Did the agent consult Performance Insights? | Yes — required evidence source | |
| 9 | Does the agent rule out **connection exhaustion** (mentioning "connection" as symptom, not root cause)? | Yes — ruling_out_keyword | |
| 10 | Does the agent rule out **replication lag** as an independent problem (mentioning it as a downstream symptom)? | Yes — ruling_out_keyword | |
| 11 | Does the agent acknowledge **two** independent root causes (compositional fault)? | Yes — ruling_out_keyword | |
| 12 | Does the agent identify the two **specific workloads** (analytics SELECT + audit_log INSERT)? | Ideally yes | |
| 13 | Did the agent complete in ≤ 3 investigation loops? | Yes | |

### Known Pitfalls
- **Difficulty 4 + Axis 2:** Hardest category — agent must identify TWO independent root causes
- Connection spike (148→563) is caused by blocked writers — NOT connection exhaustion
- ReplicaLag growth (1s→196s) is downstream of the write burst — NOT independent replication failure
- The two faults are **coincidental** (unrelated scheduled jobs that ran at the same time)

---

## 012-replication-lag-misleading-events

**Run:** `opensre tests synthetic --scenario 012-replication-lag-misleading-events`

> **Axis 2 scenario** — uses `SelectiveGrafanaBackend`.

**Scenario:** Replication lag from ETL bulk INSERT, but the RDS event stream contains
**three historical infrastructure events** (maintenance, failover, replica promotion)
that all completed hours before the current incident. A naive agent will blame the
failover.

**Alert summary:** _"ReplicaLag on reporting-prod-replica-1 has exceeded 900 seconds. Replica reads are severely stale."_

### Q&A Checklist

| # | Question | Expected Answer | Pass/Fail |
|---|----------|-----------------|-----------|
| 1 | Did the agent return a non-empty root cause? | Yes | |
| 2 | Is `ROOT_CAUSE_CATEGORY` set to `resource_exhaustion`? | Yes | |
| 3 | Does the output mention "replication lag"? | Yes — required keyword | |
| 4 | Does the output mention "WAL"? | Yes — required keyword | |
| 5 | Does the output mention "replica"? | Yes — required keyword | |
| 6 | Does the output mention "ETL"? | Yes — required keyword | |
| 7 | Does the agent avoid diagnosing `infrastructure`? | Yes — **forbidden category** | |
| 8 | Did the agent consult RDS events? | Yes — required evidence source | |
| 9 | Did the agent consult Performance Insights? | Yes — required evidence source | |
| 10 | Does the agent mention the historical **failover** but correctly dismiss it as resolved? | Yes — ruling_out_keyword | |
| 11 | Does the agent identify WAL replay bottleneck as the active cause? | Yes — ruling_out_keyword | |
| 12 | Does the agent address the **replica** specifically? | Yes — ruling_out_keyword | |
| 13 | Does the agent characterize the historical events as "completed" / "resolved" / "historical"? | Yes — must dismiss them, not blame them | |
| 14 | Did the agent complete in ≤ 3 investigation loops? | Yes | |

### Known Pitfalls
- **Critical adversarial test:** Three distracting infrastructure events in the RDS event log
- Agent must check timestamps — all three events completed **hours** before the current lag
- The ETL job starting at 13:00Z coincides exactly with the lag onset — this is the true cause
- Mild CPU elevation (~40%) is a symptom of the write-heavy ETL, not independent cpu_saturation

---

## 013-storage-recovery-false-alert

**Run:** `opensre tests synthetic --scenario 013-storage-recovery-false-alert`

> **Axis 2 scenario** — uses `SelectiveGrafanaBackend`.

**Scenario:** FreeStorageSpace dropped to ~3.5 GB during a write burst, but **storage
autoscaling** expanded the volume and the system has already recovered. The alert is
**stale** — no active failure exists at investigation time.

**Alert summary:** _"FreeStorageSpace on orders-prod dropped below 10 GB threshold. Storage autoscaling triggered and volume has been expanded."_

### Q&A Checklist

| # | Question | Expected Answer | Pass/Fail |
|---|----------|-----------------|-----------|
| 1 | Did the agent return a non-empty root cause? | Yes — should state "no active failure" / healthy | |
| 2 | Is `ROOT_CAUSE_CATEGORY` set to `healthy`? | Yes | |
| 3 | Does the output mention "recovered"? | Yes — required keyword | |
| 4 | Does the output mention "autoscal" (autoscaling/autoscaled)? | Yes — required keyword | |
| 5 | Does the output mention "no active" (failure/issue)? | Yes — required keyword | |
| 6 | Did the agent consult RDS events? | Yes — required evidence source | |
| 7 | Does the agent rule out **resource_exhaustion** (confirming storage has recovered)? | Yes — ruling_out_keyword | |
| 8 | Does the agent attribute recovery to **autoscaling**? | Yes — ruling_out_keyword | |
| 9 | Does the agent conclude there is **no active** failure at investigation time? | Yes — ruling_out_keyword | |
| 10 | Does the agent note the alert fired during the pressure window and is now stale? | Ideally yes | |
| 11 | Did the agent complete in ≤ 3 investigation loops? | Yes | |

### Known Pitfalls
- **Key insight:** The alert is stale — the problem self-resolved before investigation
- Agent must NOT diagnose storage exhaustion when FreeStorageSpace shows 200 GB at investigation time
- The dramatic spike-and-recovery pattern in FreeStorageSpace is alarming but already resolved
- WriteLatency elevation was brief and has returned to baseline

---

## 014-checkpoint-storm-cpu-saturation

**Run:** `opensre tests synthetic --scenario 014-checkpoint-storm-cpu-saturation`

> **Axis 2 scenario** — uses `SelectiveGrafanaBackend`.

**Scenario:** CPU is at 92% and the alert fired on CPU — but the **true root cause**
is a runaway `VACUUM FREEZE` on a large table that triggered checkpoint storms. CPU
saturation is a **symptom** of the I/O storm, not the root cause. An agent that
diagnoses `cpu_saturation` gets the causal chain backwards.

**Alert summary:** _"CPUUtilization on billing-prod has been above 88% for 15 minutes. Query response times are degraded."_

### Q&A Checklist

| # | Question | Expected Answer | Pass/Fail |
|---|----------|-----------------|-----------|
| 1 | Did the agent return a non-empty root cause? | Yes | |
| 2 | Is `ROOT_CAUSE_CATEGORY` set to `resource_exhaustion`? | Yes | |
| 3 | Does the output mention "vacuum"? | Yes — required keyword | |
| 4 | Does the output mention "checkpoint"? | Yes — required keyword | |
| 5 | Does the output mention "LWLock"? | Yes — required keyword | |
| 6 | Does the output mention "WAL"? | Yes — required keyword | |
| 7 | Does the agent avoid diagnosing `cpu_saturation`? | Yes — **forbidden category** | |
| 8 | Did the agent consult Performance Insights? | Yes — required evidence source | |
| 9 | Does the agent identify **VACUUM FREEZE** as the initiating process? | Yes — ruling_out_keyword | |
| 10 | Does the agent name **checkpoint storms** as the mechanism? | Yes — ruling_out_keyword | |
| 11 | Does the agent cite **LWLock:BufferMapping** as the dominant wait event (not CPU:user)? | Yes — ruling_out_keyword | |
| 12 | Does the agent explain that CPU elevation is a **downstream symptom** of the I/O storm? | Yes — the causal chain must go VACUUM → checkpoints → I/O storm → CPU | |
| 13 | Does the agent note that `CPU:user` is only 0.2 AAS (proving this is I/O-bound)? | Ideally yes | |
| 14 | Did the agent complete in ≤ 3 investigation loops? | Yes | |

### Known Pitfalls
- **Hardest adversarial test (Difficulty 4 + Axis 2):** The alert explicitly says "CPU" — agent must look deeper
- An agent that stops at "CPU is high" will get the wrong answer
- The dominant wait event `LWLock:BufferMapping` proves this is I/O-bound, not CPU-bound
- `rdsadmin` user (autovacuum) accounts for 7.9 AAS — the load is internal, not from application queries
- Connection growth (98→254) is from blocked INSERT workload, not a connection pool issue

---

## Summary: Common Bug Patterns to Watch For

When reviewing agent output across all scenarios, watch for these recurring issues:

1. **Confidence 0%** — Agent returns a root cause but confidence scoring is broken
2. **"Grafana integration not configured"** — Mock Grafana backend not being injected properly
3. **Diagnosing too fast** — Agent skips evidence gathering and jumps to conclusions from the alert title alone
4. **Missing evidence consultation** — Agent produces keywords that match but didn't actually query the required evidence sources
5. **Forbidden category violations** — Agent falls for adversarial signals (especially CPU red herrings in 006, 007, 014)
6. **Causal chain direction** — Agent gets the cause/symptom relationship backwards (especially 009, 011, 014)
7. **Stale alert handling** — Agent doesn't check if the problem has already resolved (013)
8. **Missing metric panic** — Agent gives up when a key metric is absent instead of reasoning from indirect evidence (008, 010)

## Filing Issues

When you find a bug, open a GitHub issue at `https://github.com/Tracer-Cloud/opensre/issues` with:

- **Title:** `[synthetic] <scenario-id>: <short description of bug>`
- **Body:**
  - Scenario ID and name
  - Which Q&A question(s) failed
  - The agent's actual output (relevant excerpt)
  - The expected behavior from `answer.yml`
  - Any error messages from the CLI
