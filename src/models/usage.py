"""Pydantic models for usage logging."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UsageLog(BaseModel):
    """A single tool call usage record."""

    id: int | None = None
    api_key_id: int
    tool_name: str
    success: bool = True
    error_msg: str | None = None
    called_at: datetime = Field(default_factory=datetime.utcnow)
