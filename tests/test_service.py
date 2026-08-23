import pytest

from bot.models import AnalysisResult, Classification, Review
from bot.service import PoemAnalysisService


class FakeAI:
    def __init__(self, classification: Classification, review: Review) -> None:
        self.classification = classification
        self.review_result = review
        self.classify_calls: list[str] = []
        self.review_calls: list[tuple[str, Classification]] = []

    async def classify(self, text: str) -> Classification:
        self.classify_calls.append(text)
        return self.classification

    async def review(self, text: str, classification: Classification) -> Review:
        self.review_calls.append((text, classification))
        return self.review_result


class FakeComposer:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def compose(self, text: str) -> bytes:
        self.calls.append(text)
        return b"png-bytes"


def _review() -> Review:
    return Review(
        comment="講評です。",
        ratings={
            "情景": 4,
            "余韻": 5,
            "独創性": 4,
        },
        overall=4,
    )


@pytest.mark.asyncio
async def test_non_poem_stops_after_the_first_openai_call() -> None:
    classification = Classification(
        is_poem=False,
        type="other",
        confidence=0.95,
        extracted_text="",
        normalized_lines=["説明"],
    )
    ai = FakeAI(classification, _review())
    composer = FakeComposer()
    service = PoemAnalysisService(ai=ai, composer=composer)

    assert await service.analyze("これは質問です") is None
    assert ai.classify_calls == ["これは質問です"]
    assert ai.review_calls == []
    assert composer.calls == []


@pytest.mark.asyncio
async def test_poem_uses_extracted_text_for_the_review_image() -> None:
    classification = Classification(
        is_poem=True,
        type="haiku",
        confidence=0.95,
        extracted_text="元の作品",
        normalized_lines=["整形された句"],
    )
    ai = FakeAI(classification, _review())
    composer = FakeComposer()
    service = PoemAnalysisService(ai=ai, composer=composer)

    result = await service.analyze("前置きの会話。元の作品。後置きの説明")

    assert isinstance(result, AnalysisResult)
    assert result is not None
    assert result.classification is classification
    assert result.review is ai.review_result
    assert result.image_bytes == b"png-bytes"
    assert ai.classify_calls == ["前置きの会話。元の作品。後置きの説明"]
    assert ai.review_calls == [
        ("前置きの会話。元の作品。後置きの説明", classification)
    ]
    assert composer.calls == ["元の作品"]


@pytest.mark.asyncio
async def test_target_without_an_extracted_text_stops_before_review() -> None:
    classification = Classification(
        is_poem=True,
        type="senryu",
        confidence=0.95,
        extracted_text="",
        normalized_lines=["候補"],
    )
    ai = FakeAI(classification, _review())
    composer = FakeComposer()
    service = PoemAnalysisService(ai=ai, composer=composer)

    assert await service.analyze("候補") is None
    assert ai.review_calls == []
    assert composer.calls == []


@pytest.mark.asyncio
async def test_non_contiguous_extraction_is_discarded_without_a_second_call() -> None:
    classification = Classification(
        is_poem=True,
        type="senryu",
        confidence=0.95,
        extracted_text="整形された句",
        normalized_lines=["整形された句"],
    )
    ai = FakeAI(classification, _review())
    composer = FakeComposer()
    service = PoemAnalysisService(ai=ai, composer=composer)

    assert await service.analyze("元の作品") is None
    assert ai.review_calls == []
    assert composer.calls == []
