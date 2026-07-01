"""Tests for karuma.utils."""

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from karuma.utils import (
    fetch_member_ids,
    random_cooldown,
    resolve_bot_member,
    resolve_guild,
    wait_for_ready,
)


def test_random_cooldown_within_bounds() -> None:
    for _ in range(50):
        value = random_cooldown(1.0, 3.0)
        assert 1.0 <= value <= 3.0


async def test_wait_for_ready_returns_ready_clients() -> None:
    ready_client = MagicMock(spec=discord.Client)
    ready_client.is_ready.return_value = True
    pending_client = MagicMock(spec=discord.Client)
    pending_client.is_ready.return_value = False

    result = await wait_for_ready([ready_client, pending_client], timeout=0.6)
    assert result == [ready_client]


async def test_wait_for_ready_empty_on_timeout() -> None:
    client = MagicMock(spec=discord.Client)
    client.is_ready.return_value = False
    result = await wait_for_ready([client], timeout=0.3)
    assert result == []


async def test_resolve_guild_found() -> None:
    guild = MagicMock(spec=discord.Guild)
    guild.id = 123
    client = MagicMock(spec=discord.Client)
    client.guilds = [guild]
    assert await resolve_guild(client, 123) is guild


async def test_resolve_guild_not_found() -> None:
    client = MagicMock(spec=discord.Client)
    client.guilds = []
    assert await resolve_guild(client, 999) is None


async def test_resolve_bot_member_from_cache() -> None:
    user = MagicMock()
    user.id = 42
    member = MagicMock(spec=discord.Member)
    guild = MagicMock(spec=discord.Guild)
    guild.get_member.return_value = member
    guild.fetch_member = AsyncMock()
    client = MagicMock(spec=discord.Client)
    client.user = user

    result = await resolve_bot_member(guild, client)
    assert result is member
    guild.fetch_member.assert_not_called()


async def test_resolve_bot_member_fetches_when_missing() -> None:
    user = MagicMock()
    user.id = 42
    member = MagicMock(spec=discord.Member)
    guild = MagicMock(spec=discord.Guild)
    guild.get_member.return_value = None
    guild.fetch_member = AsyncMock(return_value=member)
    client = MagicMock(spec=discord.Client)
    client.user = user

    result = await resolve_bot_member(guild, client)
    assert result is member


async def test_resolve_bot_member_returns_none_on_http_error() -> None:
    user = MagicMock()
    user.id = 42
    guild = MagicMock(spec=discord.Guild)
    guild.name = "Test"
    guild.get_member.return_value = None
    guild.fetch_member = AsyncMock(side_effect=discord.HTTPException(MagicMock(), "fail"))
    client = MagicMock(spec=discord.Client)
    client.user = user

    assert await resolve_bot_member(guild, client) is None


async def test_fetch_member_ids_from_fetch() -> None:
    bot_user = MagicMock()
    bot_user.id = 1
    human = MagicMock()
    human.id = 2
    human.bot = False
    bot_member = MagicMock()
    bot_member.id = 3
    bot_member.bot = True

    guild = MagicMock(spec=discord.Guild)
    guild.fetch_members = AsyncMock(return_value=[human, bot_member])
    client = MagicMock(spec=discord.Client)
    client.user = bot_user

    assert await fetch_member_ids(guild, client) == [2]


async def test_fetch_member_ids_fallback_to_cache() -> None:
    bot_user = MagicMock()
    bot_user.id = 1
    human = MagicMock()
    human.id = 2
    human.bot = False

    guild = MagicMock(spec=discord.Guild)
    guild.name = "Test"
    guild.fetch_members = AsyncMock(side_effect=RuntimeError("chunk failed"))
    guild.members = [human]
    client = MagicMock(spec=discord.Client)
    client.user = bot_user

    assert await fetch_member_ids(guild, client) == [2]
