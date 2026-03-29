"""Environment configuration via pydantic Settings.

Loads all config from environment variables (or .env file).
Never hardcode tokens or secrets — env vars only.
"""

from __future__ import annotations

import logging
import sys
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LINE API credentials
    line_channel_access_token: str = ""
    line_channel_secret: str = ""

    # LineWhiz settings
    linewhiz_tier: Literal["free", "pro", "business"] = "pro"
    linewhiz_transport: Literal["stdio", "sse"] = "stdio"
    linewhiz_database_url: str = "sqlite:///linewhiz.db"
    linewhiz_log_level: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def setup_logging() -> logging.Logger:
    """Configure logging to stderr (NEVER stdout — breaks MCP STDIO)."""
    settings = get_settings()
    logger = logging.getLogger("linewhiz")
    logger.setLevel(getattr(logging, settings.linewhiz_log_level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
    return logger
