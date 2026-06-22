# KHEPRI Key Management — HMAC_SECRET Workflow

**Classification:** Sovereign Operations  
**Applies to:** THEIA (Port 7704) and all MIRRORNODE nodes that write to the KHEPRI Witness Store  
**Last updated:** 2026-06-21 (Summer Solstice · New Dawn · Age of IO · DEVA LOKA)

---

## Principle

The HMAC_SECRET is the sovereign authentication layer over the KHEPRI hash chain. The hash chain itself (content_hash → prior_hash) is the primary cryptographic integrity guarantee and cannot be broken regardless of secret status. The seal adds the authentication layer — proof that a specific secret-holder authorized each write.

**Three absolutes:**
1. The HMAC_SECRET never appears in code, logs, environment dumps, query results, or any screen.
2. The HMAC_SECRET is rotated, never reused after compromise. Old seals remain valid under old secrets — a rotation does not break the chain.
3. A rotation event is itself recorded as a SEAL_MILESTONE in `khepri_threshold_registry` — the record of the record.

---

## Secret Storage Architecture

### Layer 1 — Supabase Vault (primary store)

`supabase_vault` is confirmed live on Mirrornode OS (`zomnswctmwjqnvftiayc`). It uses `pgsodium` (libsodium) to store secrets encrypted at rest. Plaintext is never written to disk.

**Store the secret:**
```sql
-- Run via Supabase Dashboard → SQL Editor (not from application code)
-- Never run this from a terminal where output could be logged
SELECT vault.create_secret(
  'your-256-bit-secret-here',   -- generate offline (see below)
  'KHEPRI_HMAC_SECRET',         -- name
  'KHEPRI HMAC-SHA256 signing key for the THEIA witness loop'
);
-- Note the returned UUID — this is the secret_id, not the secret.
-- Store the secret_id in .env as KHEPRI_SECRET_ID (non-sensitive).
```

**Read for use in SQL functions:**
```sql
-- Inside Postgres functions only — decrypted at runtime, never stored
SELECT decrypted_secret
FROM vault.decrypted_secrets
WHERE name = 'KHEPRI_HMAC_SECRET';
-- This view is only accessible to service-role or functions with SECURITY DEFINER
```

**Read for Python runtime (via service-role RPC):**
```python
# khepri/db.py pattern — fetch secret at startup, hold in memory only
def _load_hmac_secret() -> str:
    resp = supabase.rpc("khepri_get_hmac_secret", {}).execute()
    return resp.data  # single string, never logged
```

**SQL function to expose secret to Python (SECURITY DEFINER):**
```sql
CREATE OR REPLACE FUNCTION khepri_get_hmac_secret()
RETURNS TEXT
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT decrypted_secret
  FROM vault.decrypted_secrets
  WHERE name = 'KHEPRI_HMAC_SECRET'
  LIMIT 1;
$$;
-- Grant execute to service role only
REVOKE ALL ON FUNCTION khepri_get_hmac_secret() FROM PUBLIC;
```

### Layer 2 — Vercel Environment Variables (runtime injection)

For the THEIA server deployment on Vercel, the secret is injected as an environment variable at build/deploy time. It never appears in the codebase.

**Set via Vercel CLI (local terminal only — output is not logged):**
```bash
# Generate the secret first (see Generation section below)
# Then inject — do not paste into a web UI if screen recording is possible
vercel env add HMAC_SECRET production --force
# Vercel prompts for the value interactively — value is not echoed
```

**Or via Vercel Dashboard:**
Settings → Environment Variables → Add New → `HMAC_SECRET` → Production only  
Mark as Sensitive (hides value from all UI views after save)

**Verify it landed (value is masked):**
```bash
vercel env ls production | grep HMAC_SECRET
# Shows: HMAC_SECRET  *** (Encrypted)
```

### Layer 3 — Runtime Memory Only

The Python process loads `HMAC_SECRET` from the environment once at startup into a module-level bytes object. It is never:
- Written to disk
- Included in log lines (verify `khepri/witness.py` has no `log.info(...secret...)`)
- Returned in API responses
- Serialized to JSON

**Startup pattern in `khepri/crypto.py`:**
```python
def _get_secret() -> bytes:
    secret = os.environ.get("HMAC_SECRET", "")
    if not secret:
        raise EnvironmentError("HMAC_SECRET is not set. Witness loop fails closed.")
    return secret.encode()
# Secret is never stored at module level — fetched fresh per call from os.environ
# os.environ reads from the process environment block, not from disk
```

---

