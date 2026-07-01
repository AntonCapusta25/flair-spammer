"""Tests for karuma.captcha.twocaptcha helpers."""

from unittest.mock import MagicMock

from karuma.captcha.twocaptcha import _apply_proxy_payload


def test_apply_proxy_payload_sets_fields() -> None:
    client = MagicMock()
    client.http.proxy = "http://user:pass@1.2.3.4:8080"
    payload: dict = {}

    _apply_proxy_payload(payload, client)

    assert payload["proxyType"] == "HTTP"
    assert payload["proxytype"] == "HTTP"
    assert payload["proxy"] == "user:pass@1.2.3.4:8080"


def test_apply_proxy_payload_no_proxy() -> None:
    client = MagicMock()
    client.http.proxy = None
    payload: dict = {}

    _apply_proxy_payload(payload, client)

    assert "proxy" not in payload
