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
    def __init__(self, parsed) -> None:
        self.output_parsed = parsed


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
    analyzer = OpenAIAnalyzer(client=client, classification_model="gpt-5.6", review_model="gpt-5.6")

    classification = await analyzer.classify("春の句")
    review = await analyzer.review("春の句", classification)

    assert classification.type.value == "senryu"
    assert review.overall == 4
    assert len(client.responses.calls) == 2
    assert client.responses.calls[0]["model"] == "gpt-5.6"
    assert client.responses.calls[0]["text_format"] is Classification
    assert client.responses.calls[1]["text_format"] is Review
    assert "image_generation" not in str(client.responses.calls[1])


@pytest.mark.asyncio
async def test_analyzer_raises_when_structured_output_is_missing() -> None:
    client = FakeClient([Parsed(None)])
    analyzer = OpenAIAnalyzer(client=client)

    with pytest.raises(AIServiceError, match="structured"):
        await analyzer.classify("春の句")
