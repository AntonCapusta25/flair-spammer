"""Tests for karuma.features.permissions."""

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from karuma.features.permissions import check_permissions_and_confirm


def _make_guild_with_perms(*, ban_members: bool = False) -> tuple[MagicMock, MagicMock, MagicMock]:
    client = MagicMock(spec=discord.Client)
    client.user = MagicMock(id=99)
    guild = MagicMock(spec=discord.Guild)
    member = MagicMock(spec=discord.Member)
    perms = MagicMock()
    perms.ban_members = ban_members
    member.guild_permissions = perms
    return client, guild, member


async def test_check_permissions_all_present() -> None:
    client, guild, member = _make_guild_with_perms(ban_members=True)
    with patch("karuma.features.permissions.resolve_bot_member", AsyncMock(return_value=member)):
        result = await check_permissions_and_confirm(
            client, guild, {"ban_members": True}, "banning"
        )
    assert result is True


async def test_check_permissions_missing_user_skips_skip() -> None:
    client, guild, _ = _make_guild_with_perms()
    with patch("karuma.features.permissions.resolve_bot_member", AsyncMock(return_value=None)):
        result = await check_permissions_and_confirm(
            client, guild, {"ban_members": True}, "banning"
        )
    assert result is False


async def test_check_permissions_missing_confirmed_skip() -> None:
    client, guild, member = _make_guild_with_perms(ban_members=False)
    with patch("karuma.features.permissions.resolve_bot_member", AsyncMock(return_value=member)):
        with patch("karuma.features.permissions.prompt", AsyncMock(return_value="yes")):
            result = await check_permissions_and_confirm(
                client, guild, {"ban_members": True}, "banning"
            )
    assert result is False


async def test_check_permissions_missing_declined() -> None:
    client, guild, member = _make_guild_with_perms(ban_members=False)
    with patch("karuma.features.permissions.resolve_bot_member", AsyncMock(return_value=member)):
        with patch("karuma.features.permissions.prompt", AsyncMock(return_value="no")):
            result = await check_permissions_and_confirm(
                client, guild, {"ban_members": True}, "banning"
            )
    assert result is False
