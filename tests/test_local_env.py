import os
from pathlib import Path

import bot.main as main_module


def test_load_local_environment_reads_only_existing_explicit_file(monkeypatch, tmp_path) -> None:
    env_path = tmp_path / ".env.local"
    env_path.write_text("DISCORD_TOKEN=local-token\n", encoding="utf-8")
    calls: list[dict] = []

    monkeypatch.setattr(
        main_module,
        "load_dotenv",
        lambda **kwargs: calls.append(kwargs),
    )

    main_module.load_local_environment(env_path)

    assert calls == [{"dotenv_path": env_path, "override": False}]


def test_load_local_environment_does_not_load_a_missing_file(monkeypatch, tmp_path) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(
        main_module,
        "load_dotenv",
        lambda **kwargs: calls.append(kwargs),
    )

    main_module.load_local_environment(Path(tmp_path / ".env.local"))

    assert calls == []


def test_load_local_environment_does_not_override_existing_shell_values(
    monkeypatch, tmp_path
) -> None:
    env_path = tmp_path / ".env.local"
    env_path.write_text("LOCAL_ENV_TEST=from-file\n", encoding="utf-8")
    monkeypatch.setenv("LOCAL_ENV_TEST", "from-shell")

    main_module.load_local_environment(env_path)

    assert os.environ["LOCAL_ENV_TEST"] == "from-shell"
