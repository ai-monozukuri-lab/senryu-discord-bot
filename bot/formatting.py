"""Discord-safe formatting for a poem appreciation reply."""

from __future__ import annotations

from .models import Classification, Review


def format_stars(score: int) -> str:
    """Render a validated five-point score as stars."""

    if not 1 <= score <= 5:
        raise ValueError("score must be between 1 and 5")
    return "★" * score + "☆" * (5 - score)


def format_reply(_classification: Classification, _original_text: str, review: Review) -> str:
    """Build a review-only reply; the poem is shown in the attached image."""

    stars = review.ratings.as_stars()
    rating_lines = "\n".join(f"{label}: {value}" for label, value in stars.items())
    return (
        f"講評:\n{review.comment}\n\n"
        f"評価:\n{rating_lines}\n"
        f"総合評価: {format_stars(review.overall)}"
    )


def chunk_text(text: str, *, limit: int = 2_000) -> list[str]:
    """Split a message at line boundaries without dropping any characters."""

    if limit <= 0:
        raise ValueError("limit must be positive")
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    remaining = text
    while len(remaining) > limit:
        split_at = remaining.rfind("\n", 0, limit + 1)
        if split_at <= 0:
            split_at = limit
        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:]
        if remaining.startswith("\n"):
            remaining = remaining[1:]
    if remaining:
        chunks.append(remaining)
    return chunks
