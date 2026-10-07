# Architecture Specification

## Overview

The **Boundrix Runtime Authorization Demo** models runtime authorization at the **execution boundary** between an autonomous AI agent and the tools or systems it attempts to invoke.

```text
                         Developer
                             │
                             │ 1. Delegates task ("Fix auth bug in auth-service")
                             ▼
                     Autonomous AI Agent
                             │
                             │ 2. Proposes action (e.g. modify, create_pull_request, repo.delete)
                             ▼
              ┌──────────────────────────────┐
              │  Boundrix Runtime            │
              │  Authorization Boundary      │
              │                              │
              │ • Identity                   │
              │ • Task / Intent              │
              │ • Delegation Path / Lineage  │
              │ • Resource URI               │
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

---

## The Execution Boundary Concept

In traditional architectures, permissions are checked when an API token or credentials are initially provisioned (at the "front door"). 

Boundrix places the authorization decision point at the **execution boundary** immediately before a consequential tool or system call is executed:

1. **Pre-Invocation Evaluation**: No cached grants. Every discrete mutation or query is evaluated independently.
2. **Task Confinement**: Authority exists only within the scope of the active task grant.
3. **Out-of-Band Policy Engine**: Boundrix evaluates whether the action is permitted. If `ALLOW`, the agent proceeds to invoke the tool; if `DENY`, the agent runtime halts without executing side-effects.

---

## Architectural Distinctions & Scope

* **Demonstrator Scope**: This demo models the policy evaluation engine, task states, lineage validation, and audit flight logging in pure Python.
* **Non-Proxy Architecture**: This demo does **not** act as a raw TCP/IP packet interceptor or kernel hook. It enforces at the software execution boundary (e.g., tool wrappers, SDK interceptors, API gateways).
