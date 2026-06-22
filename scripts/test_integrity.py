"""
scripts/test_integrity.py — KHEPRI Witness Store integrity test suite.

Gates (all three must pass before Snapshot #2 is authorized):
  1. Deterministic seal — same payload always produces the same HMAC seal.
  2. Tamper detection  — mutating previous_hash invalidates the seal.
  3. Fail closed       — missing HMAC_SECRET raises EnvironmentError,
                         never produces a seal silently.

Run:
    HMAC_SECRET=<secret> python scripts/test_integrity.py

Exit 0 on full pass. Exit 1 on any failure.
"""

import os
import sys

# Allow running from repo root without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from khepri.crypto import generate_seal, verify_seal

SEPARATOR = "-" * 60


def run_suite() -> bool:
    os.environ["HMAC_SECRET"] = "test-secret-123"

    # The canonical Snapshot #2 payload shape
    payload = {
        "arc_id": "dd94471c-e243-4cdd-9676-1669d70f41d2",
        "snapshot_index": 2,
        "previous_hash": "b033ec1f5ef0e563938a83ccf3a86aa2c72600a5c6c014cf25a0d75c9de2ac15",
        "content_hash": "abc123def456",           # placeholder — real hash computed at ingest
        "threshold_flag": True,
        "marker_type": "KHEPRI_SYNC",
        "transition_from": "KHEPRI_ONLINE",
        "transition_to": "KHEPRI_ONLINE",
        "created_at": "2026-06-21T22:15:00Z",
    }

    all_passed = True

    print(SEPARATOR)
    print("KHEPRI Integrity Suite — PRE_TRIGGER_VERIFICATION")
    print(SEPARATOR)

    # ── Gate 1: Deterministic Seal ──────────────────────────────────────────
    try:
        seal_1 = generate_seal(payload)
        seal_2 = generate_seal(payload)
        assert seal_1 == seal_2, "Non-deterministic: two calls produced different seals."
        assert verify_seal(payload, seal_1) is True, "verify_seal returned False on valid seal."
        assert len(seal_1) == 64, f"Seal length {len(seal_1)} != 64."
        print(f"[PASS] Gate 1 — Deterministic seal verified. ({seal_1[:16]}...)")
    except Exception as exc:
        print(f"[FAIL] Gate 1 — {exc}")
        all_passed = False

    # ── Gate 2: Tamper Detection ────────────────────────────────────────────
    try:
        seal_original = generate_seal(payload)

        tampered = payload.copy()
        tampered["previous_hash"] = "0000000000000000000000000000000000000000000000000000000000000000"
        result = verify_seal(tampered, seal_original)
        assert result is False, "Tampered previous_hash was NOT detected — chain integrity broken."
        print("[PASS] Gate 2 — previous_hash tamper detected correctly.")

        tampered2 = payload.copy()
        tampered2["threshold_flag"] = False
        result2 = verify_seal(tampered2, seal_original)
        assert result2 is False, "Tampered threshold_flag was NOT detected."
        print("[PASS] Gate 2 — threshold_flag tamper detected correctly.")

        tampered3 = payload.copy()
        tampered3["arc_id"] = "00000000-0000-0000-0000-000000000000"
        result3 = verify_seal(tampered3, seal_original)
        assert result3 is False, "Tampered arc_id was NOT detected."
        print("[PASS] Gate 2 — arc_id tamper detected correctly.")

    except Exception as exc:
        print(f"[FAIL] Gate 2 — {exc}")
        all_passed = False

    # ── Gate 3: Fail Closed (Missing Secret) ────────────────────────────────
    try:
        saved = os.environ.pop("HMAC_SECRET", None)
        raised = False
        try:
            generate_seal(payload)
        except EnvironmentError as env_err:
            raised = True
            print(f"[PASS] Gate 3 — Missing HMAC_SECRET fails closed: {env_err}")
        if not raised:
            print("[FAIL] Gate 3 — generate_seal did NOT raise EnvironmentError without HMAC_SECRET.")
            all_passed = False
        # Restore for any subsequent use
        if saved:
            os.environ["HMAC_SECRET"] = saved
    except Exception as exc:
        print(f"[FAIL] Gate 3 — Unexpected error: {exc}")
        all_passed = False

    print(SEPARATOR)
    if all_passed:
        print("STATUS: Integrity Suite Passed. KHEPRI cleared for Snapshot #2.")
    else:
        print("STATUS: SUITE FAILED — holding at PRE_TRIGGER_VERIFICATION.")
    print(SEPARATOR)

    return all_passed


if __name__ == "__main__":
    passed = run_suite()
    sys.exit(0 if passed else 1)
