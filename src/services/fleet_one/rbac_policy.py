"""
FLEET-ONE RBAC & Policy Engine

Role-Based Access Control and conflict resolution policies.

Roles:
- dispatcher: Plan creation, work order management, transfers
- workshop: Work order status updates, parts consumption
- procurement: Purchase requests, stock management
- finance: Invoice management, budget access
- ecm: ECM reports, document management
- viewer: Read-only access

Policy Rules:
- Register-based (dispatcher authority)
- Last-writer-wins (same role)
- Append-only (measurements, media)
- Authoritative sources (workshop actual times)
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass
import hashlib
import json


class Role(Enum):
    """User roles"""
    DISPATCHER = "dispatcher"
    WORKSHOP = "workshop"
    PROCUREMENT = "procurement"
    FINANCE = "finance"
    ECM = "ecm"
    VIEWER = "viewer"


class Scope(Enum):
    """Permission scopes"""
    # Planning
    PLAN_CREATE = "plan:create"
    PLAN_UPDATE = "plan:update"

    # Work Orders
    WO_CREATE = "wo:create"
    WO_UPDATE = "wo:update"
    WO_STATUS = "wo:status"
    WO_ACTUALS = "wo:actuals"

    # Transfers
    TRANSFER_PLAN = "transfer:plan"

    # Parts
    PARTS_CONSUME = "parts:consume"
    PARTS_STOCK = "parts:stock"

    # Purchasing
    PURCHASE_REQ = "purchase:req"

    # Suppliers
    SUPPLIER_READ = "supplier:read"

    # Invoices
    INVOICE_CREATE = "invoice:create"
    INVOICE_APPROVE = "invoice:approve"

    # Budget
    BUDGET_READ = "budget:read"

    # ECM
    ECM_READ = "ecm:read"
    ECM_REPORT = "ecm:report"

    # Documents
    DOCS_MANAGE = "docs:manage"

    # Media
    MEDIA_APPEND = "media:append"

    # Read all
    READ_ALL = "read:*"


class ConflictResolver(Enum):
    """Conflict resolution strategies"""
    REGISTER_POLICY = "register-policy"  # Dispatcher authority
    REGISTER_AUTHORITATIVE = "register-authoritative"  # Workshop actual times
    TS_LAST_WRITER_SAME_ROLE = "ts-last-writer(same-role)"  # Last writer wins (same role)
    APPEND_ONLY = "append-only"  # Append-only (no conflicts)
    APPEND_ONLY_GSET = "append-only(gset)"  # Append-only grow-set
    APPEND_ONLY_IS_PRIMARY = "append-only+is_primary"  # Append with primary flag


@dataclass
class PolicyRule:
    """Policy rule for field conflicts"""
    field_pattern: str
    authority: str  # Role or "system"
    resolver: ConflictResolver
    description: Optional[str] = None


@dataclass
class AccessResult:
    """Result of access check"""
    allowed: bool
    reason: Optional[str] = None
    required_scope: Optional[Scope] = None


class RBACEngine:
    """
    Role-Based Access Control engine.

    Manages permissions and validates access based on user role.
    """

    # Role → Scopes mapping (from policy)
    ROLE_SCOPES: Dict[Role, Set[Scope]] = {
        Role.DISPATCHER: {
            Scope.PLAN_CREATE,
            Scope.PLAN_UPDATE,
            Scope.WO_CREATE,
            Scope.WO_UPDATE,
            Scope.TRANSFER_PLAN
        },
        Role.WORKSHOP: {
            Scope.WO_STATUS,
            Scope.WO_ACTUALS,
            Scope.PARTS_CONSUME,
            Scope.MEDIA_APPEND
        },
        Role.PROCUREMENT: {
            Scope.PURCHASE_REQ,
            Scope.PARTS_STOCK,
            Scope.SUPPLIER_READ
        },
        Role.FINANCE: {
            Scope.INVOICE_CREATE,
            Scope.INVOICE_APPROVE,
            Scope.BUDGET_READ
        },
        Role.ECM: {
            Scope.ECM_READ,
            Scope.ECM_REPORT,
            Scope.DOCS_MANAGE
        },
        Role.VIEWER: {
            Scope.READ_ALL
        }
    }

    def __init__(self):
        pass

    def check_access(
        self,
        user_role: str,
        required_scope: str
    ) -> AccessResult:
        """
        Check if user role has required scope.

        Args:
            user_role: User's role (string)
            required_scope: Required scope (string)

        Returns:
            AccessResult indicating if access is allowed
        """
        try:
            role = Role(user_role)
            scope = Scope(required_scope)
        except ValueError as e:
            return AccessResult(
                allowed=False,
                reason=f"Invalid role or scope: {e}"
            )

        # Check if role has scope
        if scope in self.ROLE_SCOPES.get(role, set()):
            return AccessResult(allowed=True)

        # Check for READ_ALL (viewer)
        if Scope.READ_ALL in self.ROLE_SCOPES.get(role, set()):
            # Viewers can read, but not write
            if any(write_verb in required_scope for write_verb in ["create", "update", "approve", "manage"]):
                return AccessResult(
                    allowed=False,
                    reason="Viewer role cannot perform write operations",
                    required_scope=scope
                )
            return AccessResult(allowed=True)

        return AccessResult(
            allowed=False,
            reason=f"Role {role.value} does not have scope {scope.value}",
            required_scope=scope
        )

    def get_user_scopes(self, user_role: str) -> Set[str]:
        """Get all scopes for a user role"""
        try:
            role = Role(user_role)
            return {scope.value for scope in self.ROLE_SCOPES.get(role, set())}
        except ValueError:
            return set()


class PolicyEngine:
    """
    Conflict resolution policy engine.

    Resolves conflicts between concurrent updates based on field authority
    and resolution strategy.
    """

    def __init__(self, policy_rules: List[Dict[str, Any]]):
        """
        Initialize policy engine with rules.

        Args:
            policy_rules: List of policy rules from config
        """
        self.rules = self._parse_rules(policy_rules)

    def _parse_rules(self, rules_config: List[Dict[str, Any]]) -> List[PolicyRule]:
        """Parse policy rules from config"""
        rules = []
        for rule_config in rules_config:
            rule = PolicyRule(
                field_pattern=rule_config["field"],
                authority=rule_config["authority"],
                resolver=ConflictResolver(rule_config["resolver"]),
                description=rule_config.get("description")
            )
            rules.append(rule)
        return rules

    def get_authority(self, field: str) -> Optional[str]:
        """Get authority role for field"""
        for rule in self.rules:
            # Simple pattern matching (could be enhanced with regex)
            if self._field_matches_pattern(field, rule.field_pattern):
                return rule.authority
        return None

    def get_resolver(self, field: str) -> Optional[ConflictResolver]:
        """Get conflict resolver for field"""
        for rule in self.rules:
            if self._field_matches_pattern(field, rule.field_pattern):
                return rule.resolver
        return None

    def _field_matches_pattern(self, field: str, pattern: str) -> bool:
        """Check if field matches pattern"""
        # Support wildcards: "measurement.*" matches "measurement.speed"
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return field.startswith(prefix)
        return field == pattern

    def resolve_conflict(
        self,
        field: str,
        local_value: Any,
        remote_value: Any,
        local_role: str,
        remote_role: str,
        local_ts: datetime,
        remote_ts: datetime
    ) -> Dict[str, Any]:
        """
        Resolve conflict between local and remote values.

        Args:
            field: Field name
            local_value: Local value
            remote_value: Remote value
            local_role: Local user role
            remote_role: Remote user role
            local_ts: Local timestamp
            remote_ts: Remote timestamp

        Returns:
            Resolution result with winning value and reason
        """
        authority = self.get_authority(field)
        resolver = self.get_resolver(field)

        if not authority or not resolver:
            # No policy - default to last writer wins
            if local_ts > remote_ts:
                return {
                    "winner": "local",
                    "value": local_value,
                    "reason": "No policy found, default to last writer wins (local)"
                }
            else:
                return {
                    "winner": "remote",
                    "value": remote_value,
                    "reason": "No policy found, default to last writer wins (remote)"
                }

        # Apply resolver strategy
        if resolver == ConflictResolver.REGISTER_POLICY:
            # Authority role wins
            if local_role == authority:
                return {
                    "winner": "local",
                    "value": local_value,
                    "reason": f"Register policy: {authority} has authority"
                }
            elif remote_role == authority:
                return {
                    "winner": "remote",
                    "value": remote_value,
                    "reason": f"Register policy: {authority} has authority"
                }
            else:
                # Neither has authority - last writer wins
                return {
                    "winner": "local" if local_ts > remote_ts else "remote",
                    "value": local_value if local_ts > remote_ts else remote_value,
                    "reason": "Neither has authority, last writer wins"
                }

        elif resolver == ConflictResolver.REGISTER_AUTHORITATIVE:
            # Workshop actual times are authoritative
            if local_role == authority:
                return {
                    "winner": "local",
                    "value": local_value,
                    "reason": f"Authoritative source: {authority}"
                }
            elif remote_role == authority:
                return {
                    "winner": "remote",
                    "value": remote_value,
                    "reason": f"Authoritative source: {authority}"
                }
            else:
                return {
                    "winner": "none",
                    "value": None,
                    "reason": "No authoritative source available"
                }

        elif resolver == ConflictResolver.TS_LAST_WRITER_SAME_ROLE:
            # Last writer wins if same role
            if local_role == remote_role:
                return {
                    "winner": "local" if local_ts > remote_ts else "remote",
                    "value": local_value if local_ts > remote_ts else remote_value,
                    "reason": "Same role, last writer wins"
                }
            else:
                return {
                    "winner": "conflict",
                    "value": None,
                    "reason": "Different roles, manual resolution required"
                }

        elif resolver in [ConflictResolver.APPEND_ONLY, ConflictResolver.APPEND_ONLY_GSET]:
            # Append-only - merge both values
            merged = self._merge_append_only(local_value, remote_value)
            return {
                "winner": "merged",
                "value": merged,
                "reason": "Append-only field, values merged"
            }

        else:
            # Unknown resolver
            return {
                "winner": "error",
                "value": None,
                "reason": f"Unknown resolver: {resolver}"
            }

    def _merge_append_only(self, local: Any, remote: Any) -> Any:
        """Merge append-only values"""
        # If both are lists, merge
        if isinstance(local, list) and isinstance(remote, list):
            # Use set to deduplicate, then back to list
            # (assumes items are hashable)
            try:
                merged = list(set(local + remote))
                return merged
            except TypeError:
                # Items not hashable - just concatenate
                return local + remote

        # If both are dicts, merge keys
        if isinstance(local, dict) and isinstance(remote, dict):
            merged = {**local, **remote}
            return merged

        # Otherwise, return both as list
        return [local, remote]


class PolicySigner:
    """
    Policy signing and verification.

    Uses Ed25519 for cryptographic signing of policy decisions.
    """

    def __init__(self, public_key: Optional[str] = None):
        """
        Initialize signer.

        Args:
            public_key: Ed25519 public key (hex string)
        """
        self.public_key = public_key

    def sign_decision(
        self,
        decision: Dict[str, Any],
        private_key: str
    ) -> str:
        """
        Sign a policy decision.

        Args:
            decision: Decision data to sign
            private_key: Ed25519 private key (hex)

        Returns:
            Signature (hex string)

        Note: Actual Ed25519 signing requires nacl or cryptography library
        For now, using SHA-256 as placeholder
        """
        # Serialize decision to JSON
        decision_json = json.dumps(decision, sort_keys=True)

        # Hash with SHA-256 (placeholder for Ed25519)
        hash_obj = hashlib.sha256(decision_json.encode())
        signature = hash_obj.hexdigest()

        return signature

    def verify_signature(
        self,
        decision: Dict[str, Any],
        signature: str
    ) -> bool:
        """
        Verify policy decision signature.

        Args:
            decision: Decision data
            signature: Signature to verify

        Returns:
            True if signature is valid
        """
        # Recreate signature
        expected_signature = self.sign_decision(decision, "")

        return signature == expected_signature


# Singleton instances
_rbac_engine: Optional[RBACEngine] = None
_policy_engine: Optional[PolicyEngine] = None


def get_rbac_engine() -> RBACEngine:
    """Get global RBAC engine instance"""
    global _rbac_engine
    if _rbac_engine is None:
        _rbac_engine = RBACEngine()
    return _rbac_engine


def init_policy_engine(policy_rules: List[Dict[str, Any]]) -> PolicyEngine:
    """Initialize global policy engine"""
    global _policy_engine
    _policy_engine = PolicyEngine(policy_rules)
    return _policy_engine


def get_policy_engine() -> Optional[PolicyEngine]:
    """Get global policy engine instance"""
    return _policy_engine
