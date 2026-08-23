"""Create the deterministic Japanese-style background template."""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 1024
OUTPUT = Path(__file__).resolve().parent.parent / "assets" / "senryu_template.png"


def create_template() -> None:
    rng = random.Random(20260823)
    image = Image.new("RGB", (SIZE, SIZE), (241, 232, 210))
    draw = ImageDraw.Draw(image)

    # Layered wood frame with a quiet, low-contrast finish.
    for inset in range(0, 82, 4):
        ratio = inset / 82
        color = (
            int(84 + 38 * ratio),
            int(52 + 27 * ratio),
            int(31 + 20 * ratio),
            255,
        )
        draw.rectangle((inset, inset, SIZE - inset - 1, SIZE - inset - 1), outline=color, width=4)

    draw.rectangle((79, 79, 944, 944), fill=(201, 181, 148), outline=(104, 72, 48), width=4)
    draw.rectangle((105, 105, 918, 918), fill=(241, 232, 210), outline=(157, 129, 92), width=3)

    # A pale ink-wash landscape kept outside the text-safe center.
    draw.ellipse((115, 650, 540, 970), fill=(209, 218, 207))
    draw.ellipse((560, 700, 920, 970), fill=(207, 216, 218))
    draw.polygon([(120, 760), (270, 580), (390, 760), (520, 590), (700, 780)], fill=(188, 197, 188))
    draw.arc((650, 160, 910, 470), 170, 305, fill=(153, 164, 156), width=7)

    # Stable paper-fibre texture; the high-contrast center remains readable.
    for _ in range(16_000):
        x = rng.randint(112, 911)
        y = rng.randint(112, 911)
        dark = rng.randint(0, 4)
        if 185 < x < 840 and 185 < y < 840:
            dark = min(dark, 2)
        if rng.random() < 0.55:
            draw.point((x, y), fill=(241 - dark * 3, 232 - dark * 3, 210 - dark * 3))
        else:
            draw.line((x, y, x + rng.randint(1, 4), y), fill=(246, 239, 223), width=1)

    # An abstract red seal, deliberately without generated or embedded text.
    seal_x, seal_y = 815, 815
    draw.rounded_rectangle(
        (seal_x, seal_y, seal_x + 48, seal_y + 48),
        radius=5,
        fill=(169, 69, 59),
        outline=(139, 55, 48),
        width=3,
    )
    draw.rectangle(
        (seal_x + 12, seal_y + 12, seal_x + 36, seal_y + 36),
        outline=(228, 158, 139),
        width=3,
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, format="PNG", optimize=True)


if __name__ == "__main__":
    create_template()
