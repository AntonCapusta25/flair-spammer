"""Shared pytest fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def sample_config_json(project_root: Path) -> Path:
    path = project_root / "config.json"
    path.write_text(
        """{
  "skip_disclaimer": true,
  "skip_booting": false,
  "minimum_dm_delay": 2.0,
  "maximum_dm_delay": 4.0,
  "minimum_ban_delay": 1.0,
  "maximum_ban_delay": 2.0,
  "minimum_general_delay": 0.5,
  "maximum_general_delay": 1.0,
  "captcha_api_key": "",
  "captcha_service": "manual"
}""",
        encoding="utf-8",
    )
    return path
