"""Unit tests for delegation path and lineage verification."""

import pytest
from pathlib import Path
from src.audit import AuditLogger
from src.authorizer import RuntimeAuthorizer
from src.models import (
    AuthorizationRequest,
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


def test_valid_delegation_path(authorizer):
    """Verifies that requests carrying authorized delegation paths are allowed."""
    task = Task(id="task-del-01", description="Delegation test")
    req = AuthorizationRequest(
        request_id="req-del-valid",
        identity=Identity(type="agent", id="coding-agent-01"),
        delegator=Delegator(type="human", id="developer-01"),
        task=task,
        intent="read repo",
        delegation_path=["developer-01", "coding-agent-01", "github-tool"],
        resource="github://acme/auth-service",
        action="read",
        context={"branch": "bugfix/token-expiration"},
    )
    decision = authorizer.evaluate(req)
    assert decision.decision == Decision.ALLOW


def test_unauthorized_delegation_path(authorizer):
    """Verifies that requests carrying unexpected or privileged tool hops are DENIED."""
    task = Task(id="task-del-02", description="Delegation test")
    req = AuthorizationRequest(
        request_id="req-del-invalid",
        identity=Identity(type="agent", id="coding-agent-01"),
        delegator=Delegator(type="human", id="developer-01"),
        task=task,
        intent="privileged tool invocation",
        delegation_path=["developer-01", "coding-agent-01", "privileged-admin-tool"],
        resource="github://acme/auth-service",
        action="read",
        context={"branch": "bugfix/token-expiration"},
    )
    decision = authorizer.evaluate(req)
    assert decision.decision == Decision.DENY
    assert "Delegation path is not authorized for this task" in decision.reason
