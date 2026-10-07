"""Unit tests for task-scoped runtime authorization decisions."""

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
    audit_logger = AuditLogger(log_filepath=None)  # In-memory only for tests
    return RuntimeAuthorizer(policy=policy, audit_logger=audit_logger)


@pytest.fixture
def base_request_data():
    return {
        "identity": Identity(type="agent", id="coding-agent-01"),
        "delegator": Delegator(type="human", id="developer-01"),
        "task": Task(id="task-001", description="Fix auth bug in auth-service and create a pull request"),
        "delegation_path": ["developer-01", "coding-agent-01"],
    }


def test_allowed_actions(authorizer, base_request_data):
    """Verifies that all actions within the task scope return ALLOW."""
    allowed_actions = ["read", "modify", "run_tests", "create_branch", "create_pull_request"]

    for i, action in enumerate(allowed_actions):
        req = AuthorizationRequest(
            request_id=f"req-allow-{i}",
            identity=base_request_data["identity"],
            delegator=base_request_data["delegator"],
            task=base_request_data["task"],
            intent="valid task action",
            delegation_path=base_request_data["delegation_path"],
            resource="github://acme/auth-service",
            action=action,
            context={"branch": "bugfix/token-expiration"},
        )
        decision = authorizer.evaluate(req)
        assert decision.decision == Decision.ALLOW
        assert "within delegated task scope" in decision.reason


def test_denied_unrelated_resource(authorizer, base_request_data):
    """Verifies that accessing an unrelated repository (billing-service) is DENIED."""
    req = AuthorizationRequest(
        request_id="req-deny-resource",
        identity=base_request_data["identity"],
        delegator=base_request_data["delegator"],
        task=base_request_data["task"],
        intent="unrelated service modification",
        delegation_path=base_request_data["delegation_path"],
        resource="github://acme/billing-service",
        action="modify",
        context={"branch": "bugfix/token-expiration"},
    )
    decision = authorizer.evaluate(req)
    assert decision.decision == Decision.DENY
    assert "outside delegated task scope" in decision.reason


def test_denied_delete_main_branch(authorizer, base_request_data):
    """Verifies that attempting to delete a branch or touching main branch is DENIED."""
    req = AuthorizationRequest(
        request_id="req-deny-delete-branch",
        identity=base_request_data["identity"],
        delegator=base_request_data["delegator"],
        task=base_request_data["task"],
        intent="delete branch",
        delegation_path=base_request_data["delegation_path"],
        resource="github://acme/auth-service",
        action="delete_branch",
        context={"branch": "main"},
    )
    decision = authorizer.evaluate(req)
    assert decision.decision == Decision.DENY
    assert "explicitly denied" in decision.reason


def test_denied_iam_modification(authorizer, base_request_data):
    """Verifies that IAM privilege modification is DENIED."""
    req = AuthorizationRequest(
        request_id="req-deny-iam",
        identity=base_request_data["identity"],
        delegator=base_request_data["delegator"],
        task=base_request_data["task"],
        intent="modify cloud iam",
        delegation_path=base_request_data["delegation_path"],
        resource="iam://production",
        action="modify_iam",
        context={"environment": "production"},
    )
    decision = authorizer.evaluate(req)
    assert decision.decision == Decision.DENY
    assert "IAM modification is outside delegated task authority" in decision.reason


def test_branch_restriction_enforcement(authorizer, base_request_data):
    """Verifies that modifying outside allowed branch pattern (e.g. main directly) is DENIED."""
    req = AuthorizationRequest(
        request_id="req-deny-branch-scope",
        identity=base_request_data["identity"],
        delegator=base_request_data["delegator"],
        task=base_request_data["task"],
        intent="modify main branch directly",
        delegation_path=base_request_data["delegation_path"],
        resource="github://acme/auth-service",
        action="modify",
        context={"branch": "main"},  # Not matching bugfix/*
    )
    decision = authorizer.evaluate(req)
    assert decision.decision == Decision.DENY
    assert "Branch is outside delegated authority" in decision.reason
