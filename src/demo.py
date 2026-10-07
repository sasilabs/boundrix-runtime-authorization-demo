"""Runnable Demonstration of Boundrix Task-Scoped Runtime Authorization."""

import os
from pathlib import Path
from src.audit import AuditLogger
from src.authorizer import RuntimeAuthorizer
from src.models import (
    AuthorizationRequest,
    Delegator,
    Identity,
    Task,
)
from src.policy import Policy

# ANSI Colors for clear terminal visibility
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def run_demo():
    # Resolve policy path
    base_dir = Path(__file__).resolve().parent.parent
    policy_path = base_dir / "policies" / "coding_agent_policy.json"
    audit_path = base_dir / "audit.jsonl"

    # Initialize components
    policy = Policy.from_file(policy_path)
    audit_logger = AuditLogger(log_filepath=audit_path)
    authorizer = RuntimeAuthorizer(policy=policy, audit_logger=audit_logger)

    identity = Identity(type="agent", id="coding-agent-01")
    delegator = Delegator(type="human", id="developer-01")
    task = Task(
        id="task-001",
        description="Fix auth bug in auth-service and create a pull request",
    )
    delegation_path = ["developer-01", "coding-agent-01"]

    print(f"\n{BOLD}========================================================{RESET}")
    print(f"{BOLD}{CYAN}BOUNDRIX Runtime Authorization Demo{RESET}")
    print(f"{BOLD}========================================================{RESET}\n")

    print(f"{BOLD}Task:{RESET}\n{task.description}\n")
    print(f"{BOLD}Delegator:{RESET}\n{delegator.id}\n")
    print(f"{BOLD}Agent:{RESET}\n{identity.id}\n")
    print(f"{BOLD}Policy:{RESET}\n{policy.policy_id}\n")

    # -------------------------------------------------------------
    # Standard Scenarios (REQUEST 1 to REQUEST 7)
    # -------------------------------------------------------------
    requests_data = [
        {
            "id": "req-001",
            "action": "read",
            "resource": "github://acme/auth-service",
            "context": {"branch": "bugfix/token-expiration"},
        },
        {
            "id": "req-002",
            "action": "modify",
            "resource": "github://acme/auth-service",
            "context": {"branch": "bugfix/token-expiration"},
        },
        {
            "id": "req-003",
            "action": "run_tests",
            "resource": "github://acme/auth-service",
            "context": {"branch": "bugfix/token-expiration"},
        },
        {
            "id": "req-004",
            "action": "create_pull_request",
            "resource": "github://acme/auth-service",
            "context": {"branch": "bugfix/token-expiration"},
        },
        {
            "id": "req-005",
            "action": "modify",
            "resource": "github://acme/billing-service",
            "context": {"branch": "bugfix/token-expiration"},
        },
        {
            "id": "req-006",
            "action": "delete_branch",
            "resource": "github://acme/auth-service",
            "context": {"branch": "main"},
        },
        {
            "id": "req-007",
            "action": "modify_iam",
            "resource": "iam://production",
            "context": {"environment": "production"},
        },
    ]

    for i, req_info in enumerate(requests_data, start=1):
        req = AuthorizationRequest(
            request_id=req_info["id"],
            identity=identity,
            delegator=delegator,
            task=task,
            intent="fix authentication bug",
            delegation_path=delegation_path,
            resource=req_info["resource"],
            action=req_info["action"],
            context=req_info["context"],
        )

        decision = authorizer.evaluate(req)
        decision_color = GREEN if decision.decision.value == "ALLOW" else RED

        print("--------------------------------------------------------")
        print(f"{BOLD}REQUEST {i}{RESET}")
        print(f"Action: {req.action}")
        print(f"Resource: {req.resource}")
        if "branch" in req.context:
            print(f"Branch: {req.context['branch']}")
        print(f"\nDecision: {decision_color}{BOLD}{decision.decision.value}{RESET}")
        if decision.reason:
            print(f"Reason: {decision.reason}")
        print()

    # -------------------------------------------------------------
    # Mid-Task Revocation Scenario
    # -------------------------------------------------------------
    print(f"\n{BOLD}========================================================{RESET}")
    print(f"{BOLD}{YELLOW}MID-TASK REVOCATION DEMO{RESET}")
    print(f"{BOLD}========================================================{RESET}\n")

    print(f"Task:\n{task.description}\n")
    print(f"Initial authorization:\n{BOLD}{GREEN}ACTIVE{RESET}\n")

    # Allowed initial action
    req_active = AuthorizationRequest(
        request_id="req-rev-001",
        identity=identity,
        delegator=delegator,
        task=task,
        intent="fix authentication bug",
        delegation_path=delegation_path,
        resource="github://acme/auth-service",
        action="modify",
        context={"branch": "bugfix/token-expiration"},
    )
    dec_active = authorizer.evaluate(req_active)
    print("Action:\nmodify auth-service\n")
    print(f"Decision:\n{GREEN}{BOLD}{dec_active.decision.value}{RESET}\n")

    print("--------------------------------------------------------")
    print(f"{BOLD}Developer revokes task.{RESET}\n")
    authorizer.revoke_task(task.id)
    print(f"Authorization state:\n{RED}{BOLD}REVOKED{RESET}\n")
    print("--------------------------------------------------------")

    # Attempt action after revocation
    req_post_revoke = AuthorizationRequest(
        request_id="req-rev-002",
        identity=identity,
        delegator=delegator,
        task=task,
        intent="fix authentication bug",
        delegation_path=delegation_path,
        resource="github://acme/auth-service",
        action="create_pull_request",
        context={"branch": "bugfix/token-expiration"},
    )
    dec_post_revoke = authorizer.evaluate(req_post_revoke)
    print("Agent attempts:\n")
    print("Action:\ncreate_pull_request\n")
    print(f"Decision:\n{RED}{BOLD}{dec_post_revoke.decision.value}{RESET}\n")
    print(f"Reason:\n{dec_post_revoke.reason}\n")

    # -------------------------------------------------------------
    # Delegation / Lineage Scenario
    # -------------------------------------------------------------
    print(f"\n{BOLD}========================================================{RESET}")
    print(f"{BOLD}{CYAN}LINEAGE & DELEGATION PATH CHECK{RESET}")
    print(f"{BOLD}========================================================{RESET}\n")

    # Reset task state for clean test
    task_lineage = Task(id="task-lineage-001", description="Lineage verification task")
    authorizer.set_task_state(task_lineage.id, "ACTIVE")

    # Valid Lineage
    req_valid_lineage = AuthorizationRequest(
        request_id="req-lin-001",
        identity=identity,
        delegator=delegator,
        task=task_lineage,
        intent="authorized git tool operation",
        delegation_path=["developer-01", "coding-agent-01", "github-tool"],
        resource="github://acme/auth-service",
        action="read",
        context={"branch": "bugfix/token-expiration"},
    )
    dec_valid = authorizer.evaluate(req_valid_lineage)
    print(f"Delegation Path:\n{' ➔ '.join(req_valid_lineage.delegation_path)}")
    print(f"Decision: {GREEN}{BOLD}{dec_valid.decision.value}{RESET}\n")

    # Unexpected / Unauthorized Lineage (e.g. Privileged Admin Tool injection)
    req_invalid_lineage = AuthorizationRequest(
        request_id="req-lin-002",
        identity=identity,
        delegator=delegator,
        task=task_lineage,
        intent="unauthorized tool delegation",
        delegation_path=["developer-01", "coding-agent-01", "privileged-admin-tool"],
        resource="github://acme/auth-service",
        action="read",
        context={"branch": "bugfix/token-expiration"},
    )
    dec_invalid = authorizer.evaluate(req_invalid_lineage)
    print(f"Unexpected Delegation Path:\n{' ➔ '.join(req_invalid_lineage.delegation_path)}")
    print(f"Decision: {RED}{BOLD}{dec_invalid.decision.value}{RESET}")
    print(f"Reason: {dec_invalid.reason}\n")

    print(f"========================================================")
    print(f"Audit log generated at: {audit_path}")
    print(f"Total audit events recorded: {len(audit_logger.get_records())}")
    print(f"========================================================\n")


if __name__ == "__main__":
    run_demo()
