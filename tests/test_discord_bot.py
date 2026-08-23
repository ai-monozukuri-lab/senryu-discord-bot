from types import SimpleNamespace

import pytest

from bot.discord_bot import SenryuBot
from bot.models import AnalysisResult, Classification, Review


class FakeService:
    def __init__(self, result) -> None:
        self.result = result
        self.calls: list[str] = []

    async def analyze(self, text: str):
        self.calls.append(text)
        return self.result


class FakeMessage:
    def __init__(self, message_id: int, content: str, *, is_bot: bool = False) -> None:
        self.id = message_id
        self.content = content
        self.author = SimpleNamespace(bot=is_bot)
        self.replies: list[dict] = []

    async def reply(self, **kwargs) -> None:
        self.replies.append(kwargs)


def _result() -> AnalysisResult:
    return AnalysisResult(
        classification=Classification(
            is_poem=True,
            type="haiku",
            confidence=0.9,
            source_text="句",
            extracted_text="句",
            normalized_lines=["句"],
        ),
        review=Review(
            comment="講評です。",
            ratings={
                "情景": 4,
                "余韻": 5,
                "独創性": 4,
            },
            overall=4,
        ),
        image_bytes=b"png",
    )


@pytest.mark.asyncio
async def test_bot_ignores_its_own_messages_and_empty_messages() -> None:
    service = FakeService(_result())
    bot = SenryuBot(service=service)

    own = FakeMessage(1, "句", is_bot=True)
    empty = FakeMessage(2, "   ")
    await bot.handle_message(own)
    await bot.handle_message(empty)

    assert service.calls == []
    assert own.replies == []
    assert empty.replies == []


@pytest.mark.asyncio
async def test_bot_replies_once_for_a_target_and_suppresses_duplicates() -> None:
    service = FakeService(_result())
    bot = SenryuBot(service=service)
    message = FakeMessage(10, "春の句")

    await bot.handle_message(message)
    await bot.handle_message(message)

    assert service.calls == ["春の句"]
    assert len(message.replies) == 1
    assert message.replies[0]["content"].splitlines()[0] == "俳句を検出しました！"
    assert message.replies[0]["content"].splitlines()[1].startswith("総合評価:")
    assert "\n評価\n" not in message.replies[0]["content"]
    assert "\n講評\n" not in message.replies[0]["content"]
    assert "作品種別" not in message.replies[0]["content"]
    assert "作品:" not in message.replies[0]["content"]
    assert "講評です。" in message.replies[0]["content"]
    assert message.replies[0]["file"].filename == "senryu-10.png"
