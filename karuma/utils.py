"""Shared helpers for delays, console I/O, and guild access."""

import asyncio
import logging
import os
import random

import discord

log = logging.getLogger(__name__)


def random_cooldown(minimum: float, maximum: float) -> float:
    """Return a random delay between two bounds."""
    return random.uniform(minimum, maximum)


async def clear_console() -> None:
    os.system("cls" if os.name == "nt" else "clear")


async def prompt(text: str) -> str:
    """Non-blocking-friendly input wrapper (runs in executor if needed)."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: input(text))


async def prompt_int(text: str) -> int:
    while True:
        value = await prompt(text)
        try:
            return int(value)
        except ValueError:
            log.error("Invalid number — try again")


async def wait_for_ready(clients: list[discord.Client], timeout: float) -> list[discord.Client]:
    """Wait until each client is ready or timeout expires."""
    pending = {id(c): c for c in clients}
    deadline = asyncio.get_running_loop().time() + timeout

    while pending and asyncio.get_running_loop().time() < deadline:
        ready = [c for c in pending.values() if c.is_ready()]
        for client in ready:
            pending.pop(id(client), None)
        if pending:
            await asyncio.sleep(0.25)

    return [c for c in clients if c.is_ready()]


async def resolve_guild(client: discord.Client, guild_id: int) -> discord.Guild | None:
    """Find a guild on the client by ID."""
    return discord.utils.get(client.guilds, id=guild_id)


async def resolve_bot_member(guild: discord.Guild, client: discord.Client) -> discord.Member | None:
    """Return the client's guild member, fetching if needed."""
    member = guild.get_member(client.user.id)
    if member is not None:
        return member
    try:
        return await guild.fetch_member(client.user.id)
    except discord.HTTPException as exc:
        log.warning("Could not resolve member for %s in %s: %s", client.user, guild.name, exc)
        return None


async def fetch_member_ids(guild: discord.Guild, client: discord.Client) -> list[int]:
    """Fetch all non-bot member IDs, falling back to cache."""
    try:
        members = await guild.fetch_members()
        return [m.id for m in members if not m.bot and m.id != client.user.id]
    except Exception as exc:
        log.warning("fetch_members failed for %s, using cache: %s", guild.name, exc)
        return [m.id for m in guild.members if not m.bot and m.id != client.user.id]
