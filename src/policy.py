"""Policy definitions and parsing for Boundrix Runtime Authorization Demo."""

import fnmatch
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Policy:
    """Represents a human-readable task-scoped security policy."""
    policy_id: str
    task: str
    allowed_resources: List[str] = field(default_factory=list)
    allowed_actions: List[str] = field(default_factory=list)
    allowed_branches: List[str] = field(default_factory=list)
    denied_resources: List[str] = field(default_factory=list)
    denied_actions: List[str] = field(default_factory=list)
    authorized_delegation_paths: List[List[str]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Policy":
        return cls(
            policy_id=data.get("policy_id", "default-policy"),
            task=data.get("task", ""),
            allowed_resources=data.get("allowed_resources", []),
            allowed_actions=data.get("allowed_actions", []),
            allowed_branches=data.get("allowed_branches", []),
            denied_resources=data.get("denied_resources", []),
            denied_actions=data.get("denied_actions", []),
            authorized_delegation_paths=data.get("authorized_delegation_paths", []),
        )

    @classmethod
    def from_file(cls, filepath: str | Path) -> "Policy":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def is_resource_denied(self, resource: str) -> bool:
        """Checks if the resource explicitly matches any denied patterns."""
        for pattern in self.denied_resources:
            if fnmatch.fnmatch(resource, pattern):
                return True
        return False

    def is_resource_allowed(self, resource: str) -> bool:
        """Checks if the resource matches allowed resource patterns."""
        for pattern in self.allowed_resources:
            if fnmatch.fnmatch(resource, pattern):
                return True
        return False

    def is_action_denied(self, action: str) -> bool:
        """Checks if the action is explicitly denied."""
        return action in self.denied_actions

    def is_action_allowed(self, action: str) -> bool:
        """Checks if the action is within allowed actions."""
        return action in self.allowed_actions

    def is_branch_allowed(self, branch: Optional[str]) -> bool:
        """Checks if the branch conforms to allowed branch patterns."""
        if not branch or not self.allowed_branches:
            return True
        for pattern in self.allowed_branches:
            if fnmatch.fnmatch(branch, pattern):
                return True
        return False

    def is_delegation_path_authorized(self, delegation_path: List[str]) -> bool:
        """Checks if the delegation path is recognized in authorized chains."""
        if not self.authorized_delegation_paths:
            return True
        return delegation_path in self.authorized_delegation_paths
