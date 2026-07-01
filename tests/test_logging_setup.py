"""Tests for karuma.logging_setup."""

import logging
from pathlib import Path

from karuma.logging_setup import ColorFormatter, setup_logging


def test_color_formatter_adds_ansi() -> None:
    formatter = ColorFormatter("%(levelname)s | %(message)s")
    record = logging.LogRecord("test", logging.INFO, "", 0, "hello", (), None)
    output = formatter.format(record)
    assert "INFO" in output
    assert "hello" in output


def test_setup_logging_creates_file_handler(tmp_path: Path) -> None:
    log_file = tmp_path / "test.log"
    setup_logging(level="DEBUG", log_file=log_file, use_color=False)
    logging.getLogger("karuma.test").info("test message")
    assert log_file.exists()
    assert "test message" in log_file.read_text(encoding="utf-8")


def test_setup_logging_no_file() -> None:
    setup_logging(level="INFO", log_file=None, use_color=False)
    root = logging.getLogger()
    assert any(isinstance(h, logging.StreamHandler) for h in root.handlers)
    assert not any(isinstance(h, logging.FileHandler) for h in root.handlers)
