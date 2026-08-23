from types import SimpleNamespace

import pytest

from bot.ai import AIServiceError, OpenAIAnalyzer
from bot.models import Classification, Review


class FakeResponses:
    def __init__(self, responses) -> None:
        self.responses = iter(responses)
        self.calls: list[dict] = []

    async def parse(self, **kwargs):
        self.calls.append(kwargs)
        return next(self.responses)


class FakeClient:
    def __init__(self, responses) -> None:
        self.responses = FakeResponses(responses)


class Parsed:
    def __init__(self, parsed, *, usage=None, response_id="resp_test") -> None:
        self.output_parsed = parsed
        self.usage = usage
        self.id = response_id
        self.model = "gpt-5.6-luna"


def _classification() -> Classification:
    return Classification(
        is_poem=True,
        type="senryu",
        confidence=0.8,
        normalized_lines=["句"],
    )


def _review() -> Review:
    return Review(
        comment="講評です。",
        ratings={
            "情景": 4,
            "余韻": 5,
            "独創性": 4,
            "言葉選び": 4,
            "ユーモア・風刺": 3,
        },
        overall=4,
    )


@pytest.mark.asyncio
async def test_analyzer_makes_classification_and_review_as_separate_calls() -> None:
    client = FakeClient([Parsed(_classification()), Parsed(_review())])
    analyzer = OpenAIAnalyzer(
        client=client,
        classification_model="gpt-5.6-luna",
        review_model="gpt-5.6-luna",
        reasoning_effort="max",
    )

    classification = await analyzer.classify("春の句")
    review = await analyzer.review("春の句", classification)

    assert classification.type.value == "senryu"
    assert review.overall == 4
    assert len(client.responses.calls) == 2
    assert client.responses.calls[0]["model"] == "gpt-5.6-luna"
    assert client.responses.calls[0]["reasoning"] == {"effort": "max"}
    assert client.responses.calls[0]["text_format"] is Classification
    assert client.responses.calls[1]["text_format"] is Review
    assert client.responses.calls[1]["reasoning"] == {"effort": "max"}
    assert "image_generation" not in str(client.responses.calls[1])


@pytest.mark.asyncio
async def test_analyzer_raises_when_structured_output_is_missing() -> None:
    client = FakeClient([Parsed(None)])
    analyzer = OpenAIAnalyzer(client=client, reasoning_effort="max")

    with pytest.raises(AIServiceError, match="structured"):
        await analyzer.classify("春の句")


@pytest.mark.asyncio
async def test_analyzer_logs_one_usage_event_for_each_openai_response(caplog) -> None:
    usage = SimpleNamespace(
        input_tokens=10,
        output_tokens=4,
        total_tokens=14,
        input_tokens_details=SimpleNamespace(cached_tokens=0, cache_write_tokens=0),
        output_tokens_details=SimpleNamespace(reasoning_tokens=0),
    )
    client = FakeClient(
        [
            Parsed(_classification(), usage=usage, response_id="resp_classify"),
            Parsed(_review(), usage=usage, response_id="resp_review"),
        ]
    )
    analyzer = OpenAIAnalyzer(client=client, reasoning_effort="max")

    with caplog.at_level("INFO", logger="bot.ai"):
        classification = await analyzer.classify("春の句")
        await analyzer.review("春の句", classification)

    usage_events = [
        record for record in caplog.records if record.message.startswith("openai_usage ")
    ]
    assert len(usage_events) == 2
    assert '"operation":"classification"' in usage_events[0].message
    assert '"operation":"review"' in usage_events[1].message
    assert '"input_tokens":10' in usage_events[0].message
    assert '"estimated_cost_usd":6.8e-06' in usage_events[0].message
