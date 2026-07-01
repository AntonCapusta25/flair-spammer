"""Tests for karuma.config."""

from pathlib import Path

import pytest

from karuma.config import AppConfig


def test_load_from_json(sample_config_json: Path) -> None:
    cfg = AppConfig.load(sample_config_json)
    assert cfg.minimum_dm == 2.0
    assert cfg.maximum_dm == 4.0
    assert cfg.skip_disclaimer is True
    assert cfg.skip_booting is False
    assert cfg.captcha_service == "manual"


def test_load_missing_file_uses_defaults(tmp_path: Path) -> None:
    cfg = AppConfig.load(tmp_path / "missing.json")
    assert cfg.minimum_dm == 1.0
    assert cfg.captcha_service == "manual"


def test_load_invalid_json_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Failed to load config"):
        AppConfig.load(bad)


def test_placeholder_captcha_key_falls_back_to_manual(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        '{"captcha_api_key": "Your Captcha API Key Here", "captcha_service": "2captcha"}',
        encoding="utf-8",
    )
    cfg = AppConfig.load(path)
    assert cfg.captcha_api_key == ""
    assert cfg.captcha_service == "manual"


def test_load_tokens_from_file(tmp_path: Path) -> None:
    tokens_path = tmp_path / "tokens.txt"
    tokens_path.write_text("# comment\nTOKEN_A\n\nTOKEN_B\n", encoding="utf-8")
    cfg = AppConfig.load(tmp_path / "x.json")
    cfg.tokens_path = tokens_path
    assert cfg.load_tokens() == ["TOKEN_A", "TOKEN_B"]


def test_load_tokens_fallback_to_config(tmp_path: Path) -> None:
    cfg = AppConfig.load(tmp_path / "x.json")
    cfg.tokens_path = tmp_path / "missing.txt"
    cfg.token = "fallback_token"
    assert cfg.load_tokens() == ["fallback_token"]


def test_load_tokens_ignores_placeholder_config_token(tmp_path: Path) -> None:
    cfg = AppConfig.load(tmp_path / "x.json")
    cfg.tokens_path = tmp_path / "missing.txt"
    cfg.token = "Your Token Here"
    assert cfg.load_tokens() == []


def test_load_proxies_normalizes_scheme(tmp_path: Path) -> None:
    proxies_path = tmp_path / "proxies.txt"
    proxies_path.write_text(
        "# comment\n1.2.3.4:8080\nhttp://user:pass@5.6.7.8:3128\n",
        encoding="utf-8",
    )
    cfg = AppConfig.load(tmp_path / "x.json")
    cfg.proxies_path = proxies_path
    assert cfg.load_proxies() == [
        "http://1.2.3.4:8080",
        "http://user:pass@5.6.7.8:3128",
    ]


def test_cli_overrides_applied(sample_config_json: Path) -> None:
    cfg = AppConfig.load(sample_config_json, connect_timeout=30.0, skip_booting=True)
    assert cfg.connect_timeout == 30.0
    assert cfg.skip_booting is True
