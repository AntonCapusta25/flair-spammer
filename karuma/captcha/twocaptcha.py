"""2Captcha integration."""

import asyncio
import logging
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import aiohttp
import discord

if TYPE_CHECKING:
    from karuma.bot import KarumaBot
    from karuma.config import AppConfig

log = logging.getLogger(__name__)


def _apply_proxy_payload(payload: dict, client: "KarumaBot") -> None:
    bot_proxy = getattr(client.http, "proxy", None)
    if not bot_proxy or not isinstance(bot_proxy, str):
        log.warning(
            "No proxy on client — hCaptcha Enterprise may reject 2Captcha solutions (IP mismatch)"
        )
        return

    parsed = urlparse(bot_proxy)
    ptype = parsed.scheme if parsed.scheme in {"http", "https", "socks4", "socks5"} else "http"
    payload["proxyType"] = ptype.upper()
    payload["proxytype"] = ptype.upper()

    proxy_str = ""
    if parsed.username and parsed.password:
        proxy_str += f"{parsed.username}:{parsed.password}@"
    if parsed.hostname:
        proxy_str += parsed.hostname
    if parsed.port:
        proxy_str += f":{parsed.port}"
    payload["proxy"] = proxy_str
    log.info("2Captcha proxy: %s (%s)", proxy_str, ptype.upper())


async def solve_captcha_2captcha(
    client: "KarumaBot",
    exception: discord.CaptchaRequired,
    config: "AppConfig",
) -> str:
    if not config.captcha_api_key:
        raise RuntimeError("No captcha_api_key set in config")

    method = exception.service.lower()
    if "hcaptcha" in method:
        method = "hcaptcha"
    elif "recaptcha" in method:
        method = "userrecaptcha"
    else:
        raise RuntimeError(f"Unsupported captcha service: {exception.service}")

    log.info("Submitting captcha to 2Captcha for %s", client.user)
    async with aiohttp.ClientSession() as session:
        payload: dict = {
            "key": config.captcha_api_key,
            "method": method,
            "pageurl": "https://discord.com/channels/@me",
            "json": 1,
        }
        if method == "hcaptcha":
            payload["sitekey"] = exception.sitekey
        else:
            payload["googlekey"] = exception.sitekey

        try:
            payload["useragent"] = client.http.user_agent
            payload["userAgent"] = client.http.user_agent
        except AttributeError:
            pass

        rqdata = getattr(exception, "rqdata", None)
        if rqdata:
            payload["data"] = rqdata
            payload["enterprise"] = 1

        payload["invisible"] = 1 if getattr(exception, "should_serve_invisible", False) else 0
        _apply_proxy_payload(payload, client)

        async with session.post("https://2captcha.com/in.php", data=payload) as resp:
            try:
                res = await resp.json(content_type=None)
            except Exception as exc:
                raw = await resp.text()
                raise RuntimeError(f"2Captcha invalid JSON: {raw[:200]}") from exc
            if res.get("status") != 1:
                raise RuntimeError(f"2Captcha error: {res.get('request')}")
            req_id = res["request"]

        log.info("2Captcha task %s queued", req_id)
        for i in range(60):
            await asyncio.sleep(5)
            params = {"key": config.captcha_api_key, "action": "get", "id": req_id, "json": 1}
            async with session.get("https://2captcha.com/res.php", params=params) as resp:
                try:
                    result = await resp.json(content_type=None)
                except Exception:
                    raw = await resp.text()
                    if "CAPCHA_NOT_READY" in raw:
                        if i % 3 == 0:
                            log.debug("2Captcha still solving (%ss)", i * 5)
                        continue
                    if "OK|" in raw:
                        return raw.split("|", 1)[1]
                    log.warning("2Captcha non-JSON response: %s", raw[:100])
                    continue

                if result.get("status") == 1:
                    return result["request"]
                if result.get("request") != "CAPCHA_NOT_READY":
                    raise RuntimeError(f"2Captcha solve error: {result.get('request')}")
                if i % 3 == 0:
                    log.debug("2Captcha still solving (%ss)", i * 5)

    raise RuntimeError("2Captcha timed out after 300 seconds")
