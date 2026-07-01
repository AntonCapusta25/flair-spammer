"""Server raid operations."""

import asyncio
import logging

import discord

from karuma.config import AppConfig
from karuma.features.permissions import check_permissions_and_confirm
from karuma.utils import prompt, prompt_int, random_cooldown, resolve_bot_member, resolve_guild

log = logging.getLogger(__name__)


async def raid_server(client: discord.Client, config: AppConfig, guild_id: int | None = None) -> None:
    if guild_id is None:
        guild_id = await prompt_int("Enter server ID: ")

    guild = await resolve_guild(client, guild_id)
    if guild is None:
        log.error("Server %s not found", guild_id)
        return

    bot_member = await resolve_bot_member(guild, client)
    if bot_member is None:
        log.error("Cannot resolve member in guild — aborting raid")
        return

    new_name = await prompt("New server name (leave blank to skip): ")
    channel_name = await prompt("Channel name to spam: ")
    channel_count = int((await prompt("Number of channels to create (0 to skip): ")) or "0")
    role_name = await prompt("Role name to spam: ")
    role_count = int((await prompt("Number of roles to create (0 to skip): ")) or "0")
    nickname = await prompt("Nickname to set (leave blank to skip): ")

    planned: list[tuple[str, dict, object, tuple | None]] = [
        ("renaming server", {"manage_guild": True}, rename_server, (guild, new_name) if new_name else None),
        (
            "creating channels",
            {"manage_channels": True},
            create_channels,
            (guild, channel_name, channel_count, config) if channel_count > 0 else None,
        ),
        (
            "creating roles",
            {"manage_roles": True},
            create_roles,
            (guild, role_name, role_count, config) if role_count > 0 else None,
        ),
        (
            "changing nicknames",
            {"manage_nicknames": True},
            change_nicknames,
            (client, guild, bot_member, nickname, config) if nickname else None,
        ),
    ]

    for name, perms, func, args in planned:
        if args is None:
            continue
        if await check_permissions_and_confirm(client, guild, perms, name):
            await func(*args)

    log.info("Raid operations completed for %s", guild.name)
    await prompt("Press Enter to continue...")


async def rename_server(guild: discord.Guild, new_name: str) -> None:
    try:
        await guild.edit(name=new_name)
        log.info("Server renamed to %s", new_name)
    except discord.HTTPException as exc:
        log.error("Failed to rename server: %s", exc)


async def create_channels(guild: discord.Guild, channel_name: str, count: int, config: AppConfig) -> None:
    for i in range(count):
        try:
            await guild.create_text_channel(f"{channel_name}-{i + 1}")
            log.info("Created channel %s-%s", channel_name, i + 1)
        except discord.HTTPException as exc:
            log.error("Failed to create channel: %s", exc)
        await asyncio.sleep(random_cooldown(config.min_general, config.max_general))


async def create_roles(guild: discord.Guild, role_name: str, count: int, config: AppConfig) -> None:
    for i in range(count):
        try:
            await guild.create_role(name=f"{role_name}-{i + 1}")
            log.info("Created role %s-%s", role_name, i + 1)
        except discord.HTTPException as exc:
            log.error("Failed to create role: %s", exc)
        await asyncio.sleep(random_cooldown(config.min_general, config.max_general))


async def change_nicknames(
    client: discord.Client,
    guild: discord.Guild,
    bot_member: discord.Member,
    nickname: str,
    config: AppConfig,
) -> None:
    members = [m for m in guild.members if m != client.user and m.top_role < bot_member.top_role]
    for member in members:
        try:
            await member.edit(nick=nickname)
            log.info("Changed nickname for %s", member)
        except discord.HTTPException as exc:
            log.error("Failed to change nickname for %s: %s", member, exc)
        await asyncio.sleep(random_cooldown(config.min_general, config.max_general))
