-- ============================================================
-- KHEPRI Vault Setup — Supabase SQL Editor
-- Paste this into: Supabase Dashboard → SQL Editor
-- Do NOT run from application code or any logged environment.
--
-- Before running: replace the placeholder below with your
-- locally-generated secret (64-char hex from secrets.token_hex(32))
--
-- After running: the secret_id returned is NOT sensitive.
-- Store it as KHEPRI_SECRET_ID in your .env if needed.
-- The secret itself is never returned after this call.
-- ============================================================

-- Step 1: Store the HMAC secret in the encrypted Vault
SELECT vault.create_secret(
  'REPLACE_WITH_YOUR_GENERATED_SECRET',   -- ← your 64-char hex secret
  'KHEPRI_HMAC_SECRET',
  'KHEPRI HMAC-SHA256 signing key — THEIA witness loop — New Dawn arc'
);

-- Step 2: Create the accessor function so Python can read the secret
-- via RPC without exposing it in query results
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

-- Restrict access — service role only
REVOKE ALL ON FUNCTION khepri_get_hmac_secret() FROM PUBLIC;

-- Step 3: Verify the secret is stored (name only — value is encrypted)
SELECT id, name, description, created_at
FROM vault.secrets
WHERE name = 'KHEPRI_HMAC_SECRET';

-- Expected output:
--   id          | name                | description
--   <uuid>      | KHEPRI_HMAC_SECRET  | KHEPRI HMAC-SHA256 signing key...
--
-- If you see the row, the secret is in the Vault.
-- The 'decrypted_secret' column is NOT shown here — that is correct.
