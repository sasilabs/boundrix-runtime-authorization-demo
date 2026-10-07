# Boundrix Runtime Authorization Demo

A runnable, self-contained technical demonstration of **task-scoped runtime authorization** for autonomous AI coding agents.

---

## Why This Exists

As software teams deploy autonomous AI coding agents (such as Claude Code, Cursor, Devin, and custom ReAct agents), agents are granted write access to repositories and engineering tools. 

However, existing security models stop at identity authentication: once an agent is given an API token, it can take thousands of unsupervised actions across any resource permitted by that token.

This repository demonstrates the core concept of **Boundrix**:

> **An AI agent may have a valid identity and baseline permissions, but every consequential action must be evaluated at runtime against the active task, delegated authority, target resource, action verb, and execution context.**

---

## The Problem

Traditional access control answers:
> *"Does this identity have permission to access this resource?"*

Autonomous agents introduce a fundamentally different question:
> *"Should this agent perform this specific action for the task it was delegated, right now?"*

```text
Identity permission ≠ Task authority
```

When an agent is delegated a bug fix in `auth-service`, a standard API key or personal access token often allows:
* ✅ Modifying `auth-service` *(Intended)*
* ❌ Modifying `billing-service` or `customer-db` *(Unintended Scope-Creep)*
* ❌ Deleting the `main` branch *(Destructive Action)*
* ❌ Altering IAM roles or security policies *(Privilege Escalation)*

Prompt guardrails and system instructions are probabilistic and vulnerable to hallucinations or prompt injections. Teams need **deterministic execution boundaries**.

---

## Traditional IAM vs Runtime Authorization

| Dimension | Traditional IAM (Okta, GitHub RBAC, AWS IAM) | Boundrix Runtime Authorization |
| :--- | :--- | :--- |
| **Question Answered** | *"Who is the identity and what can it access globally?"* | *"Should this action execute for this active task right now?"* |
| **Scope Lifetime** | Permanent / Long-lived keys | Ephemeral, task-bound (15–60 min) |
| **Enforcement Point** | Front-door login & token issuance | At the execution boundary before each tool call |
| **Awareness** | Identity-aware | Task-scoped & Lineage-aware |
| **Kill Switch** | Manual token rotation / credential revocation | Instant task-level revocation denying the next action |

> **Note**: IAM provides identity and baseline permissions. Runtime authorization adds task-specific context to the authorization decision immediately before execution.

---

## Scenario

A developer delegates a task to an autonomous AI coding agent:
> *"Fix the authentication/token expiration bug in `auth-service` and create a pull request."*

The authorization engine intercepts every consequential action:

```text
Developer
   │
   │ Task: "Fix auth bug in auth-service"
   ▼
AI Coding Agent
   │
   ▼
Boundrix Runtime Authorization
   │
   ├── read auth-service          → ALLOW
   ├── modify auth-service        → ALLOW
   ├── run tests                  → ALLOW
   ├── create branch              → ALLOW
   ├── create pull request        → ALLOW
   │
   ├── read billing-service       → DENY  (Outside task scope)
   ├── modify billing-service     → DENY  (Outside task scope)
   ├── delete main branch         → DENY  (Explicitly forbidden)
   └── modify IAM                 → DENY  (Outside delegated authority)
```

---

## Architecture

```text
                         Developer
                             │
                             │ 1. Delegates task ("Fix auth bug in auth-service")
                             ▼
                     Autonomous AI Agent
                             │
                             │ 2. Action request (e.g., modify, create_pull_request)
                             ▼
              ┌──────────────────────────────┐
              │  Boundrix Runtime            │
              │  Authorization Boundary      │
              │                              │
              │ • Identity                   │
              │ • Task / Intent              │
              │ • Delegation Path / Lineage  │
              │ • Target Resource URI        │
              │ • Action Verb                │
              │ • Runtime Context (Branch)   │
              │ • Live Authorization State   │
              └──────────────┬───────────────┘
                             │
                    3. Evaluates (< 1ms)
                       ALLOW / DENY
                             │
                             ▼
                     Protected Tool (e.g., GitHub API)
                             │
                             ▼
                     Target Enterprise System
                             │
                             ▼
                     Structured Audit Event
```

