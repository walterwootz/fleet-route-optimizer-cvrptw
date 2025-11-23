"""
Policy management with SHA-256 hash verification and Ed25519 signatures.

Policies are JSON files that define conflict resolution rules, scheduler constraints,
and other configurable behavior. They must be verified for integrity and authenticity.
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
import nacl.signing
import nacl.encoding


class PolicyVerificationError(Exception):
    """Raised when policy verification fails."""
    pass


class PolicyLoader:
    """
    Load and verify policy JSON files with SHA-256 hashes and Ed25519 signatures.

    Verification workflow:
    1. Load policy JSON file
    2. Verify SHA-256 hash (REQUIRED)
    3. Verify Ed25519 signature (OPTIONAL but recommended)
    """

    def __init__(self, policy_dir: Path, verify_signatures: bool = True):
        """
        Initialize policy loader.

        Args:
            policy_dir: Directory containing policy JSON files
            verify_signatures: Whether to enforce Ed25519 signature verification
        """
        self.policy_dir = Path(policy_dir)
        self.verify_signatures = verify_signatures
        self._policies: Dict[str, Dict[str, Any]] = {}

    def load_policy(self, policy_name: str, public_key_hex: Optional[str] = None) -> Dict[str, Any]:
        """
        Load and verify a policy file.

        Args:
            policy_name: Name of policy file (without .json extension)
            public_key_hex: Ed25519 public key in hex format (64 chars)

        Returns:
            dict: Verified policy data

        Raises:
            PolicyVerificationError: If verification fails
            FileNotFoundError: If policy file not found
        """
        policy_file = self.policy_dir / f"{policy_name}.json"
        sig_file = self.policy_dir / f"{policy_name}.json.sig"

        if not policy_file.exists():
            raise FileNotFoundError(f"Policy file not found: {policy_file}")

        # Read policy JSON
        with open(policy_file, 'r', encoding='utf-8') as f:
            policy_data = json.load(f)

        # Verify SHA-256 hash (REQUIRED)
        self._verify_sha256(policy_data, policy_file)

        # Verify Ed25519 signature (OPTIONAL)
        if self.verify_signatures and sig_file.exists():
            if not public_key_hex:
                raise PolicyVerificationError(
                    f"Signature file exists but no public key provided for {policy_name}"
                )
            self._verify_ed25519(policy_file, sig_file, public_key_hex)
        elif self.verify_signatures and not sig_file.exists():
            raise PolicyVerificationError(
                f"Signature verification required but .sig file not found: {sig_file}"
            )

        # Cache policy
        self._policies[policy_name] = policy_data
        return policy_data

    def _verify_sha256(self, policy_data: Dict[str, Any], policy_file: Path):
        """
        Verify SHA-256 hash embedded in policy JSON.

        Expected format in policy JSON:
        {
            "_hash": "sha256_hex_string",
            ... other policy fields ...
        }

        Args:
            policy_data: Parsed policy JSON
            policy_file: Path to policy file for error messages

        Raises:
            PolicyVerificationError: If hash missing or invalid
        """
        if "_hash" not in policy_data:
            raise PolicyVerificationError(
                f"Policy missing '_hash' field: {policy_file}"
            )

        expected_hash = policy_data["_hash"]

        # Compute canonical JSON (sorted keys, no whitespace)
        # Remove _hash field before computing
        policy_without_hash = {k: v for k, v in policy_data.items() if k != "_hash"}
        canonical_json = json.dumps(policy_without_hash, sort_keys=True, separators=(',', ':'))

        computed_hash = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

        if computed_hash != expected_hash:
            raise PolicyVerificationError(
                f"SHA-256 hash mismatch for {policy_file}:\n"
                f"  Expected: {expected_hash}\n"
                f"  Computed: {computed_hash}"
            )

    def _verify_ed25519(self, policy_file: Path, sig_file: Path, public_key_hex: str):
        """
        Verify Ed25519 signature using PyNaCl.

        Args:
            policy_file: Path to policy JSON file
            sig_file: Path to signature file (.sig)
            public_key_hex: Ed25519 public key in hex format

        Raises:
            PolicyVerificationError: If signature invalid
        """
        # Read policy file bytes
        with open(policy_file, 'rb') as f:
            policy_bytes = f.read()

        # Read signature
        with open(sig_file, 'r', encoding='utf-8') as f:
            signature_hex = f.read().strip()

        try:
            # Decode public key
            public_key_bytes = bytes.fromhex(public_key_hex)
            verify_key = nacl.signing.VerifyKey(public_key_bytes)

            # Decode signature
            signature_bytes = bytes.fromhex(signature_hex)

            # Verify signature
            verify_key.verify(policy_bytes, signature_bytes)

        except nacl.exceptions.BadSignatureError:
            raise PolicyVerificationError(
                f"Ed25519 signature verification failed for {policy_file}"
            )
        except ValueError as e:
            raise PolicyVerificationError(
                f"Invalid hex encoding for key or signature: {e}"
            )

    def get_policy(self, policy_name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached policy.

        Args:
            policy_name: Name of policy

        Returns:
            dict: Policy data if loaded, None otherwise
        """
        return self._policies.get(policy_name)

    @staticmethod
    def generate_keypair() -> tuple[str, str]:
        """
        Generate Ed25519 keypair for policy signing.

        Returns:
            tuple: (private_key_hex, public_key_hex)

        Example:
            >>> private_key, public_key = PolicyLoader.generate_keypair()
            >>> print(f"Private: {private_key}")
            >>> print(f"Public: {public_key}")
        """
        signing_key = nacl.signing.SigningKey.generate()
        private_key_hex = signing_key.encode(encoder=nacl.encoding.HexEncoder).decode('ascii')
        public_key_hex = signing_key.verify_key.encode(encoder=nacl.encoding.HexEncoder).decode('ascii')
        return private_key_hex, public_key_hex

    @staticmethod
    def sign_policy(policy_file: Path, private_key_hex: str, output_sig: Optional[Path] = None):
        """
        Sign a policy file with Ed25519 private key.

        Args:
            policy_file: Path to policy JSON file
            private_key_hex: Ed25519 private key in hex format
            output_sig: Output signature file path (default: policy_file.sig)

        Example:
            >>> from pathlib import Path
            >>> private_key, public_key = PolicyLoader.generate_keypair()
            >>> PolicyLoader.sign_policy(
            ...     Path("policy/scheduler.json"),
            ...     private_key
            ... )
        """
        if output_sig is None:
            output_sig = Path(str(policy_file) + ".sig")

        # Read policy file
        with open(policy_file, 'rb') as f:
            policy_bytes = f.read()

        # Decode private key
        private_key_bytes = bytes.fromhex(private_key_hex)
        signing_key = nacl.signing.SigningKey(private_key_bytes)

        # Sign
        signed = signing_key.sign(policy_bytes)
        signature_hex = signed.signature.hex()

        # Write signature
        with open(output_sig, 'w', encoding='utf-8') as f:
            f.write(signature_hex)

        print(f"✓ Signature written to: {output_sig}")

    @staticmethod
    def compute_sha256(policy_data: Dict[str, Any]) -> str:
        """
        Compute SHA-256 hash of policy data (canonical JSON).

        Args:
            policy_data: Policy dictionary (without _hash field)

        Returns:
            str: SHA-256 hash in hex format

        Example:
            >>> policy = {"rules": [{"type": "conflict", "resolution": "remote_wins"}]}
            >>> hash_value = PolicyLoader.compute_sha256(policy)
            >>> policy["_hash"] = hash_value
        """
        # Remove _hash if present
        policy_without_hash = {k: v for k, v in policy_data.items() if k != "_hash"}

        # Canonical JSON
        canonical_json = json.dumps(policy_without_hash, sort_keys=True, separators=(',', ':'))

        # Compute hash
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()


# Default policy loader instance
_default_loader: Optional[PolicyLoader] = None


def get_policy_loader() -> PolicyLoader:
    """
    Get default policy loader instance.

    Returns:
        PolicyLoader: Default policy loader
    """
    global _default_loader
    if _default_loader is None:
        policy_dir = Path(__file__).parent.parent.parent / "policy"
        _default_loader = PolicyLoader(policy_dir, verify_signatures=False)  # Optional by default
    return _default_loader


__all__ = [
    'PolicyLoader',
    'PolicyVerificationError',
    'get_policy_loader',
]
