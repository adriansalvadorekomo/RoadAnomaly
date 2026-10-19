"""Semantic guardrails for the committed architecture map.

These checks do not need archify. They fail if the diagram, docs and PNG assets
drift apart on the rules that matter most: six CRISP-DM regions, no promotion
from RoadAnomaly, an explicit XAI gate and a registry that keeps every candidate.
"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

pytestmark = pytest.mark.architecture

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO_ROOT / "docs" / "architecture" / "architecture.json"
LIGHT_PNG = REPO_ROOT / "assets" / "architecture.png"
DARK_PNG = REPO_ROOT / "assets" / "architecture-dark.png"

REQUIRED_REGION_PREFIXES = {
    "1 · Business understanding",
    "2 · Data understanding",
    "3 · Data preparation",
    "4 · Modeling",
    "5 · Evaluation",
    "6 · Deployment",
}


def _spec() -> dict[str, Any]:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def _component_ids(spec: dict[str, Any]) -> set[str]:
    return {component["id"] for component in spec["components"]}


def _adjacency(spec: dict[str, Any]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for connection in spec["connections"]:
        graph[connection["from"]].add(connection["to"])
    return graph


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


def test_spec_structure_and_edges_are_consistent() -> None:
    spec = _spec()
    assert spec["diagram_type"] == "architecture"
    assert spec["schema_version"] == 1

    ids = [component["id"] for component in spec["components"]]
    assert len(ids) == len(set(ids)), f"duplicate component ids: {ids}"

    known = set(ids)
    for connection in spec["connections"]:
        assert connection["from"] in known, f"unknown source: {connection['from']}"
        assert connection["to"] in known, f"unknown target: {connection['to']}"
        assert connection["from"] != connection["to"], "self-loop in the system map"

    for boundary in spec["boundaries"]:
        assert set(boundary["wraps"]) <= known, f"unknown wrapped node: {boundary['wraps']}"


def test_six_crisp_dm_regions_are_present() -> None:
    labels = [boundary["label"] for boundary in _spec()["boundaries"]]
    for prefix in REQUIRED_REGION_PREFIXES:
        assert any(label.startswith(prefix) for label in labels), f"missing region: {prefix}"
    assert len(labels) == 6, f"expected six CRISP-DM regions, found {len(labels)}"


def test_roadanomaly_and_xai_cannot_reach_the_registry() -> None:
    spec = _spec()
    graph = _adjacency(spec)
    assert "registry" in _reachable(graph, "validation"), "selection must feed the registry"
    assert "registry" not in _reachable(graph, "bench_eval"), (
        "RoadAnomaly evaluation must never promote a model"
    )
    assert "registry" not in _reachable(graph, "xai"), "XAI must never promote a model"

    direct = {(c["from"], c["to"]) for c in spec["connections"]}
    assert ("bench_eval", "registry") not in direct
    assert ("xai", "registry") not in direct


def test_selection_is_normal_road_and_registry_keeps_every_candidate() -> None:
    spec = _spec()
    components = {component["id"]: component for component in spec["components"]}
    validation = components["validation"]
    registry = components["registry"]

    assert "validation" in validation["label"].lower()
    assert "never benchmark" in validation.get("tag", "").lower()
    assert "3 savedmodels" in registry["sublabel"].lower()
    assert "alias" in registry["sublabel"].lower()

    selection_edges = [
        connection
        for connection in spec["connections"]
        if connection["from"] == "validation" and connection["to"] == "registry"
    ]
    assert selection_edges, "validation -> registry edge is missing"
    assert "retain all 3" in selection_edges[0].get("label", "").lower()


def test_xai_is_an_explicit_blocked_gate() -> None:
    spec = _spec()
    components = {component["id"]: component for component in spec["components"]}
    xai = components["xai"]
    assert "xai" in xai["label"].lower()
    assert "g1" in xai.get("tag", "").lower()

    edges = {(c["from"], c["to"]) for c in spec["connections"]}
    assert ("validation", "xai") in edges, "XAI must consume the selected model"
    assert ("xai", "prototype") in edges, "XAI explanations belong in the prototype"


def test_png_assets_match_the_two_x_export() -> None:
    spec = _spec()
    width, height = spec["meta"]["viewBox"]
    for path in (LIGHT_PNG, DARK_PNG):
        assert path.is_file(), f"missing architecture asset: {path}"
        with Image.open(path) as image:
            assert image.size == (width * 2, height * 2), (
                f"{path.name} is {image.size}, expected {(width * 2, height * 2)}"
            )
