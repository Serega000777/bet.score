from pathlib import Path

from pytest import MonkeyPatch

from bet_score.config import Settings
from bet_score.infrastructure.migrations import migrations_path


def test_cors_origins_accept_comma_separated_environment_value(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "API_CORS_ORIGINS",
        "https://app.example.com,https://telegram.example.com",
    )

    settings = Settings()

    assert settings.api_cors_origins == (
        "https://app.example.com",
        "https://telegram.example.com",
    )


def test_migrations_are_found_from_backend_directory(monkeypatch: MonkeyPatch) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(repository_root / "backend")

    path = migrations_path()

    assert path.name == "migrations"
    assert (path / "001_foundation.sql").is_file()
