"""Interactive CLI for Boundrix Runtime Authorization Demo."""

import sys
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

GREEN = "\033[92m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def run_interactive():
    base_dir = Path(__file__).resolve().parent.parent
    policy_path = base_dir / "policies" / "coding_agent_policy.json"
    audit_path = base_dir / "audit.jsonl"

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
    print(f"{BOLD}Boundrix Runtime Authorization — Interactive Mode{RESET}")
    print(f"Task: {task.description}")
    print(f"Type 'exit' or 'quit' to finish. Type 'revoke' to revoke the task.")
    print(f"{BOLD}========================================================{RESET}\n")

    counter = 0
    while True:
        try:
            action = input(f"{BOLD}Enter action (e.g. read, modify, create_pull_request, delete_branch):{RESET}\n> ").strip()
            if not action or action.lower() in ("exit", "quit"):
                print("\nExiting interactive mode. Goodbye!")
                break

            if action.lower() == "revoke":
                authorizer.revoke_task(task.id)
                print(f"\n{RED}{BOLD}Task {task.id} has been REVOKED.{RESET}\n")
                continue

            if action.lower() == "activate":
                authorizer.set_task_state(task.id, "ACTIVE")
                print(f"\n{GREEN}{BOLD}Task {task.id} is now ACTIVE.{RESET}\n")
                continue

            resource = input(f"{BOLD}Enter resource (e.g. github://acme/auth-service, github://acme/billing-service, iam://prod):{RESET}\n> ").strip()
            if not resource:
                continue

            branch = input(f"{BOLD}Enter branch (optional, default: bugfix/token-expiration):{RESET}\n> ").strip()
            if not branch:
                branch = "bugfix/token-expiration"

            counter += 1
            req = AuthorizationRequest(
                request_id=f"req-interactive-{counter:03d}",
                identity=identity,
                delegator=delegator,
                task=task,
                intent="interactive test",
                delegation_path=delegation_path,
                resource=resource,
                action=action,
                context={"branch": branch},
            )

            decision = authorizer.evaluate(req)
            decision_color = GREEN if decision.decision.value == "ALLOW" else RED

            print(f"\nDecision: {decision_color}{BOLD}{decision.decision.value}{RESET}")
            if decision.reason:
                print(f"Reason: {decision.reason}")
            print("-" * 50 + "\n")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting interactive mode.")
            break


if __name__ == "__main__":
    run_interactive()
