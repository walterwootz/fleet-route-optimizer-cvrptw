# Policy Signing with Ed25519

**Version:** 1.0
**Date:** 2025-11-23
**Status:** Active

---

## Overview

RailFleet Manager policies are JSON configuration files that define conflict resolution rules, scheduler constraints, and other behavior. To ensure integrity and authenticity, policies must be verified using:

1. **SHA-256 Hash** (REQUIRED) - Detects tampering
2. **Ed25519 Signature** (OPTIONAL) - Verifies authorship

---

## Policy Structure

### Basic Policy JSON
```json
{
  "_hash": "sha256_hex_string_computed_automatically",
  "version": "1.0",
  "rules": [
    {
      "type": "conflict",
      "field": "status",
      "resolution": "remote_wins"
    }
  ]
}
```

### Policy with Signature
```
policy/
├── scheduler_conflict_policy.json       # Policy with _hash field
└── scheduler_conflict_policy.json.sig   # Ed25519 signature (hex)
```

---

## Workflow

### 1. Generate Ed25519 Keypair (One-time)

```bash
# Via API (SUPER_ADMIN only)
curl -X POST http://localhost:8000/api/v1/policy/generate-keypair \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "private_key_hex": "64_character_hex_string...",
  "public_key_hex": "64_character_hex_string...",
  "warning": "⚠️  Store private key securely! It cannot be recovered."
}
```

**⚠️  CRITICAL:** Store the private key in a secure location (e.g., vault, HSM).
Never commit it to git!

### 2. Create Policy JSON

```python
# Example: Scheduler conflict policy
policy = {
    "version": "1.0",
    "name": "scheduler_conflict_policy",
    "rules": [
        {
            "type": "conflict",
            "entity": "work_order",
            "field": "scheduled_start_ts",
            "resolution": "dispatcher_wins",
            "priority": 1
        },
        {
            "type": "conflict",
            "entity": "work_order",
            "field": "actual_start_ts",
            "resolution": "workshop_wins",
            "priority": 2
        }
    ]
}
```

### 3. Upload Policy (Auto-computes SHA-256)

```bash
curl -X POST http://localhost:8000/api/v1/policy/upload \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_name": "scheduler_conflict",
    "policy_data": {
      "version": "1.0",
      "rules": [...]
    }
  }'
```

Response:
```json
{
  "policy_name": "scheduler_conflict",
  "policy_data": {
    "_hash": "computed_sha256_hash...",
    "version": "1.0",
    "rules": [...]
  },
  "sha256_hash": "computed_sha256_hash...",
  "signature_verified": false
}
```

### 4. Sign Policy (Optional but Recommended)

```bash
curl -X POST http://localhost:8000/api/v1/policy/sign/scheduler_conflict \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "private_key_hex": "your_private_key_here"
  }'
```

Response:
```json
{
  "policy_name": "scheduler_conflict",
  "signature_file": "policy/scheduler_conflict.json.sig",
  "signature": "hex_encoded_ed25519_signature...",
  "message": "Policy signed successfully"
}
```

### 5. Load and Verify Policy

```bash
# Without signature verification
curl -X GET http://localhost:8000/api/v1/policy/load/scheduler_conflict \
  -H "Authorization: Bearer $TOKEN"

# With signature verification
curl -X GET "http://localhost:8000/api/v1/policy/load/scheduler_conflict?public_key_hex=$PUBLIC_KEY" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Python Usage

### Load Policy in Application Code

```python
from src.core.policy import get_policy_loader, PolicyVerificationError

# Get default policy loader
loader = get_policy_loader()

try:
    # Load policy (SHA-256 verified automatically)
    policy = loader.load_policy("scheduler_conflict")

    # Access policy rules
    for rule in policy["rules"]:
        print(f"Rule: {rule['type']} - {rule['resolution']}")

except PolicyVerificationError as e:
    print(f"Policy verification failed: {e}")
```

### Load Policy with Signature Verification

```python
from src.core.policy import PolicyLoader
from pathlib import Path

# Create loader with signature enforcement
loader = PolicyLoader(
    policy_dir=Path("policy"),
    verify_signatures=True  # Require .sig files
)

