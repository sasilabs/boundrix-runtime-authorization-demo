"""Runtime Authorization Engine for Boundrix."""

import uuid
from typing import Dict, Optional
from src.audit import AuditLogger
from src.models import (
    AuthorizationDecision,
    AuthorizationRequest,
    AuthorizationState,
    Decision,
)
from src.policy import Policy


class RuntimeAuthorizer:
    """Evaluates consequential agent actions against active task policies and runtime state."""

    def __init__(self, policy: Policy, audit_logger: Optional[AuditLogger] = None):
        self.policy = policy
        self.audit_logger = audit_logger or AuditLogger()
        self._task_states: Dict[str, AuthorizationState] = {}
        self._auth_counter = 0

    def get_task_state(self, task_id: str) -> AuthorizationState:
        """Returns the current runtime authorization state for a task (default: ACTIVE)."""
        return self._task_states.get(task_id, AuthorizationState.ACTIVE)

    def set_task_state(self, task_id: str, state: AuthorizationState) -> None:
        """Updates the runtime authorization state for a task."""
        self._task_states[task_id] = state

    def revoke_task(self, task_id: str) -> None:
        """Instantly revokes task authority (simulates supervisor kill switch)."""
        self.set_task_state(task_id, AuthorizationState.REVOKED)

    def _next_auth_id(self) -> str:
        self._auth_counter += 1
        return f"authz-{self._auth_counter:03d}"

    def evaluate(self, request: AuthorizationRequest) -> AuthorizationDecision:
        """
        Evaluates an action request at the execution boundary.

        Decision = Evaluate(
            identity,
            task,
            intent,
            delegation_path,
            action,
            resource,
            context,
            current_authorization_state
        )
        """
        auth_id = self._next_auth_id()
        task_id = request.task.id

        # 1. Check Task Authorization State (Revocation Check)
        if self.get_task_state(task_id) == AuthorizationState.REVOKED:
            decision = AuthorizationDecision(
                decision=Decision.DENY,
                reason="Task authorization has been revoked",
                policy_id=self.policy.policy_id,
                authorization_id=auth_id,
                request_id=request.request_id,
            )
            self.audit_logger.log(request, decision)
            return decision

        # 2. Check Lineage / Delegation Path
        if not self.policy.is_delegation_path_authorized(request.delegation_path):
            decision = AuthorizationDecision(
                decision=Decision.DENY,
                reason="Delegation path is not authorized for this task",
                policy_id=self.policy.policy_id,
                authorization_id=auth_id,
                request_id=request.request_id,
            )
            self.audit_logger.log(request, decision)
            return decision

        # 3. Check Explicitly Denied Actions
        if self.policy.is_action_denied(request.action):
            if "iam" in request.action.lower() or "iam" in request.resource.lower():
                reason = "IAM modification is outside delegated task authority"
            else:
                reason = f"Action '{request.action}' is explicitly denied by task policy"
            decision = AuthorizationDecision(
                decision=Decision.DENY,
                reason=reason,
                policy_id=self.policy.policy_id,
                authorization_id=auth_id,
                request_id=request.request_id,
            )
            self.audit_logger.log(request, decision)
            return decision

        # 4. Check Explicitly Denied Resources
        if self.policy.is_resource_denied(request.resource):
            if "iam" in request.resource.lower() or "iam" in request.action.lower():
                reason = "IAM modification is outside delegated task authority"
            else:
                reason = "Resource is outside delegated task scope"
            decision = AuthorizationDecision(
                decision=Decision.DENY,
                reason=reason,
                policy_id=self.policy.policy_id,
                authorization_id=auth_id,
                request_id=request.request_id,
            )
            self.audit_logger.log(request, decision)
            return decision

        # 5. Check Allowed Resources
        if not self.policy.is_resource_allowed(request.resource):
            decision = AuthorizationDecision(
                decision=Decision.DENY,
                reason="Resource is outside delegated task scope",
                policy_id=self.policy.policy_id,
                authorization_id=auth_id,
                request_id=request.request_id,
            )
            self.audit_logger.log(request, decision)
            return decision

        # 6. Check Allowed Actions
        if not self.policy.is_action_allowed(request.action):
            decision = AuthorizationDecision(
                decision=Decision.DENY,
                reason=f"Action '{request.action}' is not permitted for this task",
                policy_id=self.policy.policy_id,
                authorization_id=auth_id,
                request_id=request.request_id,
            )
            self.audit_logger.log(request, decision)
            return decision

        # 7. Check Branch / Context Constraints
        branch = request.context.get("branch") if request.context else None
        if branch and not self.policy.is_branch_allowed(branch):
            decision = AuthorizationDecision(
                decision=Decision.DENY,
                reason="Branch is outside delegated authority",
                policy_id=self.policy.policy_id,
                authorization_id=auth_id,
                request_id=request.request_id,
            )
            self.audit_logger.log(request, decision)
            return decision

        # 8. All checks pass -> ALLOW
        decision = AuthorizationDecision(
            decision=Decision.ALLOW,
            reason="Resource and action are within delegated task scope",
            policy_id=self.policy.policy_id,
            authorization_id=auth_id,
            request_id=request.request_id,
        )
        self.audit_logger.log(request, decision)
        return decision
