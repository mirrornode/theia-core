from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class MirrorNodeTrace(BaseModel):
    runId: str
    ruleId: str
    attempt: int = 1
    cursor: Optional[Any] = None


class MirrorNodeMeta(BaseModel):
    agent: str
    version: str
    region: Optional[str] = None


class MirrorNodeAuth(BaseModel):
    hmac: Optional[str] = None
    keyId: Optional[str] = None
    algo: str = "HMAC-SHA256"


class MirrorNodeEvent(BaseModel):
    """
    Canonical MirrorNodeEvent v1 envelope.

    This should match the schema you defined:
    - schema: "mirror.v1"
    - id: uuid-v4 string
    - ts: ISO8601
    - source: "harpa::<ruleName>::<stepName>" (or similar)
    - type: signal | error | heartbeat | metric
    - level: info | warn | error | debug
    - subject: short human title
    - data: arbitrary JSON payload
    - tags: list of tags (["harpa","env:prod"])
    - trace: trace info (runId, ruleId, attempt, cursor)
    - meta: agent metadata
    - auth: optional in-envelope auth (plus headers)
    """
    schema: str = "mirror.v1"
    id: str
    ts: str
    source: str
    type: str
    level: str
    subject: str
    data: Dict[str, Any]
    tags: List[str] = []
    trace: MirrorNodeTrace
    meta: MirrorNodeMeta
    auth: MirrorNodeAuth = MirrorNodeAuth()