The authorization layer sits at the **execution boundary**, immediately before protected external calls occur.

---

## How Authorization Works

The authorization engine evaluates decisions conceptually as:

```text
Authorization Decision =
    Evaluate(
        identity,
        task,
        intent,
        delegation_path,
        action,
        resource,
        context,
        current_authorization_state
    )
```

### Authorization Request Model

```json
{
  "request_id": "req-001",
  "identity": {
    "type": "agent",
    "id": "coding-agent-01"
  },
  "delegator": {
    "type": "human",
    "id": "developer-01"
  },
  "task": {
    "id": "task-001",
    "description": "Fix auth bug in auth-service and create a pull request"
  },
  "intent": "fix authentication bug",
  "delegation_path": [
    "developer-01",
    "coding-agent-01"
  ],
  "resource": "github://acme/auth-service",
  "action": "modify",
  "context": {
    "branch": "bugfix/token-expiration",
    "environment": "development"
  }
}
```

---

## Example Policy

Policies define mathematical boundaries for a delegated task (`policies/coding_agent_policy.json`):

```json
{
  "policy_id": "coding-agent-task-policy",
  "task": "Fix auth bug in auth-service and create a pull request",
  "allowed_resources": [
    "github://acme/auth-service"
  ],
  "allowed_actions": [
    "read",
    "modify",
    "create_branch",
    "run_tests",
    "create_pull_request"
  ],
  "allowed_branches": [
    "bugfix/*"
  ],
  "denied_resources": [
    "github://acme/billing-service",
    "iam://*"
  ],
  "denied_actions": [
    "delete_branch",
    "modify_iam"
  ],
  "authorized_delegation_paths": [
    ["developer-01", "coding-agent-01"],
    ["developer-01", "coding-agent-01", "github-tool"]
  ]
}
```

---

## Running the Demo

### Prerequisites
* Python 3.9+

### Quickstart

```bash
# 1. Clone the repository
git clone https://github.com/sasilabs/boundrix-runtime-authorization-demo.git
cd boundrix-runtime-authorization-demo

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install test dependencies
pip install -r requirements.txt

# 4. Run the demo
python3 -m src.demo
```

### Optional Interactive Mode

```bash
python3 -m src.interactive
```

---

## Example Output

```text
========================================================
BOUNDRIX Runtime Authorization Demo
========================================================

Task:
Fix auth bug in auth-service and create a pull request

Delegator:
developer-01

Agent:
coding-agent-01

Policy:
coding-agent-task-policy

--------------------------------------------------------
REQUEST 1
Action: read
Resource: github://acme/auth-service
Branch: bugfix/token-expiration

Decision: ALLOW
Reason: Resource and action are within delegated task scope

--------------------------------------------------------
REQUEST 2
Action: modify
Resource: github://acme/auth-service
Branch: bugfix/token-expiration

Decision: ALLOW
Reason: Resource and action are within delegated task scope

--------------------------------------------------------
REQUEST 3
Action: run_tests
Resource: github://acme/auth-service
Branch: bugfix/token-expiration

Decision: ALLOW
Reason: Resource and action are within delegated task scope

--------------------------------------------------------
REQUEST 4
Action: create_pull_request
Resource: github://acme/auth-service
Branch: bugfix/token-expiration

Decision: ALLOW
Reason: Resource and action are within delegated task scope

--------------------------------------------------------
REQUEST 5
Action: modify
Resource: github://acme/billing-service
Branch: bugfix/token-expiration

Decision: DENY
Reason: Resource is outside delegated task scope

--------------------------------------------------------
REQUEST 6
Action: delete_branch
Resource: github://acme/auth-service
Branch: main

Decision: DENY
Reason: Action 'delete_branch' is explicitly denied by task policy

--------------------------------------------------------
REQUEST 7
Action: modify_iam
Resource: iam://production

Decision: DENY
Reason: IAM modification is outside delegated task authority
```

---

## Mid-Task Revocation

Boundrix demonstrates that authority can be revoked **in real time while the task is active**:

