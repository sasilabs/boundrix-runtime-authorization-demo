"""Data models for Boundrix Runtime Authorization Demo."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class Decision(str, Enum):
    """Authorization decision outcome."""
    ALLOW = "ALLOW"
    DENY = "DENY"


class AuthorizationState(str, Enum):
    """Task-level runtime authorization state."""
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


@dataclass(frozen=True)
class Identity:
    """Represents the actor identity requesting an action."""
    type: str  # e.g. "agent", "human", "tool"
    id: str    # e.g. "coding-agent-01"


@dataclass(frozen=True)
class Delegator:
    """Represents the entity delegating the task."""
    type: str  # e.g. "human", "agent"
    id: str    # e.g. "developer-01"


@dataclass(frozen=True)
class Task:
    """Represents the specific delegated task."""
    id: str
    description: str


@dataclass
class AuthorizationRequest:
    """Represents an authorization request evaluated at the execution boundary."""
    request_id: str
    identity: Identity
    delegator: Delegator
    task: Task
    intent: str
    delegation_path: List[str]
    resource: str
    action: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AuthorizationDecision:
    """The result of a policy evaluation."""
    decision: Decision
    reason: str
    policy_id: str
    authorization_id: str
    request_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "policy": self.policy_id,
            "authorization_id": self.authorization_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
        }
