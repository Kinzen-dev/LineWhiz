"""API key validation using SHA-256 hash lookup.

MVP simplification: For initial launch, skip DB-backed auth.
Use env-var tier instead. DB-backed auth will be added in v1.1.
"""

from __future__ import annotations

import hashlib
import logging

logger = logging.getLogger("linewhiz.auth.api_keys")


def hash_api_key(key: str) -> str:
    """Hash an API key with SHA-256. Never store plaintext keys."""
    return hashlib.sha256(key.encode()).hexdigest()


async def validate_api_key(api_key: str) -> bool:
    """Validate an API key.

    MVP: Always returns True (env-var tier mode).
    v1.1: Will look up key_hash in the api_keys table.
    """
    # TODO(v1.1): Implement DB-backed key validation
    if not api_key:
        logger.warning("Empty API key provided")
        return False
    return True
