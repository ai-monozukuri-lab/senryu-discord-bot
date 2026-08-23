"""Production entry point for Railway's long-running process."""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

from .ai import OpenAIAnalyzer
from .config import Settings
from .dedupe import MessageDeduplicator
from .discord_bot import SenryuBot
from .image import TemplateImageComposer
from .service import PoemAnalysisService


def create_bot(settings: Settings) -> SenryuBot:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    analyzer = OpenAIAnalyzer(
        client=client,
        classification_model=settings.classification_model,
        review_model=settings.review_model,
    )
    composer = TemplateImageComposer(
        template_path=settings.image_template_path,
        font_path=settings.font_path,
    )
    service = PoemAnalysisService(ai=analyzer, composer=composer)
    deduplicator = MessageDeduplicator(
        ttl_seconds=settings.dedup_ttl_seconds,
        max_entries=settings.dedup_max_entries,
    )
    return SenryuBot(service=service, deduplicator=deduplicator)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = Settings.from_env()
    create_bot(settings).run(settings.discord_token)


if __name__ == "__main__":
    main()
