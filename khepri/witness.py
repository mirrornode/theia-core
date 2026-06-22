"""
khepri/witness.py — KHEPRI ingestion logic.

Five Protocol Rules (must never be violated):
  1. No feedback  — zero write path back to PTAH, triad, or middleware.
  2. Append-only  — no UPDATE, no DELETE, ever.
  3. No real-time interpretation — witness observes pattern over time, not
     single events.
  4. Threshold records require sovereign authorization to become externally
     legible (externally_legible stays false until explicitly set).
  5. Content hash chain is unbroken — every snapshot links to the prior
     snapshot via prior_hash.

This module accepts a MirrorNodeEvent, derives a witness snapshot from it,
persists the snapshot to Supabase, and writes an ingestion log entry.
It never returns data to the caller that could influence PTAH or the triad.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from khepri.db import supabase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()


def _latest_snapshot_hash(arc_id: str) -> Optional[str]:
    """
    Fetch the content_hash of the most recent snapshot for this arc so we
    can chain it as prior_hash.  Returns None for the genesis record.
    """
    resp = (
        supabase.table("khepri_witness_snapshots")
        .select("content_hash")
        .eq("arc_id", arc_id)
        .order("snapshot_seq", desc=True)
        .limit(1)
        .execute()
    )
    if resp.data:
        return resp.data[0]["content_hash"]
    return None


def _resolve_arc_id(arc_name: Optional[str] = None) -> Optional[str]:
    """
    Look up the open arc by name (or fall back to the latest open arc if
    no name is supplied).  Returns the arc UUID or None if no open arc exists.
    """
    if arc_name:
        resp = (
            supabase.table("khepri_arc_registry")
            .select("id")
            .eq("arc_name", arc_name)
            .eq("sealed", False)
            .limit(1)
            .execute()
        )
    else:
        resp = (
            supabase.table("khepri_arc_registry")
            .select("id")
            .eq("sealed", False)
            .order("opened_at", desc=True)
            .limit(1)
            .execute()
        )
    if resp.data:
        return resp.data[0]["id"]
    return None


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def ingest(event: dict) -> dict:
    """
    Ingest a MirrorNodeEvent dict into the KHEPRI witness store.

    Steps:
      1. Log the raw event arrival in khepri_ingestion_log.
      2. Resolve the active arc.
      3. Build the witness snapshot (no real-time interpretation — we
         capture the envelope metadata as observed).
      4. Compute content_hash over the snapshot fields.
      5. Fetch prior_hash from the most recent snapshot (hash chain).
      6. Insert the snapshot.
      7. Update the ingestion log entry to mark produced_snapshot=True.
      8. Increment the arc snapshot_count.
      9. Return a minimal receipt — only enough for the caller to confirm
         the write succeeded.  No witness data leaks back into the triad.

    Protocol Rule 1 — the returned dict MUST NOT be forwarded to PTAH or
    any triad agent.  It is a write-confirmation receipt only.
    """
    now_utc = datetime.now(timezone.utc).isoformat()
    raw_hash = _sha256(json.dumps(event, sort_keys=True, default=str))

    # --- Step 1: Log arrival ---
    log_resp = (
        supabase.table("khepri_ingestion_log")
        .insert({
            "received_at": now_utc,
            "source_agent": event.get("source", "UNKNOWN"),
            "event_type": event.get("type", "UNKNOWN"),
            "raw_payload_hash": raw_hash,
            "produced_snapshot": False,
        })
        .execute()
    )
    log_id = log_resp.data[0]["id"] if log_resp.data else None

    # --- Step 2: Resolve arc ---
    arc_name = (event.get("data") or {}).get("arc_name")
    arc_id = _resolve_arc_id(arc_name)

    if not arc_id:
        # No open arc — drop with explanation
        if log_id:
            supabase.table("khepri_ingestion_log").update({
                "dropped_reason": "no_open_arc",
            }).eq("id", log_id).execute()
        return {"received": True, "id": event.get("id"), "khepri": "dropped:no_open_arc"}

    # --- Step 3: Build snapshot fields ---
    data = event.get("data") or {}
    meta = event.get("meta") or {}
    trace = event.get("trace") or {}

    arc_phase      = data.get("arc_phase", "UNKNOWN")
    arc_depth      = int(data.get("arc_depth", 0))
    arc_velocity   = data.get("arc_velocity", "STABLE")
    coherence      = data.get("coherence_signal", "NOMINAL")
    threshold_flag = bool(data.get("threshold_flag", False))
    witness_note   = data.get("witness_note")

    # Metric observations (all optional — witness records what it receives)
    hold_density_7d        = data.get("hold_density_7d")
    seal_count_total       = data.get("seal_count_total")
    s1_exposure            = data.get("s1_exposure")
    sovereign_hold_count   = data.get("sovereign_hold_count")
    decision_lineage_depth = data.get("decision_lineage_depth")

    # --- Step 4: Content hash ---
    hash_payload = "|".join([
        event.get("id", ""),
        event.get("ts", now_utc),
        event.get("source", ""),
        event.get("type", ""),
        arc_id,
        arc_phase,
        str(arc_depth),
        arc_velocity,
        coherence,
        str(threshold_flag),
        witness_note or "",
    ])
    content_hash = _sha256(hash_payload)

    # --- Step 5: Prior hash (chain integrity) ---
    prior_hash = _latest_snapshot_hash(arc_id)

    # --- Step 6: Insert snapshot ---
    snapshot_payload = {
        "sealed_at": now_utc,
        "trigger_event": event.get("type"),
        "trigger_agent": meta.get("agent") or event.get("source", "UNKNOWN"),
        "source_trace_id": trace.get("runId"),
        "source_hold_id": data.get("hold_id"),
        "ptah_eval_hash": data.get("ptah_eval_hash"),
        "arc_id": arc_id,
        "arc_phase": arc_phase if arc_phase in (
            "EMERGENCE", "CONSOLIDATION", "THRESHOLD",
            "INTEGRATION", "SOVEREIGNTY", "UNKNOWN"
        ) else "UNKNOWN",
        "arc_depth": arc_depth,
        "arc_velocity": arc_velocity if arc_velocity in (
            "ACCELERATING", "STABLE", "PAUSING", "REVERSING"
        ) else "STABLE",
        "hold_density_7d": hold_density_7d,
        "seal_count_total": seal_count_total,
        "s1_exposure": s1_exposure,
        "sovereign_hold_count": sovereign_hold_count,
        "decision_lineage_depth": decision_lineage_depth,
        "witness_note": witness_note,
        "coherence_signal": coherence if coherence in (
            "NOMINAL", "FRAGMENTED", "CRYSTALLIZING", "SEALED"
        ) else "NOMINAL",
        "threshold_flag": threshold_flag,
        "content_hash": content_hash,
        "prior_hash": prior_hash,
        "immutable_seal": True,
    }

    snap_resp = (
        supabase.table("khepri_witness_snapshots")
        .insert(snapshot_payload)
        .execute()
    )
    snapshot_id = snap_resp.data[0]["id"] if snap_resp.data else None
    snapshot_seq = snap_resp.data[0]["snapshot_seq"] if snap_resp.data else None

    # --- Step 7: Update ingestion log ---
    if log_id and snapshot_id:
        supabase.table("khepri_ingestion_log").update({
            "produced_snapshot": True,
            "snapshot_id": snapshot_id,
        }).eq("id", log_id).execute()

    # --- Step 8: Increment arc snapshot count ---
    if snapshot_id:
        # Use raw SQL increment — supabase-py RPC or raw increment pattern
        supabase.rpc("khepri_arc_increment_snapshot_count", {"p_arc_id": arc_id}).execute()

    # --- Step 9: Receipt only — do not surface witness data to the triad ---
    return {
        "received": True,
        "id": event.get("id"),
        "khepri": {
            "sealed": True,
            "snapshot_seq": snapshot_seq,
            "arc_id": arc_id,
            "content_hash": content_hash,
        }
    }