# Load with public key
public_key = "64_char_hex_public_key..."
policy = loader.load_policy("scheduler_conflict", public_key_hex=public_key)
```

### Sign Policy from Python

```python
from src.core.policy import PolicyLoader
from pathlib import Path

# Load private key (from secure storage)
private_key = "64_char_hex_private_key..."

# Sign policy file
PolicyLoader.sign_policy(
    policy_file=Path("policy/scheduler_conflict.json"),
    private_key_hex=private_key
)
# Creates: policy/scheduler_conflict.json.sig
```

### Generate Keypair from Python

```python
from src.core.policy import PolicyLoader

private_key, public_key = PolicyLoader.generate_keypair()
print(f"Private Key: {private_key}")  # Store securely!
print(f"Public Key: {public_key}")     # Distribute to validators
```

---

## Security Best Practices

### Key Management
1. **Generate keys once** - Use `POST /policy/generate-keypair`
2. **Store private key securely**:
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - Hardware Security Module (HSM)
3. **Never commit private keys to git**
4. **Distribute public key** - Can be safely embedded in code or config

### Policy Updates
1. **Versioning** - Include `version` field in policy JSON
2. **Audit trail** - Log all policy uploads/changes
3. **Testing** - Verify policy in staging before production
4. **Rollback plan** - Keep previous policy versions

### Signature Verification
- **Development**: Optional (verify_signatures=False)
- **Staging**: Recommended (verify_signatures=True)
- **Production**: REQUIRED (verify_signatures=True)

---

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/policy/list` | List all policies | SUPER_ADMIN |
| GET | `/api/v1/policy/load/{name}` | Load and verify policy | SUPER_ADMIN |
| POST | `/api/v1/policy/upload` | Upload new policy | SUPER_ADMIN |
| POST | `/api/v1/policy/sign/{name}` | Sign policy with Ed25519 | SUPER_ADMIN |
| POST | `/api/v1/policy/generate-keypair` | Generate Ed25519 keypair | SUPER_ADMIN |
| DELETE | `/api/v1/policy/{name}` | Delete policy and signature | SUPER_ADMIN |

---

## Troubleshooting

### SHA-256 Hash Mismatch
```
Error: SHA-256 hash mismatch
```
**Solution:** Policy file was modified. Re-upload via API to recompute hash.

### Signature Verification Failed
```
Error: Ed25519 signature verification failed
```
**Solutions:**
1. Verify correct public key used
2. Check policy file wasn't modified after signing
3. Re-sign policy with correct private key

### Missing Signature File
```
Error: Signature verification required but .sig file not found
```
**Solution:** Sign policy using `POST /policy/sign/{name}` or disable signature verification.

---

## Examples

### Complete Workflow Example

```bash
# 1. Generate keypair (one-time)
KEYS=$(curl -X POST http://localhost:8000/api/v1/policy/generate-keypair \
  -H "Authorization: Bearer $TOKEN")
PRIVATE_KEY=$(echo $KEYS | jq -r '.private_key_hex')
PUBLIC_KEY=$(echo $KEYS | jq -r '.public_key_hex')

# 2. Upload policy
curl -X POST http://localhost:8000/api/v1/policy/upload \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @policy_data.json

# 3. Sign policy
curl -X POST http://localhost:8000/api/v1/policy/sign/scheduler_conflict \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"private_key_hex\": \"$PRIVATE_KEY\"}"

# 4. Verify policy
curl -X GET "http://localhost:8000/api/v1/policy/load/scheduler_conflict?public_key_hex=$PUBLIC_KEY" \
  -H "Authorization: Bearer $TOKEN"
```

---

## References

- **Ed25519**: [RFC 8032](https://tools.ietf.org/html/rfc8032)
- **PyNaCl**: [Documentation](https://pynacl.readthedocs.io/)
- **SHA-256**: [NIST FIPS 180-4](https://csrc.nist.gov/publications/detail/fips/180/4/final)

---

## Compliance Status

✅ **Phase 2 compliant**
SHA-256 hash verification required, Ed25519 signatures optional per GAP_ANALYSIS.md WP7.

**Last Updated:** 2025-11-23
