"""Pillow composition over a fixed Japanese-style template."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


class ImageCompositionError(RuntimeError):
    """Raised when the template or Japanese font cannot be used."""


BUNDLED_FONT_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "fonts" / "YujiSyuku-Regular.ttf"
)

DEFAULT_FONT_CANDIDATES = (
    str(BUNDLED_FONT_PATH),
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSerifCJK-Regular.ttc",
)


def split_vertical_columns(text: str, *, max_chars: int) -> list[list[str]]:
    """Split source lines into vertical columns, preserving right-to-left order."""

    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    columns: list[list[str]] = []
    for source_line in text.splitlines() or [text]:
        characters = list(source_line)
        if not characters:
            columns.append([])
            continue
        for start in range(0, len(characters), max_chars):
            columns.append(characters[start : start + max_chars])
    return columns or [[]]


class TemplateImageComposer:
    """Load one fixed template and draw the original poem text vertically."""

    def __init__(
        self,
        *,
        template_path: str | Path,
        font_path: str | Path | None = None,
        output_size: tuple[int, int] = (1024, 1024),
    ) -> None:
        self._template_path = Path(template_path)
        self._font_path = Path(font_path) if font_path is not None else None
        self._output_size = output_size

    def _resolve_font(self) -> Path:
        if self._font_path is not None:
            if self._font_path.exists():
                return self._font_path
            raise ImageCompositionError(f"font file not found: {self._font_path}")
        for candidate in DEFAULT_FONT_CANDIDATES:
            path = Path(candidate)
            if path.exists():
                return path
        raise ImageCompositionError("Japanese font could not be found")

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        try:
            return ImageFont.truetype(str(self._resolve_font()), size=size)
        except ImageCompositionError:
            raise
        except Exception as exc:
            raise ImageCompositionError("Japanese font could not be loaded") from exc

    def compose(self, text: str) -> bytes:
        if not self._template_path.exists():
            raise ImageCompositionError(f"template file not found: {self._template_path}")

        try:
            with Image.open(self._template_path) as source:
                canvas = ImageOps.fit(
                    source.convert("RGBA"), self._output_size, method=Image.Resampling.LANCZOS
                )
        except ImageCompositionError:
            raise
        except Exception as exc:
            raise ImageCompositionError("template image could not be opened") from exc

        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay, "RGBA")
        draw = ImageDraw.Draw(canvas, "RGBA")
        font_size = 96
        max_width = int(canvas.width * 0.64)
        max_height = int(canvas.height * 0.70)
        column_gap = 18

        while True:
            font = self._load_font(font_size)
            glyph_advance = int(font_size * 1.16)
            max_chars = max(1, max_height // glyph_advance)
            columns = split_vertical_columns(text, max_chars=max_chars)
            column_width = int(font_size * 1.22)
            text_width = len(columns) * column_width - column_gap
            text_height = max(len(column) for column in columns) * glyph_advance
            if (text_width <= max_width and text_height <= max_height) or font_size <= 40:
                break
            font_size -= 4

        left = (canvas.width - text_width) // 2
        top = (canvas.height - text_height) // 2
        padding = 42
        overlay_draw.rounded_rectangle(
            (
                left - padding,
                top - padding,
                left + text_width + padding,
                top + text_height + padding,
            ),
            radius=24,
            fill=(255, 251, 236, 105),
        )
        canvas = Image.alpha_composite(canvas, overlay)
        draw = ImageDraw.Draw(canvas, "RGBA")

        right = left + text_width
        for column_index, column in enumerate(columns):
            column_left = right - (column_index + 1) * column_width
            for character_index, character in enumerate(column):
                bbox = draw.textbbox((0, 0), character or " ", font=font)
                glyph_width = bbox[2] - bbox[0]
                draw_x = column_left + (column_width - glyph_width) // 2 - bbox[0]
                draw_y = top + character_index * glyph_advance - bbox[1]
                draw.text(
                    (draw_x + 3, draw_y + 3),
                    character,
                    font=font,
                    fill=(255, 250, 240, 150),
                )
                draw.text((draw_x, draw_y), character, font=font, fill=(48, 38, 31, 255))

        output = BytesIO()
        canvas.save(output, format="PNG", optimize=True)
        return output.getvalue()
