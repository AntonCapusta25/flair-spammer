"""Guild permission checks for destructive actions."""

import logging

import discord

from karuma.utils import prompt, resolve_bot_member

log = logging.getLogger(__name__)


async def check_permissions_and_confirm(
    client: discord.Client,
    guild: discord.Guild,
    required_perms: dict[str, bool],
    action_name: str,
) -> bool:
    """
    Verify the client has required permissions.

    Returns True when the action should proceed, False when it should be skipped.
    """
    bot_member = await resolve_bot_member(guild, client)
    if bot_member is None:
        log.error("Cannot resolve guild member for %s — skipping %s", client.user, action_name)
        return False

    missing = [
        perm
        for perm, required in required_perms.items()
        if required and not getattr(bot_member.guild_permissions, perm, False)
    ]

    if not missing:
        return True

    log.warning("Missing permissions for %s: %s", action_name, ", ".join(missing))
    confirm = (await prompt(f"Missing {action_name} permissions. Skip this step? (yes/no): ")).lower()
    if confirm == "yes":
        log.info("Skipping %s due to missing permissions", action_name)
        return False

    log.info("Aborting %s — user declined to skip", action_name)
    return False
