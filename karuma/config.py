"""Configuration loading and validation."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PLACEHOLDER_CAPTCHA_KEYS = frozenset({
    "",
    "your captcha api key here",
    "your_captcha_api_key_here",
})


@dataclass
class AppConfig:
    """Runtime settings loaded from config.json and CLI overrides."""

    config_path: Path = field(default_factory=lambda: Path("config.json"))
    tokens_path: Path = field(default_factory=lambda: Path("tokens.txt"))
    proxies_path: Path = field(default_factory=lambda: Path("proxies.txt"))
    members_path: Path = field(default_factory=lambda: Path("members.txt"))

    minimum_dm: float = 1.0
    maximum_dm: float = 3.0
    min_ban: float = 1.0
    max_ban: float = 3.0
    min_general: float = 0.5
    max_general: float = 1.5

    token: str = ""
    skip_booting: bool = False
    skip_disclaimer: bool = False
    captcha_api_key: str = ""
    captcha_service: str = "manual"
    x_super_properties: str = ""
    connect_timeout: float = 60.0

    @classmethod
    def load(cls, config_path: Path | str = "config.json", **overrides: Any) -> "AppConfig":
        """Load config from disk and apply CLI overrides."""
        path = Path(config_path)
        cfg = cls(config_path=path)

        if path.exists():
            try:
                with path.open(encoding="utf-8") as fh:
                    data = json.load(fh)
                cfg._apply_file(data)
            except (OSError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"Failed to load config from {path}: {exc}") from exc
        else:
            logger.warning("Config file not found at %s — using defaults", path)

        for key, value in overrides.items():
            if value is not None and hasattr(cfg, key):
                setattr(cfg, key, value)

        cfg._normalize_captcha_settings()
        return cfg

    def _apply_file(self, data: dict[str, Any]) -> None:
        self.minimum_dm = float(data.get("minimum_dm_delay", self.minimum_dm))
        self.maximum_dm = float(data.get("maximum_dm_delay", self.maximum_dm))
        self.min_ban = float(data.get("minimum_ban_delay", self.min_ban))
        self.max_ban = float(data.get("maximum_ban_delay", self.max_ban))
        self.min_general = float(data.get("minimum_general_delay", self.min_general))
        self.max_general = float(data.get("maximum_general_delay", self.max_general))
        self.token = data.get("token", self.token)
        self.skip_booting = bool(data.get("skip_booting", self.skip_booting))
        self.skip_disclaimer = bool(data.get("skip_disclaimer", self.skip_disclaimer))
        self.captcha_api_key = data.get("captcha_api_key", self.captcha_api_key)
        self.captcha_service = data.get("captcha_service", self.captcha_service)
        self.x_super_properties = data.get("x_super_properties", self.x_super_properties)

    def _normalize_captcha_settings(self) -> None:
        key = (self.captcha_api_key or "").strip()
        if key.lower() in PLACEHOLDER_CAPTCHA_KEYS:
            self.captcha_api_key = ""
            if self.captcha_service != "manual":
                logger.warning(
                    "captcha_api_key is missing or a placeholder — falling back to manual captcha"
                )
                self.captcha_service = "manual"
        elif not self.captcha_service:
            self.captcha_service = "2captcha"

    def load_tokens(self) -> list[str]:
        """Return tokens from tokens file, falling back to config token."""
        tokens: list[str] = []
        if self.tokens_path.exists():
            tokens = [
                line.strip()
                for line in self.tokens_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        if not tokens and self.token and self.token.strip().lower() != "your token here":
            tokens = [self.token.strip()]
        return tokens

    def load_proxies(self) -> list[str]:
        """Return normalized proxy URLs from proxies file."""
        if not self.proxies_path.exists():
            return []

        proxies: list[str] = []
        for line in self.proxies_path.read_text(encoding="utf-8").splitlines():
            p = line.strip()
            if not p or p.startswith("#"):
                continue
            if not p.startswith(("http://", "https://", "socks4://", "socks5://")):
                p = f"http://{p}"
            proxies.append(p)
        return proxies
