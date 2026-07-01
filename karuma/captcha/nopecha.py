"""Nopecha token API integration."""

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


async def solve_captcha_nopecha(
    client: "KarumaBot",
    exception: discord.CaptchaRequired,
    config: "AppConfig",
) -> str:
    if not config.captcha_api_key:
        raise RuntimeError("No captcha_api_key set in config")

    log.info("Submitting captcha to Nopecha for %s", client.user)
    async with aiohttp.ClientSession() as session:
        payload: dict = {
            "key": config.captcha_api_key,
            "type": "hcaptcha" if exception.service.lower() == "hcaptcha" else exception.service.lower(),
            "sitekey": exception.sitekey,
            "url": "https://discord.com/channels/@me",
        }

        user_agent = getattr(client.http, "user_agent", None)
        if user_agent:
            payload["useragent"] = user_agent
            payload["userAgent"] = user_agent

        rqdata = getattr(exception, "rqdata", None)
        if rqdata:
            payload["data"] = {"rqdata": rqdata}

        bot_proxy = getattr(client.http, "proxy", None)
        if bot_proxy and isinstance(bot_proxy, str):
            parsed = urlparse(bot_proxy)
            scheme = parsed.scheme.lower() if parsed.scheme in {"http", "https", "socks4", "socks5"} else "http"
            proxy_obj = {
                "scheme": scheme,
                "address": parsed.hostname or "",
                "port": int(parsed.port) if parsed.port else (80 if scheme in {"http", "https"} else 1080),
            }
            if parsed.username:
                proxy_obj["username"] = parsed.username
            if parsed.password:
                proxy_obj["password"] = parsed.password
            payload["proxy"] = proxy_obj
        else:
            log.warning("No proxy on client — Nopecha solutions may fail IP checks")

        async with session.post("https://api.nopecha.com/token/", json=payload) as resp:
            try:
                res = await resp.json()
            except Exception as exc:
                raw = await resp.text()
                raise RuntimeError(f"Nopecha invalid JSON: {raw[:200]}") from exc
            if "error" in res:
                raise RuntimeError(f"Nopecha error: {res.get('error')}")
            job_id = res.get("data")
            if not job_id:
                raise RuntimeError(f"Nopecha missing job ID: {res}")

        log.info("Nopecha task %s queued", job_id)
        for i in range(60):
            await asyncio.sleep(2)
            poll_url = f"https://api.nopecha.com/token/?key={config.captcha_api_key}&id={job_id}"
            async with session.get(poll_url) as resp:
                try:
                    result = await resp.json()
                except Exception:
                    continue

                if "data" in result:
                    return result["data"]
                if result.get("code") == 14:
                    if i % 5 == 0:
                        log.debug("Nopecha still solving (%ss)", i * 2)
                    continue
                raise RuntimeError(f"Nopecha error: {result.get('message', result)}")

    raise RuntimeError("Nopecha timed out after 120 seconds")
