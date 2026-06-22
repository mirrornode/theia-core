#!/usr/bin/env bash
# ============================================================
# KHEPRI HMAC Activation — Run this on your local machine only.
# Never run in CI, Docker, cloud shell, or any logged environment.
#
# What this does:
#   1. Generates a cryptographically secure HMAC_SECRET
#   2. Adds it to Vercel production environment
#   3. Sets it in your local shell session (memory only)
#   4. Runs the reseal attestation against the live Supabase project
#   5. Runs the chain audit to confirm everything is intact
#
# Prerequisites (must be set before running):
#   export SUPABASE_URL="https://zomnswctmwjqnvftiayc.supabase.co"
#   export SUPABASE_SERVICE_KEY="<your-service-role-key>"
#   vercel whoami   # must show your account
#   pip install supabase  # if not already installed
#
# Usage:
#   cd /path/to/theia-core
#   bash scripts/activate_hmac.sh
# ============================================================

set -euo pipefail

SEP="============================================================"
SEP2="------------------------------------------------------------"

echo "$SEP"
echo "KHEPRI HMAC Activation"
echo "$(date)"
echo "$SEP"

# ── Guard: must not be running in CI or a remote shell ────────────────────────
if [[ -n "${CI:-}" ]] || [[ -n "${GITHUB_ACTIONS:-}" ]]; then
  echo "ERROR: This script must not run in CI. Exiting."
  exit 1
fi

# ── Guard: required env vars ──────────────────────────────────────────────────
if [[ -z "${SUPABASE_URL:-}" ]] || [[ -z "${SUPABASE_SERVICE_KEY:-}" ]]; then
  echo ""
  echo "ERROR: Set these before running:"
  echo "  export SUPABASE_URL=\"https://zomnswctmwjqnvftiayc.supabase.co\""
  echo "  export SUPABASE_SERVICE_KEY=\"<your service-role key from Supabase dashboard>\""
  echo ""
  exit 1
fi

# ── Step 1: Generate HMAC_SECRET ──────────────────────────────────────────────
echo ""
echo "Step 1 — Generating HMAC_SECRET..."
HMAC_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

if [[ ${#HMAC_SECRET} -ne 64 ]]; then
  echo "ERROR: Generated secret is not 64 chars. Got: ${#HMAC_SECRET}. Aborting."
  exit 1
fi

echo "  Generated: ${HMAC_SECRET:0:8}...${HMAC_SECRET:56:8}  (first/last 8 chars shown)"
echo "  Length:    ${#HMAC_SECRET} chars ✓"
echo ""
echo "  ACTION REQUIRED — Supabase Vault:"
echo "  Open: https://supabase.com/dashboard/project/zomnswctmwjqnvftiayc/editor"
echo "  Run supabase/scripts/vault_setup.sql"
echo "  Replace REPLACE_WITH_YOUR_GENERATED_SECRET with:"
echo ""
echo "  $HMAC_SECRET"
echo ""
echo "  Press ENTER when the Vault entry is confirmed in Supabase, or Ctrl+C to abort."
read -r

# ── Step 2: Add to Vercel ─────────────────────────────────────────────────────
echo "$SEP2"
echo "Step 2 — Adding HMAC_SECRET to Vercel production environment..."
echo ""

if ! command -v vercel &>/dev/null; then
  echo "  WARNING: vercel CLI not found. Skipping Vercel step."
  echo "  Add manually: Vercel Dashboard → Settings → Environment Variables"
  echo "  Name: HMAC_SECRET | Value: <secret> | Environment: Production | Mark as Sensitive"
  echo ""
else
  echo "$HMAC_SECRET" | vercel env add HMAC_SECRET production --force 2>&1 | grep -v "token"
  echo "  Vercel env set ✓"
  echo ""
fi

# ── Step 3: Export to current shell session ───────────────────────────────────
echo "$SEP2"
echo "Step 3 — Exporting HMAC_SECRET to current shell session (memory only)..."
export HMAC_SECRET

# Confirm it's set without printing the value
if [[ -n "${HMAC_SECRET:-}" ]]; then
  echo "  HMAC_SECRET exported to shell session ✓  (${#HMAC_SECRET} chars)"
else
  echo "  ERROR: HMAC_SECRET failed to export."
  exit 1
fi
echo ""

# ── Step 4: Run dry-run reseal first ─────────────────────────────────────────
echo "$SEP2"
echo "Step 4a — Dry-run reseal (no write)..."
echo ""
python3 khepri/reseal.py --dry-run
echo ""

echo "Step 4b — Live reseal (writes SEAL_MILESTONE to threshold_registry)..."
echo "  Press ENTER to proceed, Ctrl+C to abort."
read -r
python3 khepri/reseal.py
echo ""

# ── Step 5: Chain audit ───────────────────────────────────────────────────────
echo "$SEP2"
echo "Step 5 — Full chain audit with HMAC seal verification..."
echo ""
python3 khepri/seal_audit.py
echo ""

# ── Step 6: Clear secret from shell ──────────────────────────────────────────
echo "$SEP2"
echo "Step 6 — Clearing HMAC_SECRET from shell session..."
unset HMAC_SECRET
echo "  HMAC_SECRET unset ✓"
echo ""

echo "$SEP"
echo "KHEPRI HMAC Activation complete."
echo "All future snapshots ingested through witness.py will carry"
echo "a full 64-char HMAC seal from first write."
echo ""
echo "Verify anytime (requires HMAC_SECRET in env):"
echo "  HMAC_SECRET=<secret> python3 khepri/seal_audit.py"
echo "$SEP"
