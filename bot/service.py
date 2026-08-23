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
        if not classification.is_target or not self._has_valid_extraction(text, classification):
            return None

        review = await self._ai.review(text, classification)
        image_bytes = await asyncio.to_thread(
            self._composer.compose, classification.extracted_text
        )
        return AnalysisResult(
            classification=classification,
            review=review,
            image_bytes=image_bytes,
        )

    @staticmethod
    def _has_valid_extraction(text: str, classification: Classification) -> bool:
        source_text = classification.source_text
        extracted_text = classification.extracted_text
        if not source_text or not extracted_text or source_text not in text:
            return False
        segments = extracted_text.split(" ")
        if len(segments) != 3 or any(not segment for segment in segments):
            return False
        source_compact = "".join(source_text.split())
        extracted_compact = "".join(extracted_text.split())
        return source_compact == extracted_compact
