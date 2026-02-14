import os

from app.config import _env_bool, get_settings


def test_env_bool_variants(monkeypatch):
    monkeypatch.setenv("X_BOOL", " Yes ")
    assert _env_bool("X_BOOL", "0") is True


def test_telegram_enabled_fallback(monkeypatch):
    monkeypatch.delenv("TELEGRAM_ENABLED", raising=False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    settings = get_settings()
    assert settings.telegram_enabled is True
    assert settings.telegram_enabled_raw_present is False
