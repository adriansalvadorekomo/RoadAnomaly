"""How the shared train / validation / test split was made, and how it is checked.

The split is frozen in splits/split_manifest.csv. Notebook 3 regenerates it with the code
below and asserts that the result is identical to the manifest; nothing ever overwrites it.

- Scene groups (notebook 2, section 8): frames listed under the same source block or the
  same URL of credits.txt come from the same video, photographer or article. A group
  never spans two splits, otherwise the test score would be inflated by near-duplicates.
- make_split: greedy group assignment per category, about 70 / 15 / 15.
- The kept seed is the one whose validation and test sets are closest to the whole dataset
  (anomaly ratio and number of objects per image).
"""
import random

import numpy as np
import pandas as pd
from scipy import ndimage

from roadanomaly import data_pipeline as dp
from roadanomaly.protocol import MIN_OBJECT_PX_FULL

SPLIT_FRACTIONS = {"train": 0.70, "val": 0.15, "test": 0.15}
SPLIT_SEEDS = range(500)              # candidate splits compared by split_distance
EXPECTED_SIZES = {"train": 42, "val": 9, "test": 9}


def frame_statistics(data_dir=dp.DATA_DIR):
    """One row per frame: category, anomaly pixel ratio and number of objects (full resolution).

    An object is an 8-connected component of at least MIN_OBJECT_PX_FULL pixels (smaller
    components are annotation speckle, notebook 2 section 6).
    """
    rows = []
    for frame in dp.list_frames(data_dir):
        _, mask = dp.load_frame(frame, data_dir)
        labeled, n = ndimage.label(mask, structure=np.ones((3, 3)))
        areas = ndimage.sum(mask, labeled, range(1, n + 1)) if n else np.array([])
        rows.append({"frame": frame, "category": dp.category_of(frame),
                     "anomaly_ratio": float(mask.mean()),
                     "n_objects": int((np.asarray(areas) >= MIN_OBJECT_PX_FULL).sum())})
    return pd.DataFrame(rows)


def parse_credits(credits_path):
    """Blocks of credits.txt as (frame names, source lines).

    Frame names are lines without indentation; their source lines are indented below them.
    """
    blocks, names, sources = [], [], []
    for line in credits_path.read_text().splitlines():
        if not line.strip():
            continue
        if line[0] in " \t":
            sources.append(line.strip())
        else:
            if sources:
                blocks.append((names, sources))
                names, sources = [], []
            names.append(line.strip())
    blocks.append((names, sources))
    return blocks


def scene_groups(frames, credits_path):
    """Scene group of every frame: union of the frames sharing a credits block or a source URL.

    Returns a dict frame -> group name (the name of one member of the group).
    """
    parent = {frame: frame for frame in frames}

    def find(frame):
        while parent[frame] != frame:
            parent[frame] = parent[parent[frame]]
            frame = parent[frame]
        return frame

    def union(a, b):
        parent[find(a)] = find(b)

    url_owner = {}
    for block_names, block_sources in parse_credits(credits_path):
        members = [name for name in block_names if name in parent]
        for member in members[1:]:
            union(members[0], member)
        for source in block_sources:
            if source.startswith("http") and members:
                if source in url_owner:
                    union(url_owner[source], members[0])
                url_owner[source] = members[0]
    return {frame: find(frame) for frame in frames}


def make_split(stats, seed):
    """Greedy group-aware split for one seed: a Series frame index -> 'train' / 'val' / 'test'.

    `stats` needs the columns frame, category and scene_group. Per category, groups are
    shuffled; a group goes to val or test only if it fits in the remaining room.
    """
    rng = random.Random(seed)
    assignment = {}
    for category in sorted(stats["category"].unique()):
        groups = stats[stats["category"] == category].groupby("scene_group")["frame"].apply(list).tolist()
        n = sum(len(g) for g in groups)
        target = {s: max(1, round(n * f)) if (s != "train" and n >= 3) else 0 for s, f in SPLIT_FRACTIONS.items()}
        target["train"] = n - target["val"] - target["test"]
        rng.shuffle(groups)
        count = dict.fromkeys(SPLIT_FRACTIONS, 0)
        for group in groups:
            room = {s: target[s] - count[s] for s in ("val", "test") if target[s] - count[s] >= len(group)}
            split = max(room, key=room.get) if room else "train"
            count[split] += len(group)
            for frame in group:
                assignment[frame] = split
    return stats["frame"].map(assignment)


def split_distance(stats, split):
    """How far the val and test sets are from the whole dataset (anomaly ratio and objects per image)."""
    log_ratio = np.log10(stats["anomaly_ratio"])
    distance = 0.0
    for name in ("val", "test"):
        selected = split == name
        distance += abs(log_ratio[selected].median() - log_ratio.median()) / log_ratio.std()
        distance += (abs(stats.loc[selected, "n_objects"].mean() - stats["n_objects"].mean())
                     / stats["n_objects"].std())
    return distance


def best_split(stats, seeds=SPLIT_SEEDS):
    """(split Series, seed, distance) of the most representative candidate split."""
    distance, seed = min((split_distance(stats, make_split(stats, s)), s) for s in seeds)
    return make_split(stats, seed), seed, distance


def verify_manifest(manifest_path=dp.MANIFEST_PATH):
    """Check the frozen manifest: sizes, disjoint frames and no scene group across splits.

    Returns the manifest as a DataFrame; raises AssertionError if a rule is broken.
    """
    manifest = pd.DataFrame(dp.read_manifest(manifest_path))
    sizes = manifest["split"].value_counts().to_dict()
    assert sizes == EXPECTED_SIZES, f"split sizes {sizes} != {EXPECTED_SIZES}"
    assert manifest["frame"].is_unique, "a frame appears twice in the manifest"
    leaks = manifest.groupby("scene_group")["split"].nunique()
    assert (leaks == 1).all(), f"scene groups in several splits: {list(leaks[leaks > 1].index)}"
    return manifest
