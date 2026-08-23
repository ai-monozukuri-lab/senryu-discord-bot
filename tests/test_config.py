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
    assert settings.classification_model == "gpt-5.6"
    assert settings.review_model == "gpt-5.6"
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

    with pytest.raises(ConfigurationError, match="DEDUP_TTL_SECONDS"):
        Settings.from_env(
            {
                "DISCORD_TOKEN": "token",
                "OPENAI_API_KEY": "key",
                "DEDUP_TTL_SECONDS": "0",
            }
        )