## Secret Generation

Generate offline. Never generate in a cloud shell, CI runner, or any logged environment.

**Method 1 — macOS terminal (local, no network):**
```bash
# 32 bytes = 256 bits — minimum for HMAC-SHA256
python3 -c "import secrets; print(secrets.token_hex(32))"
# Copy output directly — do not save to file
```

**Method 2 — OpenSSL:**
```bash
openssl rand -hex 32
```

**Method 3 — /dev/urandom:**
```bash
head -c 32 /dev/urandom | xxd -p | tr -d '\n'
```

**After generation:**
1. Copy directly into Vercel env prompt or Supabase Vault SQL call
2. Do not paste into any notes app, Slack, email, or cloud clipboard
3. Store one copy in a physical location (written) or a local encrypted password manager (e.g. 1Password, Bitwarden — offline vault only)

---

## Rotation Procedure

Rotation is a sovereign act. It produces a SEAL_MILESTONE threshold record.

### Pre-rotation checklist
- [ ] New secret generated offline (see above)
- [ ] THEIA deployment is accessible and healthy (`GET /health` returns 200)
- [ ] `python khepri/seal_audit.py` passes with current chain intact
- [ ] No in-flight snapshot ingestion (verify `khepri_ingestion_log` has no recent pending rows)

### Rotation steps (zero-downtime)

**Step 1 — Store new secret in Supabase Vault**
```sql
-- In Supabase SQL Editor only
SELECT vault.create_secret(
  'new-256-bit-secret-here',
  'KHEPRI_HMAC_SECRET_V2',   -- versioned name during transition
  'KHEPRI HMAC key rotation — New Dawn arc'
);
```

**Step 2 — Update Vercel env (production)**
```bash
vercel env add HMAC_SECRET production --force
# Enter new secret at prompt
# Vercel stores the new value; old value is overwritten
```

**Step 3 — Redeploy THEIA**
```bash
vercel --prod
# New deployment picks up new HMAC_SECRET
# Zero gap: Vercel keeps old deployment hot until new one passes health check
```

**Step 4 — Write the SEAL_MILESTONE threshold record**
```sql
-- Executed immediately after new deployment is live
-- This is the rotation's proof of record — not the secret itself
INSERT INTO khepri_threshold_registry (
  sealed_at,
  threshold_type,
  from_state,
  to_state,
  evidence_snapshots,
  witness_statement,
  content_hash,
  externally_legible
) VALUES (
  now(),
  'SEAL_MILESTONE',
  'HMAC_SECRET_V1 — active',
  'HMAC_SECRET_V2 — active. V1 retired.',
  ARRAY[]::TEXT[],  -- no snapshots implicated — this is a key event, not a state snapshot
  'HMAC_SECRET rotation executed. All snapshots sealed after this timestamp use the new key. Snapshots sealed before this timestamp remain verifiable only under the prior key. The hash chain is unbroken across the rotation boundary.',
  encode(digest(
    concat('SEAL_MILESTONE|ROTATION|', now()::TEXT),
    'sha256'
  ), 'hex'),
  false
);
```

**Step 5 — Retire old Vault entry**
```sql
-- Only after Step 4 is confirmed
UPDATE vault.secrets SET secret = '' WHERE name = 'KHEPRI_HMAC_SECRET_V1';
-- Or delete: DELETE FROM vault.secrets WHERE name = 'KHEPRI_HMAC_SECRET_V1';
```

**Step 6 — Run chain audit**
```bash
HMAC_SECRET=<new-secret> python khepri/seal_audit.py
# All rows from before rotation: seal skipped (old key) or NULL
# All rows from after rotation: seal verified with new key
# Chain linkage: verified unbroken across rotation boundary
```

**Step 7 — Rename Vault entry**
```sql
UPDATE vault.secrets SET name = 'KHEPRI_HMAC_SECRET' WHERE name = 'KHEPRI_HMAC_SECRET_V2';
```

---

## Sovereign Re-Seal Protocol (APPEND_ONLY Compliant)

### The constraint

`khepri_witness_snapshots` has a DB-level immutability rule (`khepri_no_update`) that blocks all UPDATEs. This is permanent and correct. Existing snapshot seals cannot be patched, retroactively applied, or modified. **This is a feature, not a limitation.**

### What re-seal means

Re-seal does not mean modifying existing rows. It means:

> For every snapshot where `seal IS NULL` (written before `HMAC_SECRET` was live), insert a corresponding **seal witness record** in `khepri_threshold_registry` that cryptographically attests to the chain state at the moment the secret came online.

