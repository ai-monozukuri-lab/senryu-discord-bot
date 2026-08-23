import pytest
from pydantic import ValidationError

from bot.models import Classification, PoemType, Ratings, Review


def test_classification_marks_only_haiku_and_senryu_as_targets() -> None:
    haiku = Classification(
        is_poem=True,
        type="haiku",
        confidence=0.91,
        source_text="古池や\n蛙飛び込む\n水の音",
        extracted_text="古池や\n蛙飛び込む\n水の音",
        normalized_lines=["古池や", "蛙飛び込む", "水の音"],
    )
    other = Classification(
        is_poem=False,
        type="other",
        confidence=0.99,
        source_text="",
        extracted_text="",
        normalized_lines=["これは説明です"],
    )

    assert haiku.type is PoemType.HAIKU
    assert haiku.is_target is True
    assert other.is_target is False


def test_non_poem_may_return_an_empty_normalized_line() -> None:
    result = Classification(
        is_poem=False,
        type="other",
        confidence=0.99,
        source_text="",
        extracted_text="",
        normalized_lines=[""],
    )

    assert result.is_target is False


def test_classification_rejects_invalid_confidence_and_empty_lines() -> None:
    with pytest.raises(ValidationError):
        Classification(
            is_poem=True,
            type="senryu",
            confidence=1.1,
            source_text="句",
            extracted_text="句",
            normalized_lines=["句"],
        )

    with pytest.raises(ValidationError):
        Classification(
            is_poem=True,
            type="senryu",
            confidence=0.5,
            source_text="句",
            extracted_text="句",
            normalized_lines=[],
        )


def test_ratings_keep_the_public_japanese_keys_and_render_stars() -> None:
    ratings = Ratings(
        情景=4,
        余韻=5,
        独創性=4,
    )

    assert ratings.model_dump(by_alias=True) == {
        "情景": 4,
        "余韻": 5,
        "独創性": 4,
    }
    assert ratings.as_stars()["情景"] == "★★★★☆"
    assert ratings.as_stars()["余韻"] == "★★★★★"


def test_review_rejects_scores_outside_one_to_five() -> None:
    with pytest.raises(ValidationError):
        Review(
            comment="講評です。",
            ratings={
                "情景": 6,
                "余韻": 5,
                "独創性": 4,
            },
            overall=4,
        )
