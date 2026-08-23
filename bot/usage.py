"""Token usage extraction and estimated OpenAI cost logging."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

_MILLION = Decimal(1_000_000)
_CACHE_WRITE_MULTIPLIER = Decimal("1.25")


@dataclass(frozen=True)
class ModelPricing:
    """List prices in USD per one million tokens."""

    input_per_million: Decimal | float | int
    cached_input_per_million: Decimal | float | int
    output_per_million: Decimal | float | int

    def __post_init__(self) -> None:
        for field_name in (
            "input_per_million",
            "cached_input_per_million",
            "output_per_million",
        ):
            try:
                value = Decimal(str(getattr(self, field_name)))
            except (InvalidOperation, ValueError) as exc:
                raise ValueError(f"{field_name} must be a number") from exc
            if value < 0:
                raise ValueError(f"{field_name} must not be negative")
            object.__setattr__(self, field_name, value)


@dataclass(frozen=True)
class UsageEstimate:
    """Token counts and the estimated USD cost for one response."""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    cached_input_tokens: int
    cache_write_input_tokens: int
    reasoning_output_tokens: int
    estimated_cost_usd: float


DEFAULT_PRICING: dict[str, ModelPricing] = {
    # The gpt-5.6 alias currently routes to the Sol model.
    "gpt-5.6": ModelPricing(5.0, 0.5, 30.0),
    "gpt-5.6-sol": ModelPricing(5.0, 0.5, 30.0),
    "gpt-5.6-terra": ModelPricing(2.0, 0.2, 12.0),
    "gpt-5.6-luna": ModelPricing(0.2, 0.02, 1.2),
}


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _nonnegative_int(value: Any) -> int:
    try:
        parsed = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return max(parsed, 0)


class PricingTable:
    """Resolve model aliases and calculate costs from Responses usage objects."""

    def __init__(self, pricing: Mapping[str, ModelPricing] | None = None) -> None:
        self._pricing = dict(DEFAULT_PRICING)
        if pricing:
            self._pricing.update(pricing)

    @classmethod
    def from_json(cls, raw: str | None) -> PricingTable:
        """Merge optional JSON pricing overrides into the built-in table."""

        if not raw or not raw.strip():
            return cls()
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("OPENAI_PRICING_JSON must be valid JSON") from exc
        if not isinstance(decoded, dict):
            raise ValueError("OPENAI_PRICING_JSON must be a JSON object")

        overrides: dict[str, ModelPricing] = {}
        for model, values in decoded.items():
            if not isinstance(model, str) or not model.strip() or not isinstance(values, dict):
                raise ValueError("each pricing entry must map a model name to an object")
            try:
                overrides[model] = ModelPricing(
                    input_per_million=values["input_per_million"],
                    cached_input_per_million=values["cached_input_per_million"],
                    output_per_million=values["output_per_million"],
                )
            except KeyError as exc:
                raise ValueError(
                    "pricing entries require input_per_million, "
                    "cached_input_per_million, and output_per_million"
                ) from exc
        return cls(overrides)

    def resolve(
        self,
        model: str | None,
        fallback_model: str | None = None,
    ) -> tuple[str | None, ModelPricing | None]:
        candidates = [candidate for candidate in (model, fallback_model) if candidate]
        for candidate in candidates:
            if candidate in self._pricing:
                return candidate, self._pricing[candidate]
            for known_model in self._pricing:
                if candidate.startswith(f"{known_model}-"):
                    return known_model, self._pricing[known_model]
        return None, None

    def estimate(
        self,
        model: str | None,
        usage: Any,
        fallback_model: str | None = None,
    ) -> UsageEstimate | None:
        pricing_model, pricing = self.resolve(model, fallback_model)
        if pricing is None or usage is None:
            return None

        input_tokens = _nonnegative_int(_field(usage, "input_tokens"))
        output_tokens = _nonnegative_int(_field(usage, "output_tokens"))
        total_tokens = _nonnegative_int(_field(usage, "total_tokens")) or (
            input_tokens + output_tokens
        )
        input_details = _field(usage, "input_tokens_details", {})
        output_details = _field(usage, "output_tokens_details", {})
        cached_tokens = min(
            _nonnegative_int(_field(input_details, "cached_tokens")), input_tokens
        )
        cache_write_tokens = min(
            _nonnegative_int(_field(input_details, "cache_write_tokens")),
            input_tokens - cached_tokens,
        )
        reasoning_tokens = _nonnegative_int(_field(output_details, "reasoning_tokens"))
        uncached_tokens = input_tokens - cached_tokens - cache_write_tokens

        cost = (
            Decimal(uncached_tokens) * pricing.input_per_million
            + Decimal(cached_tokens) * pricing.cached_input_per_million
            + Decimal(cache_write_tokens)
            * pricing.input_per_million
            * _CACHE_WRITE_MULTIPLIER
            + Decimal(output_tokens) * pricing.output_per_million
        ) / _MILLION
        return UsageEstimate(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cached_input_tokens=cached_tokens,
            cache_write_input_tokens=cache_write_tokens,
            reasoning_output_tokens=reasoning_tokens,
            estimated_cost_usd=round(float(cost), 8),
        )


def log_response_usage(
    response: Any,
    *,
    operation: str,
    requested_model: str,
    pricing_table: PricingTable,
    logger: logging.Logger,
) -> None:
    """Log usage metadata without logging request prompts or response content."""

    usage = _field(response, "usage")
    actual_model = _field(response, "model", requested_model) or requested_model
    estimate = pricing_table.estimate(actual_model, usage, fallback_model=requested_model)
    input_details = _field(usage, "input_tokens_details", {})
    output_details = _field(usage, "output_tokens_details", {})
    input_tokens = _nonnegative_int(_field(usage, "input_tokens")) if usage else None
    output_tokens = _nonnegative_int(_field(usage, "output_tokens")) if usage else None
    total_tokens = _nonnegative_int(_field(usage, "total_tokens")) if usage else None
    if usage and not total_tokens:
        total_tokens = (input_tokens or 0) + (output_tokens or 0)

    pricing_model, pricing = pricing_table.resolve(actual_model, requested_model)
    payload = {
        "event": "openai_usage",
        "operation": operation,
        "response_id": _field(response, "id"),
        "model": actual_model,
        "requested_model": requested_model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_input_tokens": _nonnegative_int(_field(input_details, "cached_tokens"))
        if usage
        else None,
        "cache_write_input_tokens": _nonnegative_int(
            _field(input_details, "cache_write_tokens")
        )
        if usage
        else None,
        "reasoning_output_tokens": _nonnegative_int(
            _field(output_details, "reasoning_tokens")
        )
        if usage
        else None,
        "pricing_model": pricing_model,
        "pricing_known": pricing is not None,
        "estimated_cost_usd": estimate.estimated_cost_usd if estimate else None,
    }
    logger.info(
        "openai_usage %s",
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    )
