"""Deterministic Pillow composition over a fixed Japanese-style template."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


class ImageCompositionError(RuntimeError):
    """Raised when the template or Japanese font cannot be used."""


DEFAULT_FONT_CANDIDATES = (
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSerifCJK-Regular.ttc",
)


class TemplateImageComposer:
    """Load one fixed template and draw the original poem text onto it."""

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

    @staticmethod
    def _wrap_lines(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
        wrapped: list[str] = []
        for source_line in text.splitlines() or [text]:
            if not source_line:
                wrapped.append("")
                continue
            current = ""
            for character in source_line:
                candidate = current + character
                if current and draw.textlength(candidate, font=font) > max_width:
                    wrapped.append(current)
                    current = character
                else:
                    current = candidate
            wrapped.append(current)
        return wrapped

    def compose(self, text: str) -> bytes:
        if not self._template_path.exists():
            raise ImageCompositionError(f"template file not found: {self._template_path}")

        try:
            with Image.open(self._template_path) as source:
                canvas = ImageOps.fit(source.convert("RGBA"), self._output_size, method=Image.Resampling.LANCZOS)
        except ImageCompositionError:
            raise
        except Exception as exc:
            raise ImageCompositionError("template image could not be opened") from exc

        draw = ImageDraw.Draw(canvas, "RGBA")
        font_size = 96
        font = self._load_font(font_size)
        max_width = int(canvas.width * 0.72)
        lines = self._wrap_lines(draw, text, font, max_width)
        while len(lines) > 8 and font_size > 36:
            font_size -= 4
            font = self._load_font(font_size)
            lines = self._wrap_lines(draw, text, font, max_width)

        line_spacing = int(font_size * 0.45)
        bboxes = [draw.textbbox((0, 0), line or " ", font=font) for line in lines]
        text_width = max((bbox[2] - bbox[0] for bbox in bboxes), default=0)
        text_height = sum(bbox[3] - bbox[1] for bbox in bboxes) + line_spacing * max(len(lines) - 1, 0)
        left = (canvas.width - text_width) // 2
        top = (canvas.height - text_height) // 2

        padding = 42
        draw.rounded_rectangle(
            (
                left - padding,
                top - padding,
                left + text_width + padding,
                top + text_height + padding,
            ),
            radius=24,
            fill=(255, 251, 236, 105),
        )

        cursor_y = top
        for line, bbox in zip(lines, bboxes):
            line_width = bbox[2] - bbox[0]
            cursor_x = (canvas.width - line_width) // 2
            draw.text((cursor_x + 3, cursor_y + 3), line, font=font, fill=(255, 250, 240, 150))
            draw.text((cursor_x, cursor_y), line, font=font, fill=(48, 38, 31, 255))
            cursor_y += bbox[3] - bbox[1] + line_spacing

        # A small abstract seal is deterministic and contains no generated text.
        seal_size = 42
        seal_x = canvas.width - 150
        seal_y = canvas.height - 180
        draw.rounded_rectangle(
            (seal_x, seal_y, seal_x + seal_size, seal_y + seal_size),
            radius=5,
            outline=(130, 42, 37, 220),
            width=5,
        )

        output = BytesIO()
        canvas.save(output, format="PNG", optimize=True)
        return output.getvalue()
