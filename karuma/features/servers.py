"""Server listing and bulk leave."""

import asyncio
import logging

import discord

from karuma.utils import prompt, resolve_bot_member

log = logging.getLogger(__name__)


async def list_servers(client: discord.Client) -> None:
    log.info("Connected servers for %s:", client.user)
    for guild in client.guilds:
        bot_member = await resolve_bot_member(guild, client)
        if bot_member is None:
            log.warning("%s (ID: %s) — member not resolved", guild.name, guild.id)
            continue

        perms = []
        gp = bot_member.guild_permissions
        if gp.ban_members:
            perms.append("Ban")
        if gp.manage_channels:
            perms.append("Channels")
        if gp.manage_roles:
            perms.append("Roles")
        if gp.manage_nicknames:
            perms.append("Nicks")
        if gp.manage_emojis:
            perms.append("Emojis")
        if gp.manage_guild:
            perms.append("Server")
        if gp.create_instant_invite:
            perms.append("Invites")

        perm_status = ", ".join(perms) if perms else "none"
        log.info("%s | ID %s | members %s | perms: %s", guild.name, guild.id, guild.member_count, perm_status)

        if gp.manage_guild:
            try:
                invites = await guild.invites()
                permanent = [inv for inv in invites if inv.max_age == 0]
                for invite in permanent:
                    log.info("  invite %s (uses %s)", invite.url, invite.uses)
            except discord.Forbidden:
                log.warning("  no invite access")
            except discord.HTTPException as exc:
                log.error("  invite fetch failed: %s", exc)

    await prompt("Press Enter to continue...")


async def leave_all_servers(client: discord.Client) -> None:
    confirm = (await prompt("Leave ALL servers on primary account? (yes/no): ")).lower()
    if confirm != "yes":
        log.info("Leave-all cancelled")
        return

    for guild in client.guilds:
        try:
            await guild.leave()
            log.info("Left %s", guild.name)
        except discord.HTTPException as exc:
            log.error("Failed to leave %s: %s", guild.name, exc)
        await asyncio.sleep(1)

    log.info("Finished leaving servers")
    await prompt("Press Enter to continue...")
