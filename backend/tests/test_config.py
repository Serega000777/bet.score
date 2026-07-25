from pytest import MonkeyPatch

from bet_score.config import Settings


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
