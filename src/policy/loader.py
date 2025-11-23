"""
Policy loader and validator for FLEET-ONE conflict resolution.
Loads and validates signed policy JSON files with SHA-256 hash verification.
"""
import json
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path


class PolicyLoader:
    """Loads and validates policy files for conflict resolution."""

    def __init__(self, policy_file: str = "policy/scheduler_conflict_policy.json"):
        """
        Initialize policy loader.

        Args:
            policy_file: Path to policy JSON file
        """
        self.policy_file = policy_file
        self.policy: Optional[Dict[str, Any]] = None
        self.load_policy()

    def load_policy(self):
        """Load and verify policy file."""
        try:
            policy_path = Path(self.policy_file)
            if not policy_path.exists():
                raise FileNotFoundError(f"Policy file not found: {self.policy_file}")

            with open(policy_path, "r") as f:
                self.policy = json.load(f)

            # Verify hash if present
            if "hash" in self.policy:
                self._verify_hash()

        except Exception as e:
            raise RuntimeError(f"Failed to load policy: {e}")

    def _verify_hash(self):
        """Verify SHA-256 hash of policy content."""
        if not self.policy:
            return

        expected_hash = self.policy.get("hash")
        content = {k: v for k, v in self.policy.items() if k != "hash"}
        content_json = json.dumps(content, sort_keys=True, separators=(",", ":"))
        actual_hash = hashlib.sha256(content_json.encode()).hexdigest()

        if expected_hash != actual_hash:
            raise ValueError("Policy hash verification failed")

    def has_field_authority(self, role: str, field: str) -> bool:
        """
        Check if role has authority over a field.

        Args:
            role: User role (e.g., "workshop", "dispatcher")
            field: Field name (e.g., "actual_start_ts")

        Returns:
            True if role has authority over field
        """
        if not self.policy:
            return False

        field_authorities = self.policy.get("field_authorities", {})
        authoritative_role = field_authorities.get(field)
        return authoritative_role == role

    def get_conflict_rule(self, field: str) -> Optional[str]:
        """
        Get conflict resolution strategy for a field.

        Args:
            field: Field name

        Returns:
            Resolution strategy ("workshop_authoritative", "plan_conflict", etc.)
        """
        if not self.policy:
            return None

        rules = self.policy.get("rules", {})
        return rules.get(field)

    def can_role_update_field(self, role: str, field: str) -> bool:
        """
        Check if a role is allowed to update a field.

        Args:
            role: User role
            field: Field name

        Returns:
            True if role can update field
        """
        if not self.policy:
            return False

        permissions = self.policy.get("permissions", {})
        allowed_fields = permissions.get(role, [])
        return field in allowed_fields

    def resolve_conflict(
        self, field: str, server_value: Any, client_value: Any, source_role: str
    ) -> Dict[str, Any]:
        """
        Resolve a conflict based on policy rules.

        Args:
            field: Field name
            server_value: Current server value
            client_value: Client's proposed value
            source_role: Role of the client making the change

        Returns:
            Dict with resolution decision:
            {
                "action": "accept" | "reject" | "flag_conflict",
                "value": resolved_value,
                "reason": explanation
            }
        """
        if not self.policy:
            return {
                "action": "reject",
                "value": server_value,
                "reason": "No policy loaded",
            }

        # Check if role has authority
        if self.has_field_authority(source_role, field):
            return {
                "action": "accept",
                "value": client_value,
                "reason": f"{source_role} is authoritative for {field}",
            }

        # Check conflict rule
        rule = self.get_conflict_rule(field)

        if rule == "workshop_authoritative":
            if source_role == "workshop":
                return {
                    "action": "accept",
                    "value": client_value,
                    "reason": "Workshop is authoritative",
                }
            else:
                return {
                    "action": "flag_conflict",
                    "value": server_value,
                    "reason": "PLAN_CONFLICT: Only workshop can update this field",
                }

        elif rule == "dispatcher_authoritative":
            if source_role == "dispatcher":
                return {
                    "action": "accept",
                    "value": client_value,
                    "reason": "Dispatcher is authoritative",
                }
            else:
                return {
                    "action": "flag_conflict",
                    "value": server_value,
                    "reason": "PLAN_CONFLICT: Only dispatcher can update this field",
                }

        elif rule == "last_write_wins":
            return {
                "action": "accept",
                "value": client_value,
                "reason": "Last write wins",
            }

        else:
            return {
                "action": "flag_conflict",
                "value": server_value,
                "reason": f"Unknown resolution rule: {rule}",
            }


# Global policy loader instance
_policy_loader: Optional[PolicyLoader] = None


def get_policy_loader() -> PolicyLoader:
    """Get global policy loader instance."""
    global _policy_loader
    if _policy_loader is None:
        _policy_loader = PolicyLoader()
    return _policy_loader
