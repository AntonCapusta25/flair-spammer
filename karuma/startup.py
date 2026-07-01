"""Client startup and connection orchestration."""

import asyncio
import logging
from dataclasses import dataclass

import discord

from karuma.bot import KarumaBot
from karuma.captcha.manual import manual_captcha_server
from karuma.config import AppConfig
from karuma.ui.boot import show_boot_animation, show_disclaimer
from karuma.utils import clear_console, wait_for_ready

log = logging.getLogger(__name__)


@dataclass
class RuntimeContext:
    config: AppConfig
    clients: list[KarumaBot]


async def prepare_captcha(config: AppConfig) -> None:
    if config.captcha_service != "manual":
        log.info("Captcha service: %s", config.captcha_service)
        return
    await manual_captcha_server.start()
    manual_captcha_server.print_instructions()


async def connect_clients(config: AppConfig) -> list[KarumaBot]:
    tokens = config.load_tokens()
    if not tokens:
        raise RuntimeError(f"No tokens in {config.tokens_path} or config")

    proxies = config.load_proxies()
    pairs: list[tuple[KarumaBot, str]] = []

    for index, token in enumerate(tokens):
        proxy = proxies[index % len(proxies)] if proxies else None
        client = KarumaBot(config=config, proxy=proxy)
        pairs.append((client, token))

    log.info("Starting %s client(s) (%s proxies loaded)", len(pairs), len(proxies))

    async def _start(client: KarumaBot, token: str) -> None:
        try:
            await client.start(token)
        except discord.LoginFailure:
            log.error("Invalid token: %s...", token[:10])
        except Exception as exc:
            log.exception("Client start failed (%s...): %s", token[:10], exc)

    for client, token in pairs:
        asyncio.create_task(_start(client, token))

    log.info("Waiting up to %ss for connections...", config.connect_timeout)
    ready = await wait_for_ready([c for c, _ in pairs], config.connect_timeout)
    if not ready:
        raise RuntimeError("No clients connected — check tokens and proxies")

    log.info("Connected %s / %s account(s)", len(ready), len(pairs))
    return ready


async def bootstrap(config: AppConfig) -> RuntimeContext:
    """Run disclaimer, captcha setup, and client connections."""
    await show_disclaimer(config)
    await show_boot_animation(config)
    await prepare_captcha(config)
    clients = await connect_clients(config)
    await clear_console()
    return RuntimeContext(config=config, clients=clients)
