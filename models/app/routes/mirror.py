from fastapi import APIRouter, Header, HTTPException
from typing import Optional

from theia_core.models import MirrorNodeEvent  # adjust import if needed
from theia.logging import bind_context

router = APIRouter(prefix="/api", tags=["mirror"])


@router.post("/mirror")
async def ingest_mirror_event(
    event: MirrorNodeEvent,
    x_mirror_keyid: Optional[str] = Header(default=None, alias="X-Mirror-KeyId"),
    x_mirror_signature: Optional[str] = Header(default=None, alias="X-Mirror-Signature"),
):
    # Bind context for logs
    bind_context(
        mirror_id=event.id,
        mirror_source=event.source,
        mirror_type=event.type,
        mirror_level=event.level,
    )

    # TODO: HMAC verification using event.auth or headers if you want it enforced.
    # For now, we accept everything that passes schema validation.

    # TODO: enqueue to a queue/bus, or persist to DB/log store.
    # For now, just acknowledge.
    return {"received": True, "id": event.id}
