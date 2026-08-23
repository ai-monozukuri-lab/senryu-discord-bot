from bot.formatting import format_reply, format_stars
from bot.models import Classification, Review


def test_format_stars_uses_five_slots() -> None:
    assert format_stars(1) == "★☆☆☆☆"
    assert format_stars(5) == "★★★★★"


def test_format_reply_contains_type_original_text_comment_and_all_ratings() -> None:
    classification = Classification(
        is_poem=True,
        type="senryu",
        confidence=0.9,
        normalized_lines=["normalized"],
    )
    review = Review(
        comment="季節の気配が伝わります。",
        ratings={
            "情景": 4,
            "余韻": 5,
            "独創性": 4,
            "言葉選び": 4,
            "ユーモア・風刺": 3,
        },
        overall=4,
    )

    body = format_reply(classification, "元の\n作品", review)

    assert "作品種別: 川柳" in body
    assert "元の\n作品" in body
    assert "季節の気配が伝わります。" in body
    assert "情景: ★★★★☆" in body
    assert "ユーモア・風刺: ★★★☆☆" in body
    assert "総合評価: ★★★★☆" in body
