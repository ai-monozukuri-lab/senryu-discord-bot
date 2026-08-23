from io import BytesIO

import pytest
from PIL import Image, ImageFont

import bot.image as image_module
from bot.image import ImageCompositionError, TemplateImageComposer


def _make_template(path) -> None:
    image = Image.new("RGBA", (300, 500), (241, 233, 211, 255))
    image.save(path, format="PNG")


def test_compose_returns_a_square_png_and_wraps_the_original_text(tmp_path, monkeypatch) -> None:
    template_path = tmp_path / "template.png"
    _make_template(template_path)
    monkeypatch.setattr(image_module.ImageFont, "truetype", lambda *args, **kwargs: ImageFont.load_default())
    composer = TemplateImageComposer(template_path=template_path, font_path=tmp_path / "font.ttf")

    result = composer.compose("first line\nsecond line")

    with Image.open(BytesIO(result)) as image:
        assert image.format == "PNG"
        assert image.size == (1024, 1024)


def test_compose_fails_clearly_when_the_template_is_missing(tmp_path) -> None:
    composer = TemplateImageComposer(
        template_path=tmp_path / "missing.png",
        font_path=tmp_path / "font.ttf",
    )

    with pytest.raises(ImageCompositionError, match="template"):
        composer.compose("poem")


def test_compose_fails_clearly_when_the_font_is_missing(tmp_path) -> None:
    template_path = tmp_path / "template.png"
    _make_template(template_path)
    composer = TemplateImageComposer(
        template_path=template_path,
        font_path=tmp_path / "missing.ttf",
    )

    with pytest.raises(ImageCompositionError, match="font"):
        composer.compose("poem")
