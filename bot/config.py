"""Environment-backed runtime settings."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CLASSIFICATION_MODEL = "gpt-5.6-luna"
DEFAULT_REVIEW_MODEL = "gpt-5.6-luna"
DEFAULT_REASONING_EFFORT = "max"
DEFAULT_IMAGE_TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "senryu_template.png"
)
DEFAULT_DEDUP_TTL_SECONDS = 15 * 60
DEFAULT_DEDUP_MAX_ENTRIES = 10_000


class ConfigurationError(ValueError):
    """Raised when a required secret is missing."""


@dataclass(frozen=True)
class Settings:
    discord_token: str
    openai_api_key: str
    classification_model: str = DEFAULT_CLASSIFICATION_MODEL
    review_model: str = DEFAULT_REVIEW_MODEL
    reasoning_effort: str = DEFAULT_REASONING_EFFORT
    image_template_path: Path = DEFAULT_IMAGE_TEMPLATE_PATH
    font_path: Path | None = None
    dedup_ttl_seconds: float = DEFAULT_DEDUP_TTL_SECONDS
    dedup_max_entries: int = DEFAULT_DEDUP_MAX_ENTRIES

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        values = os.environ if env is None else env

        def required(name: str) -> str:
            value = values.get(name, "").strip()
            if not value:
                raise ConfigurationError(f"{name} is required")
            return value

        return cls(
            discord_token=required("DISCORD_TOKEN"),
            openai_api_key=required("OPENAI_API_KEY"),
            classification_model=DEFAULT_CLASSIFICATION_MODEL,
            review_model=DEFAULT_REVIEW_MODEL,
            reasoning_effort=DEFAULT_REASONING_EFFORT,
            image_template_path=DEFAULT_IMAGE_TEMPLATE_PATH,
            font_path=None,
            dedup_ttl_seconds=DEFAULT_DEDUP_TTL_SECONDS,
            dedup_max_entries=DEFAULT_DEDUP_MAX_ENTRIES,
        )
