from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class LocalModelConfig:
    endpoint: str = "http://127.0.0.1:11434/v1/chat/completions"
    model: str = "thea-local-reviewer"
    timeout_seconds: int = 120

    @classmethod
    def from_env(cls) -> "LocalModelConfig":
        return cls(
            endpoint=os.environ.get("THEA_MODEL_ENDPOINT", cls.endpoint),
            model=os.environ.get("THEA_MODEL_NAME", cls.model),
            timeout_seconds=int(os.environ.get("THEA_MODEL_TIMEOUT", "120")),
        )


class LocalModelUnavailable(RuntimeError):
    pass


def review_with_local_model(system_prompt: str, user_prompt: str, config: LocalModelConfig | None = None) -> str:
    """Call an operator-owned OpenAI-compatible local endpoint.

    No cloud fallback exists by design. If the local verifier model is absent,
    callers must retain deterministic findings and mark model review unavailable.
    """
    cfg = config or LocalModelConfig.from_env()
    body = json.dumps(
        {
            "model": cfg.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        cfg.endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=cfg.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise LocalModelUnavailable(str(exc)) from exc

    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LocalModelUnavailable("local model returned an unsupported response shape") from exc
