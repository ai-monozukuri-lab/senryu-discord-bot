import json
import logging
from types import SimpleNamespace

from bot.usage import ModelPricing, PricingTable, log_response_usage


def _usage():
    return SimpleNamespace(
        input_tokens=1_000,
        output_tokens=200,
        total_tokens=1_200,
        input_tokens_details=SimpleNamespace(cached_tokens=100, cache_write_tokens=50),
        output_tokens_details=SimpleNamespace(reasoning_tokens=20),
    )


def test_pricing_table_calculates_standard_and_cached_token_costs() -> None:
    table = PricingTable(
        {
            "test-model": ModelPricing(
                input_per_million=5,
                cached_input_per_million=0.5,
                output_per_million=30,
            )
        }
    )

    estimate = table.estimate("test-model", _usage())

    assert estimate is not None
    assert estimate.input_tokens == 1_000
    assert estimate.output_tokens == 200
    assert estimate.total_tokens == 1_200
    assert estimate.cached_input_tokens == 100
    assert estimate.cache_write_input_tokens == 50
    assert estimate.reasoning_output_tokens == 20
    assert estimate.estimated_cost_usd == 0.0106125


def test_unknown_model_has_no_cost_estimate() -> None:
    assert PricingTable({}).estimate("unknown-model", _usage()) is None


def test_custom_json_pricing_overrides_defaults() -> None:
    table = PricingTable.from_json(
        '{"custom-model":{"input_per_million":1,"cached_input_per_million":0.1,"output_per_million":2}}'
    )

    assert table.estimate("custom-model", _usage()).estimated_cost_usd == 0.0013225


def test_log_response_usage_emits_json_without_prompt_content(caplog) -> None:
    response = SimpleNamespace(id="resp_test", model="test-model", usage=_usage())
    table = PricingTable(
        {
            "test-model": ModelPricing(
                input_per_million=5,
                cached_input_per_million=0.5,
                output_per_million=30,
            )
        }
    )

    with caplog.at_level(logging.INFO, logger="test.usage"):
        log_response_usage(
            response,
            operation="classification",
            requested_model="test-model",
            pricing_table=table,
            logger=logging.getLogger("test.usage"),
        )

    record = next(record for record in caplog.records if record.message.startswith("openai_usage "))
    payload = json.loads(record.message.removeprefix("openai_usage "))
    assert payload == {
        "event": "openai_usage",
        "operation": "classification",
        "response_id": "resp_test",
        "model": "test-model",
        "requested_model": "test-model",
        "input_tokens": 1_000,
        "output_tokens": 200,
        "total_tokens": 1_200,
        "cached_input_tokens": 100,
        "cache_write_input_tokens": 50,
        "reasoning_output_tokens": 20,
        "pricing_model": "test-model",
        "pricing_known": True,
        "estimated_cost_usd": 0.0106125,
    }
    assert "春の句" not in record.message
