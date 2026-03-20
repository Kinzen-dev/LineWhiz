"""Pydantic models for API keys and user tiers."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Tier(StrEnum):
    """Subscription tier levels."""

    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"


class APIKeyRecord(BaseModel):
    """Database record for an API key."""

    id: int
    key_hash: str = Field(description="SHA-256 hash of the API key — never store plaintext")
    tier: Tier = Tier.FREE
    label: str | None = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
