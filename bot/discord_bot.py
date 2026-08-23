"""Discord gateway client and reply handling."""

from __future__ import annotations

import io
import logging
from typing import Any

import discord

from .dedupe import MessageDeduplicator
from .formatting import chunk_text, format_reply
from .service import PoemAnalysisService

logger = logging.getLogger(__name__)


class SenryuBot(discord.Client):
    """Listen to messages and reply to AI-recognized short poems."""

    def __init__(
        self,
        *,
        service: PoemAnalysisService,
        deduplicator: MessageDeduplicator | None = None,
        intents: discord.Intents | None = None,
    ) -> None:
        if intents is None:
            intents = discord.Intents.default()
            intents.message_content = True
        super().__init__(intents=intents)
        self._service = service
        self._deduplicator = deduplicator or MessageDeduplicator()

    async def on_ready(self) -> None:
        if self.user is not None:
            logger.info("Logged in as %s (%s)", self.user, self.user.id)

    async def on_message(self, message: discord.Message) -> None:
        await self.handle_message(message)

    async def handle_message(self, message: Any) -> None:
        """Handle one message; kept public for deterministic unit testing."""

        if getattr(getattr(message, "author", None), "bot", False):
            return
        text = getattr(message, "content", "") or ""
        if not text.strip():
            return
        if not self._deduplicator.check_and_mark(message.id):
            return

        try:
            result = await self._service.analyze(text)
            if result is None:
                return

            body = format_reply(result.classification, text, result.review)
            chunks = chunk_text(body, limit=2_000)
            image_file = discord.File(
                io.BytesIO(result.image_bytes),
                filename=f"senryu-{message.id}.png",
            )
            await message.reply(content=chunks[0], file=image_file, mention_author=False)
            for chunk in chunks[1:]:
                await message.channel.send(chunk)
        except Exception:
            logger.exception("Failed to process Discord message %s", message.id)
