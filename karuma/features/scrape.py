"""Member scraping via invite and message history."""

import asyncio
import logging

import discord

from karuma.config import AppConfig
from karuma.utils import prompt

log = logging.getLogger(__name__)


async def _ensure_guild(client: discord.Client, invite_link: str) -> discord.Guild | None:
    invite = await client.fetch_invite(invite_link)
    guild = invite.guild
    if guild is None:
        log.error("Invalid invite — no guild attached")
        return None

    joined = client.get_guild(guild.id)
    if joined is None:
        log.info("Joining server %s...", guild.name)
        await client.accept_invite(invite_link)
        await asyncio.sleep(3)
        joined = client.get_guild(guild.id)

    if joined is None:
        log.error("Failed to join or resolve guild after invite")
    return joined


async def scrape_members(client: discord.Client, config: AppConfig, invite_link: str | None = None) -> None:
    invite_link = invite_link or await prompt("Enter server invite link: ")
    try:
        joined_guild = await _ensure_guild(client, invite_link)
        if joined_guild is None:
            return

        log.info("Fetching members for %s...", joined_guild.name)
        members = await joined_guild.fetch_members()
        member_ids = {str(m.id) for m in members if not m.bot and m.id != client.user.id}
        if not member_ids:
            log.error("No members returned from fetch_members")
            return

        with config.members_path.open("a", encoding="utf-8") as fh:
            for uid in member_ids:
                fh.write(uid + "\n")

        log.info("Scraped %s members → %s", len(member_ids), config.members_path)
    except discord.Forbidden:
        log.error("Permission denied — invalid invite or banned")
    except discord.HTTPException as exc:
        log.error("Scrape failed: %s", exc)


async def deep_scrape_members(client: discord.Client, config: AppConfig, invite_link: str | None = None) -> None:
    invite_link = invite_link or await prompt("Enter server invite link: ")
    try:
        joined_guild = await _ensure_guild(client, invite_link)
        if joined_guild is None:
            return

        limit_raw = await prompt("Messages per channel (default 1000): ")
        try:
            limit = int(limit_raw) if limit_raw.strip() else 1000
        except ValueError:
            limit = 1000

        log.info("Deep scraping %s (%s msg/channel)...", joined_guild.name, limit)
        member_ids: set[str] = set()
        channels = [
            c for c in joined_guild.text_channels if c.permissions_for(joined_guild.me).read_message_history
        ]

        for idx, channel in enumerate(channels, 1):
            try:
                count = 0
                async for message in channel.history(limit=limit):
                    if not message.author.bot and message.author.id != client.user.id:
                        member_ids.add(str(message.author.id))
                    count += 1
                log.info("[%s/%s] #%s — %s messages, %s unique users", idx, len(channels), channel.name, count, len(member_ids))
            except discord.Forbidden:
                log.warning("[%s/%s] #%s — missing access", idx, len(channels), channel.name)
            except discord.HTTPException as exc:
                log.error("[%s/%s] #%s — %s", idx, len(channels), channel.name, exc)
            await asyncio.sleep(0.5)

        if not member_ids:
            log.error("Deep scrape found no users")
            return

        with config.members_path.open("a", encoding="utf-8") as fh:
            for uid in member_ids:
                fh.write(uid + "\n")

        log.info("Deep scraped %s users → %s", len(member_ids), config.members_path)
    except discord.Forbidden:
        log.error("Permission denied — invalid invite or banned")
    except discord.HTTPException as exc:
        log.error("Deep scrape failed: %s", exc)
