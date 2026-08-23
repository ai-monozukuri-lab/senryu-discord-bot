"""Application service enforcing the one-or-two-call processing flow."""

from __future__ import annotations

import asyncio
from typing import Protocol

from .models import AnalysisResult, Classification, Review


class PoemAI(Protocol):
    async def classify(self, text: str) -> Classification:
        """Classify one message."""

    async def review(self, text: str, classification: Classification) -> Review:
        """Review a target poem."""


class ImageComposer(Protocol):
    def compose(self, text: str) -> bytes:
        """Return a PNG containing the original text over the template."""


class PoemAnalysisService:
    """Coordinate AI calls and local composition for one Discord message."""

    def __init__(self, *, ai: PoemAI, composer: ImageComposer) -> None:
        self._ai = ai
        self._composer = composer

    async def analyze(self, text: str) -> AnalysisResult | None:
        classification = await self._ai.classify(text)
        if not classification.is_target:
            return None

        review = await self._ai.review(text, classification)
        image_bytes = await asyncio.to_thread(self._composer.compose, text)
        return AnalysisResult(
            classification=classification,
            review=review,
            image_bytes=image_bytes,
        )