```text
========================================================
MID-TASK REVOCATION DEMO
========================================================

Task:
Fix auth bug in auth-service and create a pull request

Initial authorization:
ACTIVE

Action:
modify auth-service

Decision:
ALLOW

--------------------------------------------------------
Developer revokes task.

Authorization state:
REVOKED
--------------------------------------------------------
Agent attempts:

Action:
create_pull_request

Decision:
DENY

Reason:
Task authorization has been revoked
```

> **Security Note**: Boundrix denies the *next* protected action when authorization is re-evaluated at the execution boundary. It does not terminate active TCP connections or modify downstream provider credentials.

---

## Delegation and Lineage

Boundrix requests carry provenance context (`delegation_path`). If an unexpected or unauthorized tool is injected into the delegation chain, the engine rejects the request:

```text
Expected Delegation Path:
developer-01 ➔ coding-agent-01 ➔ github-tool
Decision: ALLOW

Unexpected Delegation Path:
developer-01 ➔ coding-agent-01 ➔ privileged-admin-tool
Decision: DENY
Reason: Delegation path is not authorized for this task
```

---

## Audit Evidence

Every authorization check produces a structured audit record stored in `audit.jsonl`:

```json
{
  "timestamp": "2026-10-07T11:45:00.123456+00:00",
  "authorization_id": "authz-005",
  "request_id": "req-005",
  "task_id": "task-001",
  "identity": {
    "type": "agent",
    "id": "coding-agent-01"
  },
  "delegator": {
    "type": "human",
    "id": "developer-01"
  },
  "delegation_path": [
    "developer-01",
    "coding-agent-01"
  ],
  "intent": "fix authentication bug",
  "resource": "github://acme/billing-service",
  "action": "modify",
  "decision": "DENY",
  "reason": "Resource is outside delegated task scope",
  "policy_id": "coding-agent-task-policy"
}
```

---

## Running Tests

Run the test suite with `pytest`:

```bash
pytest
```

Output:
```text
============================= test session starts ==============================
collected 8 items

tests/test_authorization.py .....                                        [ 62%]
tests/test_delegation.py ..                                              [ 87%]
tests/test_revocation.py .                                               [100%]

============================== 8 passed in 0.04s ===============================
```

---

## What This Demonstrates

* ✅ **Least-Privilege Task Scoping**: Confinement to specific repos and actions.
* ✅ **Runtime Execution Boundary**: Evaluating before execution, not at login.
* ✅ **Mid-Task Revocation**: Immediate kill-switch halting the next action.
* ✅ **Delegation Lineage**: Awareness of the delegation chain.
* ✅ **Audit Flight Recorder**: Structured accountability for every decision.
* ✅ **Deterministic Logic**: Immune to LLM hallucinations and prompt injection.

---

## What This Does NOT Demonstrate

* ❌ Production cryptographic certificate signing.
* ❌ Raw Linux kernel syscall interception (eBPF/LSM).
* ❌ Network TCP/IP packet proxying.
* ❌ Real GitHub OAuth token issuance.

---

## Relation to Boundrix

This repository is an **educational, open-source technical demonstrator** designed to explain the core runtime authorization architecture of Boundrix.

The production Boundrix platform expands on these principles with:
* Multi-tenant policy distribution servers.
* Enterprise SDKs (Python, Java, Kotlin).
* Secret redaction & cryptographic flight logs.
* Human-in-the-Loop (`REQUIRE_APPROVAL`) interactive step-up workflows.
* Tool proxy gateways and Model Context Protocol (MCP) sidecars.

For more information, visit [https://boundrix.io](https://boundrix.io).

---

## Roadmap

* [ ] Human-in-the-loop interactive approval hooks (`REQUIRE_APPROVAL`).
* [ ] Model Context Protocol (MCP) gateway middleware example.
* [ ] Ephemeral credential broker integration (JIT GitHub App installation tokens).
* [ ] OpenTelemetry (OTel) audit export format.

---

## License

Apache 2.0 © 2026 SAS Labs (Boundrix). See [LICENSE](LICENSE) for details.
