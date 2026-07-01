"""Tests for karuma.cli."""

import argparse
from pathlib import Path

from karuma.cli import build_parser, load_config_from_args


def test_build_parser_default_command_none() -> None:
    args = build_parser().parse_args([])
    assert args.command is None
    assert args.log_level == "INFO"
    assert args.config == "config.json"


def test_build_parser_subcommand_scrape() -> None:
    args = build_parser().parse_args(["scrape", "--invite", "https://discord.gg/test"])
    assert args.command == "scrape"
    assert args.invite == "https://discord.gg/test"


def test_build_parser_mass_dm_file_limit() -> None:
    args = build_parser().parse_args(["mass-dm-file", "--limit", "25"])
    assert args.command == "mass-dm-file"
    assert args.limit == 25


def test_load_config_from_args_paths(sample_config_json: Path, tmp_path: Path) -> None:
    tokens = tmp_path / "my_tokens.txt"
    tokens.touch()
    args = argparse.Namespace(
        config=str(sample_config_json),
        tokens=str(tokens),
        proxies=str(tmp_path / "proxies.txt"),
        members=str(tmp_path / "members.txt"),
        skip_disclaimer=False,
        skip_boot=False,
        connect_timeout=45.0,
    )
    cfg = load_config_from_args(args)
    assert cfg.config_path == sample_config_json
    assert cfg.tokens_path == tokens
    assert cfg.connect_timeout == 45.0
    assert cfg.minimum_dm == 2.0
