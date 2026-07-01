"""Interactive main menu."""

import asyncio
import logging
import sys

import pyfade
from colorama import Fore

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
from karuma.utils import clear_console, prompt

log = logging.getLogger(__name__)

BANNER = """
██╗  ██╗ █████╗ ██████╗ ██╗   ██╗███╗   ███╗ █████╗ 
██║ ██╔╝██╔══██╗██╔══██╗██║   ██║████╗ ████║██╔══██╗
█████═╝ ███████║██████╔╝██║   ██║██╔████╔██║███████║
██╔═██╗ ██╔══██║██╔══██╗██║   ██║██║╚██╔╝██║██╔══██║
██║ ╚██╗██║  ██║██║  ██║╚██████╔╝██║ ╚═╝ ██║██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝"""

MENU = """
{white}GitHub: {blue}https://github.com/hoemotion/Karuma
{green}Active Accounts: {yellow}{count}
{green}Primary Account: {yellow}{primary}

{green}[1]  Nuke Server
{green}[2]  Raid Server
{green}[3]  Mass DM Server
{green}[4]  Mass DM All Users
{green}[5]  Mass DM from members.txt
{green}[6]  Fast Scrape Members
{green}[7]  Deep Scrape Members
{green}[8]  List Servers
{green}[9]  Leave All Servers
{green}[10] Exit
"""


async def main_menu(clients: list, config: AppConfig) -> None:
    primary = clients[0]
    handlers = {
        "1": lambda: nuke_server(primary, config),
        "2": lambda: raid_server(primary, config),
        "3": lambda: mass_dm_server(clients, config),
        "4": lambda: mass_dm_all_users(clients, config),
        "5": lambda: mass_dm_from_file(clients, config),
        "6": lambda: scrape_members(primary, config),
        "7": lambda: deep_scrape_members(primary, config),
        "8": lambda: list_servers(primary),
        "9": lambda: leave_all_servers(primary),
    }

    while True:
        await clear_console()
        print(pyfade.Fade.Horizontal(pyfade.Colors.yellow_to_red, BANNER))
        print(
            MENU.format(
                white=Fore.LIGHTWHITE_EX,
                blue=Fore.LIGHTBLUE_EX,
                green=Fore.LIGHTGREEN_EX,
                yellow=Fore.YELLOW,
                count=len(clients),
                primary=primary.user,
            )
        )

        choice = (await prompt(f"{Fore.LIGHTGREEN_EX}Select>> ")).strip().lower()

        if choice in {"10", "quit", "exit"}:
            log.info("Shutting down")
            for client in clients:
                await client.close()
            sys.exit(0)

        handler = handlers.get(choice)
        if handler is None:
            log.warning("Invalid menu choice: %s", choice)
            await asyncio.sleep(1)
            continue

        try:
            await handler()
        except Exception as exc:
            log.exception("Menu action failed: %s", exc)
            await prompt("Press Enter to continue...")
