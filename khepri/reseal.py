"""
khepri/reseal.py — Sovereign re-seal attestation tool.

APPEND_ONLY compliant. This tool does NOT modify any existing snapshot row.
It computes a chain attestation hash over all existing content_hashes
in sequence order, then inserts a SEAL_MILESTONE record into
khepri_threshold_registry as proof that the chain was verified intact
at the moment HMAC_SECRET came online.

This is the correct procedure for snapshots written before HMAC_SECRET
was live in the environment. The snapshots themselves are immutable and
correct — this record attests to them, it does not alter them.

Usage:
    HMAC_SECRET=<secret> python khepri/reseal.py [--dry-run]

Flags:
    --dry-run    Compute and print the attestation hash without writing
                 to the threshold registry. Safe to run any number of times.
    --arc-name   Restrict to a specific arc (default: all open arcs)
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from khepri.crypto import generate_seal, verify_seal
from khepri.db import supabase

SEP = "=" * 70


def compute_attestation(snapshots: list) -> str:
    """
    Compute a chain attestation seal over all content_hashes in seq order.
    The canonical form is: "seq:hash|seq:hash|..." — unambiguous, ordered.
    """
    chain_str = "|".join(
        f"{s['snapshot_seq']}:{s['content_hash']}" for s in snapshots
    )
    return generate_seal({"_chain": chain_str}), chain_str


def run(dry_run: bool = False, arc_name: str = None):
    print(SEP)
    print("KHEPRI Sovereign Re-Seal Attestation")
    print(f"Mode: {'DRY RUN — no write' if dry_run else 'LIVE — will write to threshold_registry'}")
    print(SEP)

    # ── Fetch snapshots ───────────────────────────────────────────────────────
    q = supabase.table("khepri_witness_snapshots")\
        .select("id, snapshot_seq, content_hash, prior_hash, arc_id, seal, immutable_seal")\
        .order("snapshot_seq")

    if arc_name:
        arc_resp = supabase.table("khepri_arc_registry")\
            .select("id").eq("arc_name", arc_name).limit(1).execute()
        if not arc_resp.data:
            print(f"Arc not found: {arc_name}")
            sys.exit(1)
        q = q.eq("arc_id", arc_resp.data[0]["id"])

    snapshots = q.execute().data or []

    if not snapshots:
        print("No snapshots found. Nothing to attest.")
        sys.exit(0)

    print(f"Snapshots to attest: {len(snapshots)}")

    # ── Verify chain linkage before attesting ─────────────────────────────────
    print("\nVerifying chain linkage...")
    prev_hash = None
    all_linked = True
    for s in snapshots:
        seq = s["snapshot_seq"]
        if prev_hash is None:
            if s["prior_hash"] is not None:
                print(f"  [FAIL] seq={seq}: genesis record has non-null prior_hash")
                all_linked = False
            else:
                print(f"  [OK]   seq={seq}: genesis — prior_hash=NULL")
        else:
            if s["prior_hash"] != prev_hash:
                print(f"  [FAIL] seq={seq}: chain break — expected {prev_hash[:16]}..., got {s['prior_hash'] and s['prior_hash'][:16]}...")
                all_linked = False
            else:
                print(f"  [OK]   seq={seq}: prior_hash={s['prior_hash'][:16]}...")
        if not s.get("immutable_seal"):
            print(f"  [FAIL] seq={seq}: immutable_seal != TRUE")
            all_linked = False
        prev_hash = s["content_hash"]

    if not all_linked:
        print("\nCHAIN INTEGRITY FAILURE — aborting re-seal. Investigate before proceeding.")
        sys.exit(1)

    print("\nChain linkage: INTACT")

    # ── Compute attestation ───────────────────────────────────────────────────
    print("\nComputing attestation seal...")
    try:
        attestation_hash, chain_str = compute_attestation(snapshots)
    except EnvironmentError as e:
        print(f"\nFAIL: {e}")
        print("Set HMAC_SECRET in environment before running re-seal.")
        sys.exit(1)

    snapshot_ids = [s["id"] for s in snapshots]
    nulled = sum(1 for s in snapshots if s["seal"] is None)

    print(f"  Attestation hash: {attestation_hash}")
    print(f"  Snapshots covered: {len(snapshots)} ({nulled} with null seal)")
    print(f"  Chain string:     {chain_str[:80]}{'...' if len(chain_str) > 80 else ''}")

    if dry_run:
        print("\nDRY RUN complete. No records written.")
        print(SEP)
        return

    # ── Write SEAL_MILESTONE to threshold_registry ────────────────────────────
    print("\nWriting SEAL_MILESTONE to khepri_threshold_registry...")

    witness_statement = (
        "Sovereign re-seal attestation. HMAC_SECRET brought online after initial "
        f"chain was written. Chain verified intact across {len(snapshots)} snapshot(s). "
        "Attestation seal covers all content_hashes in sequence order. "
        f"Snapshots with null seal: {nulled}. "
        "Snapshots remain append-only and unmodified — this record is the proof "
        "of verification, not a mutation. APPEND_ONLY policy preserved."
    )

    resp = supabase.table("khepri_threshold_registry").insert({
        "sealed_at": datetime.now(timezone.utc).isoformat(),
        "threshold_type": "SEAL_MILESTONE",
        "from_state": "PRE_HMAC — snapshots present without HMAC seal",
        "to_state": "HMAC_ACTIVE — chain attested under active HMAC_SECRET",
        "evidence_snapshots": snapshot_ids,
        "witness_statement": witness_statement,
        "content_hash": attestation_hash,
        "externally_legible": False,
    }).execute()

    if resp.data:
        milestone_id = resp.data[0]["id"]
        print(f"  SEAL_MILESTONE recorded: {milestone_id}")
        print(f"  Attestation hash:        {attestation_hash}")
        print(f"\nRe-seal complete. Chain is attested. HMAC_ACTIVE.")
    else:
        print("  ERROR: Insert returned no data. Check Supabase permissions.")
        sys.exit(1)

    print(SEP)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KHEPRI Sovereign Re-Seal")
    parser.add_argument("--dry-run", action="store_true", help="Compute only, do not write")
    parser.add_argument("--arc-name", type=str, help="Restrict to named arc")
    args = parser.parse_args()
    run(dry_run=args.dry_run, arc_name=args.arc_name)
