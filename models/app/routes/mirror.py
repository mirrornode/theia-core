"""
models/app/routes/mirror.py — POST /api/mirror ingest endpoint.

THEIA receives canonical MirrorNodeEvent (mirror.v1) envelopes from any
node in the network and hands them to the KHEPRI witness store.

Build order (per sovereign declaration):
  [x] Store first  — KHEPRI Supabase persistence (this file)
  [ ] HMAC seal    — enforce X-Mirror-Signature after store is live

Protocol Rule 1 (enforced here):
  The response body contains ONLY a write-confirmation receipt.
  KHEPRI witness data MUST NOT be forwarded to PTAH or any triad agent.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from models.events import MirrorNodeEvent
from khepri.witness import ingest

log = logging.getLogger("theia.mirror")

router = APIRouter(prefix="/api", tags=["mirror"])


@router.post("/mirror")
async def ingest_mirror_event(
    event: MirrorNodeEvent,
    x_mirror_keyid: Optional[str] = Header(default=None, alias="X-Mirror-KeyId"),
    x_mirror_signature: Optional[str] = Header(default=None, alias="X-Mirror-Signature"),
):
    """
    Ingest a MirrorNodeEvent into the KHEPRI witness store.

    Authentication
    --------------
    HMAC verification is deliberately deferred until the store layer is
    confirmed live (sovereign instruction: "Store first").  The TODO below
    marks exactly where the seal goes.  Events are accepted if they pass
    Pydantic schema validation.

    # TODO: HMAC seal — uncomment when store is confirmed live.
    # from khepri.hmac import verify_or_raise
    # verify_or_raise(event, x_mirror_keyid, x_mirror_signature)

    Persistence
    -----------
    All ingestion is handled by khepri.witness.ingest().  The function:
      - Logs every arriving event to khepri_ingestion_log
      - Appends an immutable snapshot to khepri_witness_snapshots
      - Links the snapshot into the hash chain (content_hash → prior_hash)
      - Returns a minimal receipt — no witness data leaks back to callers
    """
    log.info(
        "mirror.ingest",
        extra={
            "mirror_id": event.id,
            "mirror_source": event.source,
            "mirror_type": event.type,
            "mirror_level": event.level,
        },
    )

    try:
        receipt = ingest(event.model_dump())
    except Exception as exc:
        log.exception("khepri.ingest_error", extra={"mirror_id": event.id})
        # Do not expose internal error details — return 500 cleanly
        raise HTTPException(status_code=500, detail="witness store unavailable") from exc

    # Receipt only — Protocol Rule 1: do not surface witness data to callers
    return {"received": True, "id": event.id, "khepri": receipt.get("khepri")}
