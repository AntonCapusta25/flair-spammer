"""Mass direct-message features."""

import asyncio
import logging
from pathlib import Path

import discord

from karuma.config import AppConfig
from karuma.utils import fetch_member_ids, prompt, random_cooldown, resolve_guild

log = logging.getLogger(__name__)


async def create_embed() -> discord.Embed:
    embed = discord.Embed()
    title = await prompt("Embed title (leave blank for none): ")
    if title:
        embed.title = title
    description = await prompt("Embed description (leave blank for none): ")
    if description:
        embed.description = description
    color = await prompt("Embed color (hex without #, e.g. FF0000): ")
    if color:
        try:
            embed.color = int(color, 16)
        except ValueError:
            embed.color = discord.Color.random()
    while True:
        field_name = await prompt("Add field name (leave blank to stop): ")
        if not field_name:
            break
        field_value = await prompt("Field value: ")
        inline = (await prompt("Inline field? (y/n): ")).lower() == "y"
        embed.add_field(name=field_name, value=field_value, inline=inline)
    author_name = await prompt("Author name (leave blank for none): ")
    if author_name:
        author_icon = await prompt("Author icon URL (leave blank for none): ")
        embed.set_author(name=author_name, icon_url=author_icon or None)
    footer_text = await prompt("Footer text (leave blank for none): ")
    if footer_text:
        footer_icon = await prompt("Footer icon URL (leave blank for none): ")
        embed.set_footer(text=footer_text, icon_url=footer_icon or None)
    thumbnail = await prompt("Thumbnail URL (leave blank for none): ")
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    image = await prompt("Image URL (leave blank for none): ")
    if image:
        embed.set_image(url=image)
    return embed


async def mass_dm_users(
    clients: list[discord.Client],
    user_ids: list[int],
    config: AppConfig,
    *,
    message_type: str | None = None,
    text_content: str | None = None,
    embed_content: discord.Embed | None = None,
) -> None:
    if message_type is None:
        message_type = (await prompt("Message type (text/embed/both): ")).lower()

    if message_type in {"text", "both"} and text_content is None:
        text_content = await prompt("Enter text message: ")
    if message_type in {"embed", "both"} and embed_content is None:
        embed_content = await create_embed()

    if not text_content and not embed_content:
        log.error("No message content provided")
        return

    total = len(user_ids)
    sent_count = 0
    for idx, uid in enumerate(user_ids, 1):
        current_client = clients[(idx - 1) % len(clients)]
        try:
            target = current_client.get_user(uid)
            if target is None:
                try:
                    target = await current_client.fetch_user(uid)
                except discord.HTTPException:
                    target = None

            if target is None or target.bot or target.id == current_client.user.id:
                continue

            try:
                dm_channel = await target.create_dm()
            except discord.HTTPException as exc:
                log.error("[%s/%s] Could not open DM with %s: %s", idx, total, uid, exc)
                continue

            embed_to_send = embed_content.copy() if embed_content is not None else None
            try:
                if message_type == "text":
                    await dm_channel.send(content=text_content)
                elif message_type == "embed":
                    await dm_channel.send(embed=embed_to_send)
                else:
                    await dm_channel.send(content=text_content, embed=embed_to_send)
                sent_count += 1
                log.info("[%s/%s] Sent to %s via %s", idx, total, target, current_client.user)
            except discord.HTTPException as exc:
                log.error("[%s/%s] Failed to send to %s: %s", idx, total, uid, exc)
        except Exception as exc:
            log.error("[%s/%s] Unexpected error for %s: %s", idx, total, uid, exc)

        if idx < total:
            await asyncio.sleep(random_cooldown(config.minimum_dm, config.maximum_dm))

    log.info("Mass DM finished — sent %s / %s targets", sent_count, total)


async def mass_dm_server(
    clients: list[discord.Client],
    config: AppConfig,
    guild_id: int | None = None,
) -> None:
    client = clients[0]
    if guild_id is None:
        guild_id = int(await prompt("Enter server ID: "))

    guild = await resolve_guild(client, guild_id)
    if guild is None:
        log.error("Server %s not found", guild_id)
        return

    log.info("Mass DM target guild: %s (%s members cached)", guild.name, guild.member_count)
    member_ids = await fetch_member_ids(guild, client)
    log.info("Resolved %s member IDs", len(member_ids))
    await mass_dm_users(clients, member_ids, config)


async def mass_dm_all_users(clients: list[discord.Client], config: AppConfig) -> None:
    all_users: set[int] = set()
    for client in clients:
        for user in client.users:
            if not user.bot:
                all_users.add(user.id)
    log.info("Mass DM all users — %s unique IDs from client cache", len(all_users))
    await mass_dm_users(clients, list(all_users), config)


async def mass_dm_from_file(
    clients: list[discord.Client],
    config: AppConfig,
    *,
    limit: int | None = None,
) -> None:
    members_path = config.members_path
    if not members_path.exists():
        log.error("%s not found", members_path)
        return

    user_ids = [
        int(line.strip())
        for line in members_path.read_text(encoding="utf-8").splitlines()
        if line.strip().isdigit()
    ]
    log.info("Loaded %s IDs from %s", len(user_ids), members_path)

    if limit is None:
        limit_input = await prompt("Limit DMs? Enter number or leave blank for all: ")
        if limit_input.isdigit():
            limit = int(limit_input)

    if limit is not None:
        user_ids = list(reversed(user_ids))[:limit]
        log.info("Limited to %s IDs from bottom of file", len(user_ids))

    await mass_dm_users(clients, user_ids, config)
