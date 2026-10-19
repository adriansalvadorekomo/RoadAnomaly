"""Dataset integrity: the frame <-> label contract CI must never let drift.

Every assertion here restates a fact published in README.md ("The dataset"
section). If the dataset is swapped for a different release, this file is
expected to fail loudly rather than let the docs go stale.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

pytestmark = pytest.mark.dataset

# Documented dataset contract. These numbers are asserted here and quoted
# verbatim in README.md. They live with the test rather than in conftest.py
# so the contract cannot drift from the assertions that enforce it.
REPO_ROOT = Path(__file__).resolve().parents[2]
FRAMES_DIR = REPO_ROOT / "data" / "frames"

EXPECTED_FRAME_COUNT = 60
EXPECTED_FRAME_SIZE = (1280, 720)
EXPECTED_INSTANCE_COUNT = 201
BACKGROUND_CLASS = 0
ANOMALY_CLASS = 2
VALID_SEMANTIC_CLASSES = {BACKGROUND_CLASS, ANOMALY_CLASS}

SEMANTIC_ONLY_DIR_COUNT = 14


def _label_dir_for(frame_name: str):
    return FRAMES_DIR / f"{frame_name.removesuffix('.webp')}.labels"


def test_frame_list_matches_frames_on_disk(frame_names: list[str]) -> None:
    assert len(frame_names) == EXPECTED_FRAME_COUNT, (
        f"frame_list.json declares {len(frame_names)} frames, "
        f"README documents {EXPECTED_FRAME_COUNT}"
    )
    on_disk = {p.name for p in FRAMES_DIR.glob("*.webp")}
    assert set(frame_names) == on_disk, "frame_list.json and frames/ disagree"


def test_every_frame_has_a_label_directory(frame_names: list[str]) -> None:
    missing = [n for n in frame_names if not _label_dir_for(n).is_dir()]
    assert not missing, f"{len(missing)} frames have no .labels directory: {missing[:5]}"

    orphaned = [
        p.name for p in FRAMES_DIR.glob("*.labels") if f"{p.name[:-7]}.webp" not in frame_names
    ]
    assert not orphaned, f"{len(orphaned)} label directories have no frame: {orphaned[:5]}"


def test_frames_are_rgb_at_documented_resolution(frame_names: list[str]) -> None:
    bad: list[str] = []
    for name in frame_names:
        with Image.open(FRAMES_DIR / name) as im:
            if im.size != EXPECTED_FRAME_SIZE or im.mode != "RGB":
                bad.append(f"{name}: {im.size} {im.mode}")
    assert not bad, f"frames deviate from {EXPECTED_FRAME_SIZE} RGB: {bad[:5]}"


def test_semantic_masks_use_documented_class_values(frame_names: list[str]) -> None:
    """Semantic masks are uint8 with only {0 = normal, 2 = anomaly}."""
    for name in frame_names:
        label_dir = _label_dir_for(name)
        with (
            Image.open(label_dir / "labels_semantic.png") as mask,
            Image.open(FRAMES_DIR / name) as frame,
        ):
            assert mask.size == frame.size, f"{name}: mask {mask.size} != frame {frame.size}"
            values = {int(v) for v in np.unique(np.array(mask))}
        assert values <= VALID_SEMANTIC_CLASSES, f"{name}: unexpected class values {values}"
        assert ANOMALY_CLASS in values, f"{name}: no anomaly pixels, this is evaluation data"


def test_colour_visualisation_accompanies_every_mask(frame_names: list[str]) -> None:
    missing = [
        n for n in frame_names if not (_label_dir_for(n) / "labels_semantic_color.png").is_file()
    ]
    assert not missing, f"{len(missing)} frames lack labels_semantic_color.png: {missing[:5]}"


def test_instance_annotations_are_self_consistent(frame_names: list[str]) -> None:
    """Where instance labels exist, max(pixel id) equals the instance count."""
    instance_dirs = [n for n in frame_names if (_label_dir_for(n) / "index.json").is_file()]
    semantic_only = [n for n in frame_names if n not in instance_dirs]

    assert len(semantic_only) == SEMANTIC_ONLY_DIR_COUNT, (
        f"{len(semantic_only)} semantic-only frames, README documents "
        f"{SEMANTIC_ONLY_DIR_COUNT}: {sorted(semantic_only)}"
    )

    total_instances = 0
    for name in instance_dirs:
        label_dir = _label_dir_for(name)
        instances = json.loads((label_dir / "index.json").read_text(encoding="utf-8"))["instances"]
        values = np.array(Image.open(label_dir / "labels_instance.png"))
        assert values.max() == len(instances), (
            f"{name}: labels_instance.png reaches id {values.max()} "
            f"but index.json lists {len(instances)} instances"
        )
        assert {inst["cls"] for inst in instances} == {ANOMALY_CLASS}, (
            f"{name}: unexpected classes in index.json"
        )
        total_instances += len(instances)

    assert total_instances == EXPECTED_INSTANCE_COUNT, (
        f"found {total_instances} instances, README documents {EXPECTED_INSTANCE_COUNT}"
    )
