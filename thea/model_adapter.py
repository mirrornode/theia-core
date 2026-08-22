from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlparse

_MAX_RESPONSE_BYTES = 2_097_152
_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


@dataclass(frozen=True)
class LocalModelConfig:
    endpoint: str = "http://127.0.0.1:11434/v1/chat/completions"
    model: str = "thea-local-reviewer"
    timeout_seconds: int = 120

    @classmethod
    def from_env(cls) -> "LocalModelConfig":
        timeout_raw = os.environ.get("THEA_MODEL_TIMEOUT", "120")
        try:
            timeout = int(timeout_raw)
        except ValueError as exc:
            raise LocalModelUnavailable("THEA_MODEL_TIMEOUT must be an integer") from exc
        if not 1 <= timeout <= 600:
            raise LocalModelUnavailable("THEA_MODEL_TIMEOUT must be between 1 and 600 seconds")
        return cls(
            endpoint=os.environ.get("THEA_MODEL_ENDPOINT", cls.endpoint),
            model=os.environ.get("THEA_MODEL_NAME", cls.model),
            timeout_seconds=timeout,
        )


class LocalModelUnavailable(RuntimeError):
    pass


def _validate_local_endpoint(endpoint: str) -> None:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"}:
        raise LocalModelUnavailable("local model endpoint must use http or https")
    if parsed.hostname not in _LOOPBACK_HOSTS:
        raise LocalModelUnavailable(
            "Thea v0.1 refuses non-loopback model endpoints; add a separately governed remote-model adapter if that boundary is ever authorized"
        )
    if parsed.username or parsed.password:
        raise LocalModelUnavailable("credentials must not be embedded in the model endpoint URL")


def review_with_local_model(system_prompt: str, user_prompt: str, config: LocalModelConfig | None = None) -> str:
    """Call an operator-owned OpenAI-compatible loopback endpoint.

    No cloud fallback exists by design. If the local verifier model is absent
    or misconfigured, callers retain deterministic findings and mark model
    review unavailable.
    """
    cfg = config or LocalModelConfig.from_env()
    _validate_local_endpoint(cfg.endpoint)
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
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
            if len(raw) > _MAX_RESPONSE_BYTES:
                raise LocalModelUnavailable("local model response exceeds maximum size")
            payload = json.loads(raw.decode("utf-8"))
    except LocalModelUnavailable:
        raise
    except (OSError, urllib.error.URLError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LocalModelUnavailable(str(exc)) from exc

    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LocalModelUnavailable("local model returned an unsupported response shape") from exc
    if not isinstance(content, str):
        raise LocalModelUnavailable("local model content must be a string")
    return content