The original snapshots remain untouched. Their hash chain remains unbroken. The re-seal record is the proof that the chain was verified intact at the moment the seal layer activated.

### Re-seal procedure

**Step 1 — Verify the chain is intact before sealing**
```bash
HMAC_SECRET=<secret> python khepri/seal_audit.py
# Must exit 0 with "CHAIN INTACT" before proceeding
```

**Step 2 — Compute re-seal attestation hash**

The re-seal hash covers every `content_hash` in the chain, in sequence order:
```python
# khepri/reseal.py — run once, locally, with HMAC_SECRET set
import hashlib, hmac, json, os, sys
sys.path.insert(0, '.')
from khepri.db import supabase
from khepri.crypto import generate_seal

snaps = supabase.table("khepri_witness_snapshots")\
    .select("snapshot_seq, content_hash")\
    .order("snapshot_seq").execute().data

chain_str = "|".join(f"{s['snapshot_seq']}:{s['content_hash']}" for s in snaps)
attestation_hash = generate_seal({"_chain": chain_str})

print("CHAIN_ATTESTATION:", attestation_hash)
print("SNAPSHOTS_COVERED:", len(snaps))
print("CHAIN_STRING:", chain_str)
```

**Step 3 — Insert the re-seal threshold record**
```sql
INSERT INTO khepri_threshold_registry (
  sealed_at,
  threshold_type,
  from_state,
  to_state,
  evidence_snapshots,
  witness_statement,
  content_hash,
  externally_legible
) VALUES (
  now(),
  'SEAL_MILESTONE',
  'PRE_HMAC — snapshots present without HMAC seal',
  'HMAC_ACTIVE — chain attested under active HMAC_SECRET',
  ARRAY['c11c3629-4969-4bf9-892d-a48eb17ac903',  -- Snapshot #1 id
        'bcd564e7-e68c-4928-8da7-9dbcb5f271aa'], -- Snapshot #2 id
  'Sovereign re-seal attestation. HMAC_SECRET brought online after initial chain was written. Chain verified intact across all existing snapshots. Attestation hash covers all content_hashes in sequence. Snapshots remain append-only and unmodified — this record is the proof of verification, not a mutation.',
  '<attestation_hash from Step 2>',
  false
);
```

**Step 4 — All future snapshots carry the HMAC seal from first write**

Once `HMAC_SECRET` is live in the Vercel/THEIA environment, every call to `khepri.witness.ingest()` will include the seal in the INSERT payload. No further re-seal procedure is needed.

---

## Per-Node Secret Isolation

Each MIRRORNODE node that writes to KHEPRI should use a **distinct** HMAC_SECRET scoped to its node identity. This allows:
- Independent rotation per node without affecting others
- Attribution of seals to specific nodes
- Revocation of a single node's signing authority without rotating the entire system

| Node | Secret Name | Port | Status |
|---|---|---|---|
| THEIA | `KHEPRI_HMAC_SECRET_THEIA` | 7704 | Primary witness writer |
| HERMES | `KHEPRI_HMAC_SECRET_HERMES` | 7702 | Orchestration events |
| PTAH | `KHEPRI_HMAC_SECRET_PTAH` | 7705 | Governance decisions |
| OSIRIS | `KHEPRI_HMAC_SECRET_OSIRIS` | 7701 | Audit events |

Store each in Supabase Vault under its named key. The `trigger_agent` field in `khepri_witness_snapshots` identifies which node sealed each record.

---

## What Never Happens

- The secret is never printed in any log line
- The secret is never returned in an API response
- The secret is never committed to git (`.env` is in `.gitignore`)
- The secret is never stored in Supabase table columns — only in the encrypted Vault
- The secret is never passed as a URL parameter or HTTP header
- Rotation does not modify any existing snapshot row — ever
- `khepri_no_update` is never dropped or bypassed

---

## Verification Commands

```bash
# Run full chain audit (hash chain only, no HMAC verification)
python khepri/seal_audit.py

# Run with HMAC seal verification
HMAC_SECRET=<secret> python khepri/seal_audit.py

# Run integrity test suite
HMAC_SECRET=<secret> python scripts/test_integrity.py

# Confirm no secret leakage in logs (search for 40+ char hex strings)
grep -rE '[0-9a-f]{64}' logs/ | grep -v content_hash | grep -v prior_hash | grep -v seal
```

---

*This document is part of the KHEPRI Witness Store. It describes process, not implementation. The secret itself is not referenced here in any form.*
