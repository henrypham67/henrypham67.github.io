---
title: 'Raft'
date: 2026-02-14T17:52:20+07:00
draft: true
---

### Applying the 80/20 Principle to Learning Raft

As a Senior DevOps Engineer, you're likely dealing with distributed systems like etcd (which uses Raft for consensus) or similar tools in Kubernetes clusters, where understanding Raft helps troubleshoot replication issues, leader elections, and fault tolerance. The 80/20 rule (Pareto Principle) means we'll focus on the **20% of Raft's concepts that deliver 80% of the practical value**. This boils down to grasping the core mechanics without drowning in edge cases like cluster membership changes or snapshotting (which are important but secondary for initial mastery).

From the algorithm's design, the high-leverage 20% is:
- **Node Roles and States** (foundation for everything).
- **Leader Election** (handles failures and starts consensus).
- **Log Replication** (ensures data consistency across nodes).
- **Safety Rules** (prevents inconsistencies, but minimally—focus on commit invariants).

We'll skip deep dives into RPC details or proofs unless they tie directly to these. For memorization, I'll use structured breakdowns, mnemonics, and visuals. Think of Raft as a "democratic dictatorship": Elect a strong leader quickly, then let it dictate logs to passive followers.

#### 1. Core Foundation: Node Roles and Terms (10% effort, 40% understanding)
Raft runs on a cluster of nodes (odd number recommended, e.g., 3-5 for quorum). Each node is in one of three states:
- **Follower**: Passive; receives updates from the leader. Most nodes stay here 99% of the time.
- **Candidate**: Temporary; actively seeks votes to become leader during elections.
- **Leader**: Active; handles all client requests, replicates logs, and sends heartbeats.

Mnemonic: **F**ollowers **C**almly **L**isten (Follower, Candidate, Leader).

Every action happens in a **term** (a monotonically increasing number, like a logical clock). Terms prevent old leaders from causing chaos—higher term always wins.

Key invariant: At most one leader per term.

This setup simplifies consensus: Leaders centralize decisions, reducing complexity compared to peer-to-peer algorithms.




(Above: Visual of state transitions—memorize the arrows: Timeout from Follower to Candidate; majority votes to Leader; higher term or lost majority back to Follower.)

#### 2. Leader Election (30% effort, 30% understanding)
This is Raft's "heartbeat"—it ensures a leader exists and recovers from failures.

Process:
- All start as Followers.
- Followers expect **heartbeats** (empty AppendEntries RPCs) from the leader every ~150-300ms.
- If no heartbeat (timeout, randomized to avoid ties), Follower becomes Candidate:
  - Increments its term.
  - Votes for itself.
  - Sends **RequestVote RPC** to all others: "Vote for me if your term is <= mine and your log is not more up-to-date."
- Others grant vote if candidate's term is higher and log is at least as current (prioritizes the most "informed" node).
- Candidate wins with **majority quorum** (e.g., 3/5 votes), becomes Leader, sends heartbeats.
- Split votes? Election restarts with new terms.

Mnemonic: **T**imeout **V**otes **M**ajority (TVM)—Timeout triggers Votes, Majority wins.

Practical DevOps tip: In production, tune timeouts for network latency; too short causes flapping elections, wasting resources.




(Above: Leader with followers—visualize the leader as the hub sending heartbeats downward.)

#### 3. Log Replication (40% effort, 20% understanding)
Once elected, the leader manages a replicated log (sequence of commands, like "set key=val").

Process:
- Client sends command to leader.
- Leader appends to its log, assigns index and term.
- Sends **AppendEntries RPC** to followers (includes prev log index/term for consistency check).
- Followers append if prev matches (rejects if gap—leader backfills).
- When majority acknowledge, leader **commits** the entry (applies to state machine) and notifies followers.
- Followers apply committed entries in order.

Key metrics:
- **nextIndex**: Leader tracks per-follower what to send next.
- **matchIndex**: Highest replicated index per follower.
- **commitIndex**: Highest safe-to-apply index (majority replicated).

Mnemonic: **A**ppend **C**ommit **A**pply (ACA)—Append to log, Commit on majority, Apply to state.

DevOps relevance: Logs are your audit trail; replication ensures high availability (tolerates f failures in 2f+1 nodes).




(Above: Nodes sharing a central state—think of the log as the "state" arrowed between processes.)

#### 4. Safety Essentials (20% effort, 10% understanding)
Raft guarantees **linearizability** (commands appear in a single order) via:
- **Election Safety**: One leader per term.
- **Leader Append-Only**: Leaders never overwrite logs.
- **Log Matching**: If logs match up to an index, they match forever.
- **State Machine Safety**: Committed entries are never changed.
- **Leader Completeness**: New leaders have all prior committed entries.

Mnemonic: **No Overwrites, Majority Rules** (NOMR).

Edge case to memorize: If a leader crashes mid-replication, the new leader won't commit incomplete entries from old terms until safe.

#### Memorization and Practice Tips
- **80/20 Drill**: Review the mnemonics daily (FCL, TVM, ACA, NOMR)—5 minutes covers 80% retention.
- **Visual Anchors**: Revisit the diagrams; associate states with colors (blue Follower, yellow Candidate, green Leader).
- **Hands-On**: Implement a toy Raft in Python (use threading for nodes, queues for RPCs). Focus on election and simple replication first—ignore persistence.
- **Test Yourself**: Quiz: "What happens if two candidates tie?" (New election, higher terms.) Or "How does a follower catch up?" (Leader sends missing entries.)
- **Resources for Depth**: If needed, dive into the original paper for proofs, but 80% of ops value is in ops simulations (try raft.github.io visualizations).

This focused approach should get you operational with Raft in hours, not days. Apply it to real systems like debugging etcd leader changes in logs. If you have a specific scenario (e.g., in Kubernetes), let me know for tailored examples.
