"""Captcha solver dispatch."""

import logging
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from karuma.bot import KarumaBot
    from karuma.config import AppConfig

log = logging.getLogger(__name__)


async def solve_captcha(
    client: "KarumaBot",
    exception: discord.CaptchaRequired,
    config: "AppConfig",
) -> str:
    """Route captcha solving to the configured backend."""
    service = (config.captcha_service or "manual").lower()
    log.warning("Captcha required for %s via %s", client.user, exception.service)

    if service == "manual":
        from karuma.captcha.manual import manual_captcha_server

        return await manual_captcha_server.solve(exception, str(client.user))
    if service == "nopecha":
        from karuma.captcha.nopecha import solve_captcha_nopecha

        return await solve_captcha_nopecha(client, exception, config)
    from karuma.captcha.twocaptcha import solve_captcha_2captcha

    return await solve_captcha_2captcha(client, exception, config)
