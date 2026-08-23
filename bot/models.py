"""Typed contracts shared by the AI, image, and Discord layers."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PoemType(StrEnum):
    """Classification labels returned by the first AI call."""

    HAIKU = "haiku"
    SENRYU = "senryu"
    OTHER = "other"


class Classification(BaseModel):
    """Structured result for deciding whether a message is a target poem."""

    model_config = ConfigDict(extra="forbid")

    is_poem: bool
    type: PoemType
    confidence: float = Field(ge=0.0, le=1.0)
    normalized_lines: list[str] = Field(min_length=1)

    @field_validator("normalized_lines")
    @classmethod
    def lines_must_contain_text(cls, lines: list[str]) -> list[str]:
        if any(not line.strip() for line in lines):
            raise ValueError("normalized_lines must not contain blank lines")
        return lines

    @property
    def is_target(self) -> bool:
        """Return whether the classification should trigger a reply."""

        return self.is_poem and self.type in {PoemType.HAIKU, PoemType.SENRYU}


def _stars(score: int) -> str:
    if not 1 <= score <= 5:
        raise ValueError("score must be between 1 and 5")
    return "★" * score + "☆" * (5 - score)


class Ratings(BaseModel):
    """The three public rating dimensions, preserving their Japanese JSON keys."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    scene: int = Field(alias="情景", ge=1, le=5)
    aftertaste: int = Field(alias="余韻", ge=1, le=5)
    originality: int = Field(alias="独創性", ge=1, le=5)

    def as_stars(self) -> dict[str, str]:
        """Return the public Japanese labels mapped to five-slot star strings."""

        return {
            "情景": _stars(self.scene),
            "余韻": _stars(self.aftertaste),
            "独創性": _stars(self.originality),
        }


class Review(BaseModel):
    """Structured result for the second AI call."""

    model_config = ConfigDict(extra="forbid")

    comment: str = Field(min_length=1)
    ratings: Ratings
    overall: int = Field(ge=1, le=5)

    @field_validator("comment")
    @classmethod
    def comment_must_contain_text(cls, comment: str) -> str:
        if not comment.strip():
            raise ValueError("comment must contain text")
        return comment


class AnalysisResult(BaseModel):
    """All data required to render and post one target message."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    classification: Classification
    review: Review
    image_bytes: bytes
