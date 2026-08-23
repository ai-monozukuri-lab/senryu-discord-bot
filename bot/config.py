"""Environment-backed runtime settings."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


class ConfigurationError(ValueError):
    """Raised when a required or numeric setting is invalid."""


@dataclass(frozen=True)
class Settings:
    discord_token: str
    openai_api_key: str
    classification_model: str = "gpt-5.6"
    review_model: str = "gpt-5.6"
    image_template_path: Path = (
        Path(__file__).resolve().parent.parent / "assets" / "senryu_template.png"
    )
    font_path: Path | None = None
    dedup_ttl_seconds: float = 15 * 60
    dedup_max_entries: int = 10_000

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        values = os.environ if env is None else env

        def required(name: str) -> str:
            value = values.get(name, "").strip()
            if not value:
                raise ConfigurationError(f"{name} is required")
            return value

        def positive_float(name: str, default: float) -> float:
            raw = values.get(name)
            if raw is None or not raw.strip():
                return default
            try:
                parsed = float(raw)
            except ValueError as exc:
                raise ConfigurationError(f"{name} must be a positive number") from exc
            if parsed <= 0:
                raise ConfigurationError(f"{name} must be a positive number")
            return parsed

        def positive_int(name: str, default: int) -> int:
            raw = values.get(name)
            if raw is None or not raw.strip():
                return default
            try:
                parsed = int(raw)
            except ValueError as exc:
                raise ConfigurationError(f"{name} must be a positive integer") from exc
            if parsed <= 0:
                raise ConfigurationError(f"{name} must be a positive integer")
            return parsed

        font_value = values.get("FONT_PATH", "").strip()
        template_value = values.get("IMAGE_TEMPLATE_PATH", "").strip()
        default_template = Path(__file__).resolve().parent.parent / "assets" / "senryu_template.png"
        return cls(
            discord_token=required("DISCORD_TOKEN"),
            openai_api_key=required("OPENAI_API_KEY"),
            classification_model=(
                values.get("OPENAI_CLASSIFICATION_MODEL", "gpt-5.6").strip() or "gpt-5.6"
            ),
            review_model=values.get("OPENAI_REVIEW_MODEL", "gpt-5.6").strip() or "gpt-5.6",
            image_template_path=Path(template_value or default_template),
            font_path=Path(font_value) if font_value else None,
            dedup_ttl_seconds=positive_float("DEDUP_TTL_SECONDS", 15 * 60),
            dedup_max_entries=positive_int("DEDUP_MAX_ENTRIES", 10_000),
        )
