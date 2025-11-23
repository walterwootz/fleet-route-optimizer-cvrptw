"""
Policy management endpoints (SUPER_ADMIN only).
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any, Optional
from pathlib import Path
import json

from src.api.v1.endpoints.auth import get_current_user
from src.models.railfleet.user import User
from src.core.policy import PolicyLoader, PolicyVerificationError, get_policy_loader

router = APIRouter(prefix="/policy", tags=["Policy"])


class PolicyUploadRequest(BaseModel):
    """Policy upload request."""
    policy_name: str
    policy_data: Dict[str, Any]
    public_key_hex: Optional[str] = None


class PolicyResponse(BaseModel):
    """Policy response."""
    policy_name: str
    policy_data: Dict[str, Any]
    sha256_hash: str
    signature_verified: bool


class KeyPairResponse(BaseModel):
    """Ed25519 keypair response."""
    private_key_hex: str
    public_key_hex: str
    warning: str = "⚠️  Store private key securely! It cannot be recovered."


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require SUPER_ADMIN role."""
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SUPER_ADMIN can manage policies"
        )
    return current_user


@router.get("/list")
def list_policies(
    current_user: User = Depends(require_super_admin)
) -> Dict[str, Any]:
    """List all available policies."""
    loader = get_policy_loader()
    policy_dir = loader.policy_dir

    if not policy_dir.exists():
        return {"policies": []}

    policies = []
    for policy_file in policy_dir.glob("*.json"):
        policy_name = policy_file.stem
        sig_file = policy_dir / f"{policy_name}.json.sig"
        policies.append({
            "name": policy_name,
            "path": str(policy_file),
            "has_signature": sig_file.exists()
        })

    return {"policies": policies}


@router.get("/load/{policy_name}", response_model=PolicyResponse)
def load_policy(
    policy_name: str,
    public_key_hex: Optional[str] = None,
    current_user: User = Depends(require_super_admin)
) -> PolicyResponse:
    """
    Load and verify a policy.

    Args:
        policy_name: Name of policy (without .json)
        public_key_hex: Optional Ed25519 public key for signature verification
    """
    loader = get_policy_loader()

    try:
        policy_data = loader.load_policy(policy_name, public_key_hex)
        return PolicyResponse(
            policy_name=policy_name,
            policy_data=policy_data,
            sha256_hash=policy_data.get("_hash", ""),
            signature_verified=public_key_hex is not None
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PolicyVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Policy verification failed: {e}"
        )


@router.post("/upload", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
def upload_policy(
    request: PolicyUploadRequest,
    current_user: User = Depends(require_super_admin)
) -> PolicyResponse:
    """
    Upload a new policy (SHA-256 hash will be computed automatically).

    Args:
        request: Policy upload request with name and data
    """
    loader = get_policy_loader()
    policy_dir = loader.policy_dir
    policy_dir.mkdir(parents=True, exist_ok=True)

    policy_file = policy_dir / f"{request.policy_name}.json"

    # Compute SHA-256 hash
    sha256_hash = PolicyLoader.compute_sha256(request.policy_data)

    # Add hash to policy
    policy_with_hash = {**request.policy_data, "_hash": sha256_hash}

    # Write policy file
    with open(policy_file, 'w', encoding='utf-8') as f:
        json.dump(policy_with_hash, f, indent=2)

    return PolicyResponse(
        policy_name=request.policy_name,
        policy_data=policy_with_hash,
        sha256_hash=sha256_hash,
        signature_verified=False
    )


@router.post("/sign/{policy_name}")
def sign_policy(
    policy_name: str,
    private_key_hex: str,
    current_user: User = Depends(require_super_admin)
) -> Dict[str, str]:
    """
    Sign a policy file with Ed25519 private key.

    Args:
        policy_name: Name of policy to sign
        private_key_hex: Ed25519 private key in hex format (64 chars)
    """
    loader = get_policy_loader()
    policy_file = loader.policy_dir / f"{policy_name}.json"

    if not policy_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy not found: {policy_name}"
        )

    try:
        PolicyLoader.sign_policy(policy_file, private_key_hex)
        sig_file = Path(str(policy_file) + ".sig")

        with open(sig_file, 'r', encoding='utf-8') as f:
            signature = f.read().strip()

        return {
            "policy_name": policy_name,
            "signature_file": str(sig_file),
            "signature": signature,
            "message": "Policy signed successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signing failed: {e}"
        )


@router.post("/generate-keypair", response_model=KeyPairResponse)
def generate_keypair(
    current_user: User = Depends(require_super_admin)
) -> KeyPairResponse:
    """
    Generate a new Ed25519 keypair for policy signing.

    ⚠️  WARNING: Store the private key securely! It cannot be recovered.
    """
    private_key, public_key = PolicyLoader.generate_keypair()

    return KeyPairResponse(
        private_key_hex=private_key,
        public_key_hex=public_key
    )


@router.delete("/{policy_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(
    policy_name: str,
    current_user: User = Depends(require_super_admin)
):
    """Delete a policy and its signature file."""
    loader = get_policy_loader()
    policy_file = loader.policy_dir / f"{policy_name}.json"
    sig_file = loader.policy_dir / f"{policy_name}.json.sig"

    if not policy_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy not found: {policy_name}"
        )

    policy_file.unlink()
    if sig_file.exists():
        sig_file.unlink()
