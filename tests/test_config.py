import pytest

from bot.config import ConfigurationError, Settings


def test_settings_load_required_values_and_defaults() -> None:
    settings = Settings.from_env(
        {
            "DISCORD_TOKEN": "discord-token",
            "OPENAI_API_KEY": "openai-key",
        }
    )

    assert settings.discord_token == "discord-token"
    assert settings.openai_api_key == "openai-key"
    assert settings.classification_model == "gpt-5.6-luna"
    assert settings.review_model == "gpt-5.6-luna"
    assert settings.reasoning_effort == "max"
    assert settings.dedup_ttl_seconds == 900

    blank_template = Settings.from_env(
        {
            "DISCORD_TOKEN": "discord-token",
            "OPENAI_API_KEY": "openai-key",
            "IMAGE_TEMPLATE_PATH": "   ",
        }
    )
    assert blank_template.image_template_path.name == "senryu_template.png"


def test_settings_reject_missing_secrets_and_invalid_numbers() -> None:
    with pytest.raises(ConfigurationError, match="DISCORD_TOKEN"):
        Settings.from_env({"OPENAI_API_KEY": "key"})

def test_non_secret_environment_overrides_are_ignored() -> None:
    settings = Settings.from_env(
        {
            "DISCORD_TOKEN": "discord-token",
            "OPENAI_API_KEY": "openai-key",
            "OPENAI_CLASSIFICATION_MODEL": "gpt-5.6-sol",
            "OPENAI_REVIEW_MODEL": "gpt-5.6-terra",
            "OPENAI_PRICING_JSON": "{}",
            "DEDUP_TTL_SECONDS": "1",
            "DEDUP_MAX_ENTRIES": "1",
            "IMAGE_TEMPLATE_PATH": "/tmp/other.png",
            "FONT_PATH": "/tmp/other.ttf",
        }
    )

    assert settings.classification_model == "gpt-5.6-luna"
    assert settings.review_model == "gpt-5.6-luna"
    assert settings.reasoning_effort == "max"
    assert settings.dedup_ttl_seconds == 900
    assert settings.dedup_max_entries == 10_000
    assert settings.image_template_path.name == "senryu_template.png"
    assert settings.font_path is None
