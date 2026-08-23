from bot.formatting import format_reply, format_stars
from bot.models import Classification, Review


def test_format_stars_uses_five_slots() -> None:
    assert format_stars(1) == "★☆☆☆☆"
    assert format_stars(5) == "★★★★★"


def test_format_reply_omits_type_and_original_text_but_keeps_review_and_ratings() -> None:
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
        },
        overall=4,
    )

    body = format_reply(classification, "元の\n作品", review)

    assert body.splitlines()[0] == "川柳を検出しました！"
    lines = body.splitlines()
    assert lines[1] == "総合評価: ★★★★☆"
    assert lines[2] == "情景: ★★★★☆"
    assert lines[3] == "余韻: ★★★★★"
    assert lines[4] == "独創性: ★★★★☆"
    assert lines[5] == "季節の気配が伝わります。"
    assert "\n評価\n" not in body
    assert "\n講評\n" not in body
    assert "作品種別" not in body
    assert "作品:" not in body
    assert "元の\n作品" not in body
    assert "季節の気配が伝わります。" in body
    assert "情景: ★★★★☆" in body
