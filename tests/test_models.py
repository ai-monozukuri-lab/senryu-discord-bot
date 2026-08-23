import pytest
from pydantic import ValidationError

from bot.models import Classification, PoemType, Ratings, Review


def test_classification_marks_only_haiku_and_senryu_as_targets() -> None:
    haiku = Classification(
        is_poem=True,
        type="haiku",
        confidence=0.91,
        normalized_lines=["古池や", "蛙飛び込む", "水の音"],
    )
    other = Classification(
        is_poem=False,
        type="other",
        confidence=0.99,
        normalized_lines=["これは説明です"],
    )

    assert haiku.type is PoemType.HAIKU
    assert haiku.is_target is True
    assert other.is_target is False


def test_classification_rejects_invalid_confidence_and_empty_lines() -> None:
    with pytest.raises(ValidationError):
        Classification(is_poem=True, type="senryu", confidence=1.1, normalized_lines=["句"])

    with pytest.raises(ValidationError):
        Classification(is_poem=True, type="senryu", confidence=0.5, normalized_lines=[])


def test_ratings_keep_the_public_japanese_keys_and_render_stars() -> None:
    ratings = Ratings(
        情景=4,
        余韻=5,
        独創性=4,
        言葉選び=3,
        **{"ユーモア・風刺": 2},
    )

    assert ratings.model_dump(by_alias=True) == {
        "情景": 4,
        "余韻": 5,
        "独創性": 4,
        "言葉選び": 3,
        "ユーモア・風刺": 2,
    }
    assert ratings.as_stars()["情景"] == "★★★★☆"
    assert ratings.as_stars()["余韻"] == "★★★★★"
    assert ratings.as_stars()["ユーモア・風刺"] == "★★☆☆☆"


def test_review_rejects_scores_outside_one_to_five() -> None:
    with pytest.raises(ValidationError):
        Review(
            comment="講評です。",
            ratings={
                "情景": 6,
                "余韻": 5,
                "独創性": 4,
                "言葉選び": 4,
                "ユーモア・風刺": 3,
            },
            overall=4,
        )
