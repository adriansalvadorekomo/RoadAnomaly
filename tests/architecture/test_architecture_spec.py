"""Semantic guardrails for the committed Structurizr C4 model.

The checks read the DSL directly, so they fail when the model, documentation and
rendered PNGs drift apart on the rules that matter: evaluation-only data, a
normal-road selection path, a registry that keeps every candidate, and XAI as a
non-promoting gate.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict, deque
from pathlib import Path

import pytest
from PIL import Image

pytestmark = pytest.mark.architecture

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCH_DIR = REPO_ROOT / "docs" / "architecture"
DSL_PATH = ARCH_DIR / "workspace.dsl"
MANIFEST_PATH = ARCH_DIR / "diagrams" / "manifest.json"
README_PATH = REPO_ROOT / "README.md"

EDGE_RE = re.compile(
    r'^\s*([A-Za-z_]\w*)\s*->\s*([A-Za-z_]\w*)\s+"([^"]*)"',
    re.MULTILINE,
)
REQUIRED_VIEWS = {"c1-system-context", "c2-offline-pipeline"}


def _dsl() -> str:
    return DSL_PATH.read_text(encoding="utf-8")


def _graph() -> tuple[dict[str, set[str]], dict[tuple[str, str], str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    labels: dict[tuple[str, str], str] = {}
    for source, target, label in EDGE_RE.findall(_dsl()):
        graph[source].add(target)
        labels[(source, target)] = label
    return graph, labels


def _reachable(graph: dict[str, set[str]], start: str) -> set[str]:
    seen: set[str] = set()
    queue: deque[str] = deque([start])
    while queue:
        node = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        queue.extend(graph.get(node, set()) - seen)
    return seen


def test_two_c4_views_and_no_legacy_archify_assets() -> None:
    dsl = _dsl()
    assert dsl.count("systemContext roadAnomaly") == 1
    assert dsl.count("container roadAnomaly") == 1
    for view in REQUIRED_VIEWS:
        assert f'"{view}"' in dsl
    for tag in ("Element,Implemented", "Element,Planned", "Element,Template"):
        assert tag in dsl, f"C4 status tag missing: {tag}"

    obsolete = [
        ARCH_DIR / "architecture.json",
        ARCH_DIR / "architecture.html",
        REPO_ROOT / "assets" / "architecture.png",
        REPO_ROOT / "assets" / "architecture-dark.png",
    ]
    for path in obsolete:
        assert not path.exists(), f"legacy architecture asset remains: {path}"


def test_benchmark_and_xai_cannot_reach_training_or_registry() -> None:
    graph, _ = _graph()
    benchmark_reach = _reachable(graph, "benchmarkDataset")
    assert "benchmarkEvaluation" in benchmark_reach
    for forbidden in ("training", "selectionScorecard", "registry"):
        assert forbidden not in benchmark_reach, f"RoadAnomaly must not reach {forbidden}"

    assert "registry" not in _reachable(graph, "benchmarkEvaluation")
    assert "registry" not in _reachable(graph, "xai")


def test_selection_is_normal_road_and_registry_retains_all_three() -> None:
    dsl = _dsl()
    _, labels = _graph()
    assert ("normalRoadValidation", "selectionScorecard") in labels
    assert ("selectionScorecard", "registry") in labels
    assert "retains all three" in labels[("selectionScorecard", "registry")]
    assert "All three candidate SavedModels" in dsl
    assert "no RoadAnomaly number" in dsl


def test_xai_is_a_selected_non_promoting_gate() -> None:
    dsl = _dsl()
    assert "XAI evidence" in dsl
    assert "Seg-Grad-CAM" in dsl
    assert "Integrated Gradients" in dsl
    assert "reconstruction-error" in dsl.lower()

    adr = (REPO_ROOT / "docs" / "adr" / "0011-xai-methods-and-faithfulness.md").read_text(
        encoding="utf-8"
    )
    assert "methods selected; implementation not started" in adr
    matrix = (REPO_ROOT / "docs" / "validation" / "requirements-matrix.md").read_text(
        encoding="utf-8"
    )
    v18 = next(line for line in matrix.splitlines() if line.startswith("| V1.8 |"))
    assert "`in progress`" in v18


def test_metric_and_xai_contracts_are_recorded() -> None:
    metrics = (REPO_ROOT / "docs" / "metrics.md").read_text(encoding="utf-8")
    assert "F1 equals Dice" in metrics
    assert "AUPRO@30%" in metrics
    assert "HD95" in metrics
    assert "Boundary IoU" in metrics

    xai = (REPO_ROOT / "docs" / "xai.md").read_text(encoding="utf-8")
    assert "Seg-Grad-CAM" in xai
    assert "Integrated Gradients" in xai
    assert "deletion and insertion" in xai.lower()
    assert "pointing game" in xai.lower()


def test_manifest_matches_dsl_and_png_dimensions() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    digest = hashlib.sha256(DSL_PATH.read_bytes()).hexdigest()
    assert manifest["workspace_sha256"] == digest, "re-render after editing workspace.dsl"

    views = manifest["views"]
    assert set(views) == REQUIRED_VIEWS
    for key, entry in views.items():
        png = ARCH_DIR / "diagrams" / entry["file"]
        assert png.is_file(), f"missing rendered view: {png}"
        with Image.open(png) as image:
            assert image.size == (entry["width"], entry["height"]), (
                f"{key} is {image.size}, manifest says ({entry['width']}, {entry['height']})"
            )
            assert image.width >= 1200 and image.height >= 600


def test_readme_embeds_c4_and_architecture_docs_are_textual() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    assert "docs/architecture/diagrams/c1-system-context.png" in readme
    assert "docs/architecture/diagrams/c2-offline-pipeline.png" in readme
    for stale in ("architecture.json", "architecture.html", "assets/architecture", "archify"):
        assert stale not in readme, f"README still references removed artifact: {stale}"

    architecture = (ARCH_DIR / "README.md").read_text(encoding="utf-8")
    for stale in ("architecture.json", "architecture.html", "assets/architecture", "archify"):
        assert stale not in architecture, (
            f"architecture README still references removed artifact: {stale}"
        )
    assert "| 1. Business understanding |" in architecture
    assert "```mermaid" not in architecture
