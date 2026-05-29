"""GitHub webhook signature verification helpers."""

from __future__ import annotations

import hashlib
import hmac


def verify_signature(payload: bytes, signature_header: str | None, secret: str) -> bool:
    """Verify a GitHub `X-Hub-Signature-256` header."""

    if not signature_header:
        return False

    if not signature_header.startswith("sha256="):
        return False

    provided_signature = signature_header.removeprefix("sha256=").strip().lower()
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(provided_signature, expected_signature)

