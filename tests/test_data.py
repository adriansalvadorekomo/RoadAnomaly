"""The frozen split, the data loader and the normal regions of Binôme B."""
import numpy as np
import pytest

from roadanomaly import data_pipeline as dp, splitting
from roadanomaly.normal_regions import normal_cells, normal_patches


def test_manifest_rules():
    manifest = splitting.verify_manifest()
    assert len(manifest) == 60


@pytest.mark.slow
def test_split_regenerates_identically():
    """The documented procedure (notebook 3) gives back the frozen manifest exactly."""
    stats = splitting.frame_statistics()
    stats["scene_group"] = stats["frame"].map(splitting.scene_groups(stats["frame"].tolist(),
                                                                     dp.DATA_DIR / "credits.txt"))
    split, seed, _ = splitting.best_split(stats)
    manifest = splitting.verify_manifest().set_index("frame")
    assert (split.values == manifest.loc[stats["frame"], "split"].values).all()
    assert seed == 415


def test_load_split_conventions():
    frames, images, masks = dp.load_split("val", (64, 128))
    assert len(frames) == 9 and images.shape == (9, 64, 128, 3) and masks.shape == (9, 64, 128, 1)
    assert images.dtype == np.float32 and 0 <= images.min() and images.max() <= 1
    assert set(np.unique(masks)) <= {0.0, 1.0}


def test_normal_patches_never_touch_an_obstacle():
    images = np.zeros((1, 128, 128, 3), np.float32)
    masks = np.zeros((1, 128, 128, 1), np.float32); masks[0, 60:70, 60:70] = 1
    patches, total = normal_patches(images, masks, patch=32, stride=32, margin=4)
    assert total == 16 and len(patches) == 12      # the 4 patches around the obstacle are dropped


def test_normal_cells_mark_the_obstacle_cells():
    masks = np.zeros((1, 64, 64, 1), np.float32); masks[0, :16, :16] = 1
    cells = normal_cells(masks, (4, 4), margin=0)
    assert not cells[0, 0, 0] and cells[0, 3, 3] and cells.sum() == 15
