"""Discord client wrapper with captcha and fingerprint support."""

import base64
import json
import logging

import discord

from karuma.config import AppConfig

log = logging.getLogger(__name__)


class KarumaBot(discord.Client):
    """Self-bot client with captcha dispatch and optional X-Super-Properties."""

    def __init__(self, config: AppConfig, proxy: str | None = None, **kwargs):
        super().__init__(proxy=proxy, **kwargs)
        self.app_config = config

    async def login(self, token: str) -> None:
        await super().login(token)
        props_b64 = self.app_config.x_super_properties
        if not props_b64:
            return

        try:
            decoded = base64.b64decode(props_b64).decode("utf-8")
            props = json.loads(decoded)
            self.http.headers.super_properties.update(props)
            self.http.headers.encoded_super_properties = props_b64
            headers_dict = self.http.headers.__dict__
            headers_dict.pop("user_agent", None)
            headers_dict.pop("client_hints", None)
            if "os" in props:
                self.http.headers.platform = props["os"]
            if "browser_version" in props:
                try:
                    self.http.headers.major_version = int(props["browser_version"].split(".")[0])
                except (ValueError, AttributeError):
                    pass
            log.info("Applied custom X-Super-Properties from config")
        except Exception as exc:
            log.error("Failed to apply X-Super-Properties: %s", exc)

    async def on_ready(self) -> None:
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="github.com/hoemotion",
            ),
            status=discord.Status.idle,
        )
        log.info("Ready: %s", self.user)

    async def handle_captcha(self, exception: discord.CaptchaRequired) -> str:
        from karuma.captcha import solve_captcha

        try:
            return await solve_captcha(self, exception, self.app_config)
        except Exception as exc:
            log.error("Captcha solve failed for %s: %s", self.user, exc)
            raise exception
