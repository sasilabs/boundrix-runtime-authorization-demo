# Security Model & Principles

This document outlines the core security principles demonstrated by the Boundrix Runtime Authorization Engine.

---

## 1. Zero Standing Privilege & Task-Scoped Authority
* **Principle**: Agents should hold zero permanent, unrestricted administrative tokens.
* **Mechanism**: Every agent operation is bound to a single-purpose `Task` with explicit resource boundaries (`github://acme/auth-service`), action lists (`read`, `modify`, `create_pull_request`), and branch patterns (`bugfix/*`).
* **Invariant**: An identity having valid credentials does **not** imply authority to execute unassigned actions or touch unassigned repositories.

---

## 2. Execution-Boundary Re-Authorization (No Cached Authorizations)
* **Principle**: Authorization is continuous, not one-time.
* **Mechanism**: An `ALLOW` on `read` does not implicitly authorize `modify` or `create_pull_request`. Every action must be evaluated at runtime immediately before invocation.

---

## 3. Real-Time Revocation (Kill Switch)
* **Principle**: When a supervisor revokes a task, the agent's authority must terminate immediately without needing emergency key rotation.
* **Mechanism**: Setting the task state to `REVOKED` causes the very next authorization check to return `DENY: Task authorization has been revoked`.

---

## 4. Lineage & Delegation Awareness
* **Principle**: Authority is derived from a principal delegation and must not be hijacked by unauthorized intermediaries or privileged tools.
* **Mechanism**: Requests carry an explicit `delegation_path` (`["developer-01", "coding-agent-01", "github-tool"]`). Unexpected or unauthorized tools in the delegation chain result in immediate `DENY`.

---

## 5. Fail-Closed by Default
* **Principle**: In the event of an unresolvable policy, unrecognized path, or out-of-scope resource, the authorizer defaults to `DENY`.

---

## 6. Auditability & Non-Repudiation
* **Principle**: Every authorization attempt (whether `ALLOW` or `DENY`) must generate structured, accountable audit evidence for subsequent security review.
