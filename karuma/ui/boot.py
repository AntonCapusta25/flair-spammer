"""Startup splash and disclaimer."""

import asyncio
import logging

from colorama import Fore, Style

from karuma.config import AppConfig

log = logging.getLogger(__name__)


async def show_disclaimer(config: AppConfig) -> None:
    if config.skip_disclaimer:
        return

    lines = [
        f"{Fore.LIGHTWHITE_EX}{Style.BRIGHT}DISCLAIMER:",
        f"{Style.RESET_ALL}{Fore.LIGHTWHITE_EX}User automation violates Discord's Terms of Service.",
        f"{Fore.LIGHTWHITE_EX}Use only for educational purposes and at your own risk.",
        f"{Fore.LIGHTWHITE_EX}Mass DM requires privileged member intents on your account.",
        f"{Fore.LIGHTWHITE_EX}Improper use may get your account banned.",
    ]
    for idx, line in enumerate(lines):
        print(line)
        if idx < len(lines) - 1:
            await asyncio.sleep(0.8)


async def show_boot_animation(config: AppConfig) -> None:
    if config.skip_booting:
        return

    stages = [
        (f"{Style.BRIGHT}{Fore.LIGHTWHITE_EX}Booting {Fore.RED}Karuma {Fore.RESET}{Fore.LIGHTWHITE_EX}Tool", 0.3),
        (f"{Fore.RED}25%", 0.5),
        (f"{Fore.YELLOW}50%", 0.6),
        (f"{Fore.LIGHTYELLOW_EX}75%", 0.7),
        (f"{Fore.LIGHTGREEN_EX}99%", 1.0),
        (f"{Fore.LIGHTBLUE_EX}Karuma Tool ready", 1.0),
    ]
    for text, delay in stages:
        print(text)
        await asyncio.sleep(delay)
