"""Command-line interface and application entry."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from karuma import __version__
from karuma.config import AppConfig
from karuma.features import (
    deep_scrape_members,
    leave_all_servers,
    list_servers,
    mass_dm_all_users,
    mass_dm_from_file,
    mass_dm_server,
    nuke_server,
    raid_server,
    scrape_members,
)
from karuma.logging_setup import setup_logging
from karuma.startup import bootstrap
from karuma.ui.menu import main_menu

log = logging.getLogger(__name__)

LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="karuma",
        description="Karuma Discord automation toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m karuma                          Interactive menu
  python -m karuma list-servers             List guilds and exit
  python -m karuma mass-dm-file --limit 50  DM from members.txt
  python -m karuma scrape --invite discord.gg/abc
  python -m karuma --log-level DEBUG menu   Verbose interactive mode
        """,
    )

    parser.add_argument("--version", action="version", version=f"Karuma {__version__}")

    parser.add_argument("-c", "--config", default="config.json", help="Path to config.json")
    parser.add_argument("-t", "--tokens", default="tokens.txt", help="Path to tokens file")
    parser.add_argument("-p", "--proxies", default="proxies.txt", help="Path to proxies file")
    parser.add_argument("-m", "--members", default="members.txt", help="Path to members ID file")

    parser.add_argument("--log-level", choices=LOG_LEVELS, default="INFO", help="Console log level")
    parser.add_argument("--log-file", default="karuma.log", help="Log file path (use 'none' to disable)")
    parser.add_argument("--no-color", action="store_true", help="Disable colored console logs")

    parser.add_argument("--skip-disclaimer", action="store_true", help="Skip TOS disclaimer")
    parser.add_argument("--skip-boot", action="store_true", help="Skip boot animation")
    parser.add_argument("--connect-timeout", type=float, default=60.0, help="Seconds to wait for login")

    sub = parser.add_subparsers(dest="command", metavar="command")

    sub.add_parser("menu", help="Interactive menu (default)")

    p_list = sub.add_parser("list-servers", help="List connected servers")
    p_list.set_defaults(run=list_servers)

    p_leave = sub.add_parser("leave-all", help="Leave every server on primary account")
    p_leave.set_defaults(run=leave_all_servers)

    p_nuke = sub.add_parser("nuke", help="Nuke a server")
    p_nuke.add_argument("--guild-id", type=int, required=True)
    p_nuke.set_defaults(run=lambda c, cfg, args: nuke_server(c, cfg, args.guild_id))

    p_raid = sub.add_parser("raid", help="Raid a server")
    p_raid.add_argument("--guild-id", type=int, required=True)
    p_raid.set_defaults(run=lambda c, cfg, args: raid_server(c, cfg, args.guild_id))

    p_dm_server = sub.add_parser("mass-dm-server", help="Mass DM all members in a guild")
    p_dm_server.add_argument("--guild-id", type=int, required=True)
    p_dm_server.set_defaults(run=lambda clients, cfg, args: mass_dm_server(clients, cfg, args.guild_id))

    p_dm_all = sub.add_parser("mass-dm-all", help="Mass DM all cached users")
    p_dm_all.set_defaults(run=lambda clients, cfg, _args: mass_dm_all_users(clients, cfg))

    p_dm_file = sub.add_parser("mass-dm-file", help="Mass DM IDs from members file")
    p_dm_file.add_argument("--limit", type=int, default=None, help="Max users to DM from file bottom")
    p_dm_file.set_defaults(run=lambda clients, cfg, args: mass_dm_from_file(clients, cfg, limit=args.limit))

    p_scrape = sub.add_parser("scrape", help="Fast member scrape via invite")
    p_scrape.add_argument("--invite", required=True, help="Discord invite URL or code")
    p_scrape.set_defaults(run=lambda c, cfg, args: scrape_members(c, cfg, args.invite))

    p_deep = sub.add_parser("deep-scrape", help="Scrape active users from message history")
    p_deep.add_argument("--invite", required=True)
    p_deep.set_defaults(run=lambda c, cfg, args: deep_scrape_members(c, cfg, args.invite))

    return parser


def load_config_from_args(args: argparse.Namespace) -> AppConfig:
    overrides = {
        "skip_disclaimer": args.skip_disclaimer or None,
        "skip_booting": args.skip_boot or None,
        "connect_timeout": args.connect_timeout,
    }
    cfg = AppConfig.load(args.config, **{k: v for k, v in overrides.items() if v is not None})
    cfg.tokens_path = Path(args.tokens)
    cfg.proxies_path = Path(args.proxies)
    cfg.members_path = Path(args.members)
    cfg.config_path = Path(args.config)
    return cfg


async def run_command(ctx, args: argparse.Namespace) -> None:
    command = args.command or "menu"
    if command == "menu":
        await main_menu(ctx.clients, ctx.config)
        return

    primary = ctx.clients[0]
    run = getattr(args, "run", None)
    if run is None:
        log.error("Unknown command: %s", command)
        return

    sig_clients = ctx.clients
    if command in {"mass-dm-server", "mass-dm-all", "mass-dm-file"}:
        await run(sig_clients, ctx.config, args)
    elif command in {"list-servers", "leave-all"}:
        await run(primary)
    else:
        await run(primary, ctx.config, args)

    for client in ctx.clients:
        await client.close()


async def async_main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    log_file = None if args.log_file.lower() == "none" else Path(args.log_file)
    setup_logging(level=args.log_level, log_file=log_file, use_color=not args.no_color)

    try:
        config = load_config_from_args(args)
        ctx = await bootstrap(config)
        await run_command(ctx, args)
        return 0
    except KeyboardInterrupt:
        log.info("Interrupted")
        return 130
    except RuntimeError as exc:
        log.error("%s", exc)
        return 1
    except Exception:
        log.exception("Fatal error")
        return 1


def main(argv: list[str] | None = None) -> None:
    sys.tracebacklimit = 0
    raise SystemExit(asyncio.run(async_main(argv)))


if __name__ == "__main__":
    main()
