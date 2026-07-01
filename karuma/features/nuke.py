"""Server nuke operations."""

import asyncio
import logging

import discord

from karuma.config import AppConfig
from karuma.features.permissions import check_permissions_and_confirm
from karuma.utils import prompt, prompt_int, random_cooldown, resolve_bot_member, resolve_guild

log = logging.getLogger(__name__)


async def nuke_server(client: discord.Client, config: AppConfig, guild_id: int | None = None) -> None:
    if guild_id is None:
        guild_id = await prompt_int("Enter server ID: ")

    guild = await resolve_guild(client, guild_id)
    if guild is None:
        log.error("Server %s not found", guild_id)
        return

    bot_member = await resolve_bot_member(guild, client)
    if bot_member is None:
        log.error("Cannot resolve member in guild — aborting nuke")
        return

    reason = await prompt("Ban reason (optional): ")

    actions = [
        ("banning members", {"ban_members": True}, ban_members, (client, guild, bot_member, reason, config)),
        ("deleting channels", {"manage_channels": True}, delete_channels, (guild, config)),
        ("deleting roles", {"manage_roles": True}, delete_roles, (guild, bot_member, config)),
        ("deleting emojis", {"manage_emojis": True}, delete_emojis, (guild, config)),
        ("deleting stickers", {"manage_emojis": True}, delete_stickers, (guild, config)),
    ]

    for name, perms, func, args in actions:
        if await check_permissions_and_confirm(client, guild, perms, name):
            await func(*args)

    log.info("Nuke operations completed for %s", guild.name)
    await prompt("Press Enter to continue...")


async def ban_members(
    client: discord.Client,
    guild: discord.Guild,
    bot_member: discord.Member,
    reason: str,
    config: AppConfig,
) -> None:
    members = [m for m in guild.members if m != client.user and m.top_role < bot_member.top_role]
    total = len(members)
    for idx, member in enumerate(members, 1):
        try:
            await member.ban(reason=reason or None, delete_message_seconds=604800)
            log.info("[%s/%s] Banned %s", idx, total, member)
        except discord.HTTPException as exc:
            log.error("[%s/%s] Failed to ban %s: %s", idx, total, member, exc)
        if idx < total:
            await asyncio.sleep(random_cooldown(config.min_ban, config.max_ban))


async def delete_channels(guild: discord.Guild, config: AppConfig) -> None:
    for channel in guild.channels:
        try:
            await channel.delete()
            log.info("Deleted channel %s", channel.name)
        except discord.HTTPException as exc:
            log.error("Failed to delete channel %s: %s", channel.name, exc)
        await asyncio.sleep(random_cooldown(config.min_general, config.max_general))


async def delete_roles(guild: discord.Guild, bot_member: discord.Member, config: AppConfig) -> None:
    for role in guild.roles:
        if role.name != "@everyone" and role.position < bot_member.top_role.position:
            try:
                await role.delete()
                log.info("Deleted role %s", role.name)
            except discord.HTTPException as exc:
                log.error("Failed to delete role %s: %s", role.name, exc)
            await asyncio.sleep(random_cooldown(config.min_general, config.max_general))


async def delete_emojis(guild: discord.Guild, config: AppConfig) -> None:
    emojis = await guild.fetch_emojis()
    for emoji in emojis:
        try:
            await emoji.delete()
            log.info("Deleted emoji %s", emoji.name)
        except discord.HTTPException as exc:
            log.error("Failed to delete emoji %s: %s", emoji.name, exc)
        await asyncio.sleep(random_cooldown(config.min_general, config.max_general))


async def delete_stickers(guild: discord.Guild, config: AppConfig) -> None:
    stickers = await guild.fetch_stickers()
    for sticker in stickers:
        try:
            await sticker.delete()
            log.info("Deleted sticker %s", sticker.name)
        except discord.HTTPException as exc:
            log.error("Failed to delete sticker %s: %s", sticker.name, exc)
        await asyncio.sleep(random_cooldown(config.min_general, config.max_general))
