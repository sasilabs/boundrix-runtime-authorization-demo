"""Unit tests for mid-task revocation and kill switch behavior."""

import pytest
from pathlib import Path
from src.audit import AuditLogger
from src.authorizer import RuntimeAuthorizer
from src.models import (
    AuthorizationRequest,
    AuthorizationState,
    Decision,
    Delegator,
    Identity,
    Task,
)
from src.policy import Policy


@pytest.fixture
def authorizer():
    base_dir = Path(__file__).resolve().parent.parent
    policy_path = base_dir / "policies" / "coding_agent_policy.json"
    policy = Policy.from_file(policy_path)
    audit_logger = AuditLogger(log_filepath=None)
    return RuntimeAuthorizer(policy=policy, audit_logger=audit_logger)


def test_mid_task_revocation_lifecycle(authorizer):
    """Verifies that an active task allows actions, but instant revocation denies subsequent actions."""
    task = Task(id="task-rev-test-01", description="Fix auth bug")
    identity = Identity(type="agent", id="coding-agent-01")
    delegator = Delegator(type="human", id="developer-01")

    # Step 1: Initial state is ACTIVE -> ALLOW
    req1 = AuthorizationRequest(
        request_id="req-rev-1",
        identity=identity,
        delegator=delegator,
        task=task,
        intent="modify code",
        delegation_path=["developer-01", "coding-agent-01"],
        resource="github://acme/auth-service",
        action="modify",
        context={"branch": "bugfix/token-expiration"},
    )
    dec1 = authorizer.evaluate(req1)
    assert dec1.decision == Decision.ALLOW

    # Step 2: Revoke task
    authorizer.revoke_task(task.id)
    assert authorizer.get_task_state(task.id) == AuthorizationState.REVOKED

    # Step 3: Next action on revoked task -> DENY
    req2 = AuthorizationRequest(
        request_id="req-rev-2",
        identity=identity,
        delegator=delegator,
        task=task,
        intent="create PR",
        delegation_path=["developer-01", "coding-agent-01"],
        resource="github://acme/auth-service",
        action="create_pull_request",
        context={"branch": "bugfix/token-expiration"},
    )
    dec2 = authorizer.evaluate(req2)
    assert dec2.decision == Decision.DENY
    assert "Task authorization has been revoked" in dec2.reason
