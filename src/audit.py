"""Audit logging for Boundrix Runtime Authorization decisions."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.models import AuthorizationDecision, AuthorizationRequest


class AuditLogger:
    """Appends authorization decision events to a structured audit store."""

    def __init__(self, log_filepath: Optional[str | Path] = "audit.jsonl"):
        self.log_filepath = Path(log_filepath) if log_filepath else None
        self._records: List[Dict[str, Any]] = []

    def log(self, request: AuthorizationRequest, decision: AuthorizationDecision) -> Dict[str, Any]:
        """Creates and appends an audit event."""
        event = {
            "timestamp": decision.timestamp,
            "authorization_id": decision.authorization_id,
            "request_id": request.request_id,
            "task_id": request.task.id,
            "identity": {
                "type": request.identity.type,
                "id": request.identity.id,
            },
            "delegator": {
                "type": request.delegator.type,
                "id": request.delegator.id,
            },
            "delegation_path": request.delegation_path,
            "intent": request.intent,
            "resource": request.resource,
            "action": request.action,
            "context": request.context,
            "decision": decision.decision.value,
            "reason": decision.reason,
            "policy_id": decision.policy_id,
        }

        self._records.append(event)

        if self.log_filepath:
            try:
                self.log_filepath.parent.mkdir(parents=True, exist_ok=True)
                with open(self.log_filepath, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event) + "\n")
            except Exception:
                pass  # Graceful fallback in read-only/test environments

        return event

    def get_records(self) -> List[Dict[str, Any]]:
        """Returns in-memory recorded audit events."""
        return list(self._records)

    def clear(self) -> None:
        """Clears in-memory audit records."""
        self._records.clear()
