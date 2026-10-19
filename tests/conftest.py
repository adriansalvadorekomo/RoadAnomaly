"""Shared fixtures for the RoadAnomaly test suite."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
FRAMES_DIR = DATA_DIR / "frames"
FRAME_LIST = DATA_DIR / "frame_list.json"


@pytest.fixture(scope="session")
def data_dir() -> Path:
    """Path to the tracked dataset directory."""
    if not DATA_DIR.is_dir():
        pytest.skip(f"dataset not present at {DATA_DIR}")
    return DATA_DIR


@pytest.fixture(scope="session")
def frame_names(data_dir: Path) -> list[str]:
    """Frame file names in the order declared by frame_list.json."""
    return json.loads(FRAME_LIST.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def label_dirs(data_dir: Path) -> list[Path]:
    """Every ``<frame>.labels`` annotation directory."""
    return sorted(FRAMES_DIR.glob("*.labels"))
