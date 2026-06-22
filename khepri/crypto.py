"""
khepri/crypto.py — HMAC-SHA256 seal generation and verification.

A seal is a 64-character hex HMAC-SHA256 digest over the canonical
JSON representation of a snapshot payload.  It is computed with a
secret loaded exclusively from the environment — never from arguments,
never from a default.  If the secret is absent the function raises
EnvironmentError and the system fails closed.

Protocol alignment:
  - Seal is computed over a deterministic canonical form (sorted keys,
    no whitespace) so the same payload always produces the same digest.
  - verify_seal recomputes the seal and uses hmac.compare_digest to
    prevent timing attacks.
  - Any missing HMAC_SECRET raises EnvironmentError immediately — the
    witness loop must not proceed without a valid seal.
"""

import hashlib
import hmac
import json
import os
from typing import Any, Dict


_ENV_KEY = "HMAC_SECRET"


def _get_secret() -> bytes:
    """
    Load the HMAC secret from the environment.
    Fails closed: raises EnvironmentError if the variable is absent or empty.
    """
    secret = os.environ.get(_ENV_KEY, "")
    if not secret:
        raise EnvironmentError(
            f"HMAC_SECRET is not set or is empty. "
            f"The witness loop cannot generate seals without it. "
            f"Set {_ENV_KEY} in your environment before proceeding."
        )
    return secret.encode()


def _canonical(payload: Dict[str, Any]) -> bytes:
    """
    Produce a deterministic byte representation of the payload.
    Keys are sorted; no extra whitespace.  Non-serialisable values
    (e.g. datetimes) are coerced to strings via default=str.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()


def generate_seal(payload: Dict[str, Any]) -> str:
    """
    Generate a 64-character hex HMAC-SHA256 seal over `payload`.

    Raises:
        EnvironmentError — if HMAC_SECRET is absent or empty.

    Returns:
        str — 64-character lowercase hex digest.
    """
    secret = _get_secret()
    canon = _canonical(payload)
    digest = hmac.new(secret, canon, hashlib.sha256).hexdigest()
    return digest


def verify_seal(payload: Dict[str, Any], seal: str) -> bool:
    """
    Verify that `seal` is the correct HMAC-SHA256 seal for `payload`.

    Uses hmac.compare_digest to prevent timing attacks.

    Raises:
        EnvironmentError — if HMAC_SECRET is absent or empty.

    Returns:
        bool — True if the seal is valid, False otherwise.
    """
    secret = _get_secret()
    canon = _canonical(payload)
    expected = hmac.new(secret, canon, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, seal)
