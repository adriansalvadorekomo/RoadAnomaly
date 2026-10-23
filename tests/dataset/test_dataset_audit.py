"""Contract tests for the read-only RoadAnomaly dataset audit.

These tests exercise the accepted local baseline, schema validation, the
JSON-derived report, failure exits and output policy. They never write to
``data/`` or to the canonical ``docs/validation`` pair.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import jsonschema
import numpy as np
import pytest
from PIL import Image

from dl.data import audit

pytestmark = pytest.mark.dataset

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data"
SCHEMA_PATH = (
    REPO_ROOT / "specs" / "003-dataset-understanding" / "contracts" / "audit-summary.schema.json"
)
CANONICAL_JSON = REPO_ROOT / "docs" / "validation" / "roadanomaly-eda.json"
CANONICAL_REPORT = REPO_ROOT / "docs" / "validation" / "roadanomaly-eda.md"

EXPECTED_BELOW_ONE_PERCENT = [
    "animals02_Zagori_On_the_road_to_Papigko.webp",
    "animals11_Cock_Pheasant_on_Romford_Road.webp",
    "lost_tires03.webp",
    "lost_tires08.webp",
    "lost_tires09.webp",
    "obstacles12_rocks2.webp",
]
EXPECTED_SOURCE_GROUPS = {
    frozenset(
        {
            "lost_tires03.webp",
            "lost_tires08.webp",
            "lost_tires09.webp",
        }
    ),
    frozenset({"cones07.webp", "cones08_can.webp"}),
    frozenset(
        {
            "obstacles03_cardboard_czech_hedgehog.webp",
            "obstacles04_cardboard_czech_hedgehog.webp",
            "obstacles05_cardboard_czech_hedgehog.webp",
            "obstacles06_cardboard_czech_hedgehog.webp",
        }
    ),
    frozenset(
        {
            "obstacles12_rocks2.webp",
            "obstacles12_rocks4.webp",
            "obstacles12_rocks5.webp",
            "obstacles12_rocks6.webp",
        }
    ),
}
ALLOWED_EVIDENCE = {"computed_local", "documented_local", "upstream_unverified", "unresolved"}


@pytest.fixture(scope="module")
def audit_summary() -> audit.AuditResult:
    assert DATA_ROOT.is_dir(), f"tracked dataset is missing at {DATA_ROOT}"
    return audit.compute_audit(DATA_ROOT)


@pytest.fixture(scope="module")
def json_bytes(audit_summary: audit.AuditResult) -> bytes:
    payload = audit.serialize_summary(audit_summary)
    audit.validate_summary(audit_summary)
    return payload


@pytest.fixture(scope="module")
def summary_digest(json_bytes: bytes) -> str:
    return hashlib.sha256(json_bytes).hexdigest()


@pytest.fixture(scope="module")
def report_text(summary_digest: str, json_bytes: bytes) -> str:
    payload = json.loads(json_bytes)
    return audit.render_report(payload, summary_digest)


def _snapshot(paths: tuple[Path, ...]) -> dict[Path, str | None]:
    return {
        path: hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        for path in paths
    }


def _copy_data(tmp_path: Path) -> Path:
    destination = tmp_path / "data"
    shutil.copytree(DATA_ROOT, destination)
    return destination


def _new_output_root(tmp_path: Path) -> Path:
    root = tmp_path / "output"
    root.mkdir(parents=True)
    return root


def _instance_frame_names() -> list[str]:
    names = json.loads((DATA_ROOT / "frame_list.json").read_text(encoding="utf-8"))
    return [
        name
        for name in names
        if (DATA_ROOT / "frames" / f"{Path(name).stem}.labels" / "index.json").is_file()
    ]


def _independent_mapping() -> tuple[list[str], set[tuple[str, int, int, int]]]:
    disagreeing: list[str] = []
    mismatches: set[tuple[str, int, int, int]] = set()
    for name in _instance_frame_names():
        label_dir = DATA_ROOT / "frames" / f"{Path(name).stem}.labels"
        instances = json.loads((label_dir / "index.json").read_text(encoding="utf-8"))["instances"]
        frame_bad = False
        for position, item in enumerate(instances, start=1):
            if int(item["id"]) != position:
                frame_bad = True
                mismatches.add((name, position, position, int(item["id"])))
        if frame_bad:
            disagreeing.append(name)
    return sorted(disagreeing), mismatches


def _independent_roi_findings() -> tuple[set[tuple[str, int]], set[tuple[str, int]], int]:
    out_of_bounds: set[tuple[str, int]] = set()
    non_tight: set[tuple[str, int]] = set()
    centroids_inside = 0
    for name in _instance_frame_names():
        label_dir = DATA_ROOT / "frames" / f"{Path(name).stem}.labels"
        instances = json.loads((label_dir / "index.json").read_text(encoding="utf-8"))["instances"]
        mask = np.asarray(Image.open(label_dir / "labels_instance.png"))
        for value, item in enumerate(instances, start=1):
            x0, y0, x1, y1 = (int(v) for point in item["roi_rect"] for v in point)
            if x0 < 0 or y0 < 0 or x1 > audit.FRAME_WIDTH or y1 > audit.FRAME_HEIGHT:
                out_of_bounds.add((name, value))
            pixels = np.argwhere(mask == value)
            by0, bx0 = int(pixels[:, 0].min()), int(pixels[:, 1].min())
            by1, bx1 = int(pixels[:, 0].max()), int(pixels[:, 1].max())
            if bx0 < x0 or by0 < y0 or bx1 >= x1 or by1 >= y1:
                non_tight.add((name, value))
            cx = (bx0 + bx1) / 2
            cy = (by0 + by1) / 2
            if 0 <= cx < audit.FRAME_WIDTH and 0 <= cy < audit.FRAME_HEIGHT:
                centroids_inside += 1
    return out_of_bounds, non_tight, centroids_inside


def test_schema_meta_validation_and_sixteen_root_fields() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(audit.AUDIT_ROOT_FIELDS)
    assert len(schema["required"]) == 16


def test_summary_is_complete_schema_valid_and_deterministic(
    audit_summary: audit.AuditResult, json_bytes: bytes
) -> None:
    assert tuple(audit_summary) == audit.AUDIT_ROOT_FIELDS
    audit.validate_summary(audit_summary)
    assert json_bytes.endswith(b"\n")
    assert json_bytes.count(b"\n") > 1
    assert json_bytes == audit.serialize_summary(audit_summary)
    decoded = json_bytes.decode("utf-8")
    assert str(REPO_ROOT) not in decoded
    assert "report_sha256" not in decoded
    assert "report_hash" not in decoded

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for extension in ("outputs", "visual_review", "readiness", "overlays", "figures"):
        invalid = deepcopy(cast(dict[str, Any], audit_summary))
        invalid[extension] = {}
        assert list(validator.iter_errors(invalid)), f"schema accepted extension field {extension}"


def test_incomplete_or_placeholder_result_is_rejected(audit_summary: audit.AuditResult) -> None:
    incomplete = deepcopy(cast(dict[str, Any], audit_summary))
    del incomplete["claims"]
    with pytest.raises(audit.AuditContractError):
        audit.serialize_summary(cast(audit.AuditResult, incomplete))

    placeholder = deepcopy(cast(dict[str, Any], audit_summary))
    placeholder["environment"]["python"] = "TODO"
    with pytest.raises(audit.AuditContractError):
        audit.serialize_summary(cast(audit.AuditResult, placeholder))

    nullable = deepcopy(cast(dict[str, Any], audit_summary))
    nullable["environment"]["python"] = None
    with pytest.raises(audit.AuditContractError):
        audit.serialize_summary(cast(audit.AuditResult, nullable))


def test_fingerprint_baseline(audit_summary: audit.AuditResult) -> None:
    fingerprint = audit_summary["fingerprint"]
    assert fingerprint["historical"] == audit.HISTORICAL_FINGERPRINT
    assert fingerprint["computed"] == audit.HISTORICAL_FINGERPRINT
    assert fingerprint["historical_file_count"] == 677
    assert fingerprint["historical_total_bytes"] == 13_135_474
    assert fingerprint["current_file_count"] == 677
    assert fingerprint["current_total_bytes"] == 13_135_474
    assert fingerprint["matches"] is True
    assert fingerprint["status"] == "match"
    assert fingerprint["provenance"] == "local_reconstruction"
    assert fingerprint["recipe"] == audit.FINGERPRINT_RECIPE


def test_inventory_and_annotation_integrity(audit_summary: audit.AuditResult) -> None:
    inventory = audit_summary["inventory"]
    assert inventory["frame_list_count"] == 60
    assert inventory["frame_count"] == 60
    assert inventory["label_dir_count"] == 60
    assert inventory["instance_frame_count"] == 46
    assert inventory["semantic_only_frame_count"] == 14
    assert len(inventory["frames"]) == 60
    kinds = [frame["annotation_kind"] for frame in inventory["frames"]]
    assert kinds.count("instance") == 46
    assert kinds.count("semantic_only") == 14
    assert sum(1 for frame in inventory["frames"] if frame["annotation_kind"] == "instance") == 46
    for frame in inventory["frames"]:
        assert frame["width"] == 1280
        assert frame["height"] == 720
        assert frame["mode"] == "RGB"
        assert frame["frame_name"].endswith(".webp")
        assert frame["frame_path"] == f"frames/{frame['frame_name']}"
        assert frame["label_dir"].endswith(".labels")
        assert len(frame["frame_sha256"]) == 64
    integrity = inventory["annotation_integrity"]
    assert integrity["semantic_values"] == [0, 2]
    assert integrity["colour_mapping"] == {"normal": [0, 0, 0], "anomaly": [255, 69, 0]}
    assert integrity["colour_mapping_valid"] is True
    assert integrity["instance_class_id"] == 2
    assert integrity["instance_ids_contiguous"] is True
    assert integrity["label_files_complete"] is True
    assert integrity["frame_decodable"] is True


def test_instance_semantic_invariant(audit_summary: audit.AuditResult) -> None:
    record = audit_summary["instance_semantic"]
    assert record["frames_checked"] == 46
    assert record["frames_exact_match"] == 46
    assert record["frames_mismatched"] == 0
    assert record["mismatched_frames"] == []
    assert record["extra_instance_pixels"] == 0
    assert record["missing_instance_pixels"] == 0
    assert record["semantic_only_frames_excluded"] == 14
    assert (
        record["definition"]
        == "union(instance values 1..N) == semantic value 2, per instance frame"
    )


def test_coverage_baseline_and_definitions(audit_summary: audit.AuditResult) -> None:
    coverage = audit_summary["coverage"]
    assert coverage["total_anomaly_pixels"] == 5_446_413
    assert coverage["total_pixels"] == 55_296_000
    assert coverage["pooled_fraction"] == 0.09849561
    assert coverage["pooled_percent"] == 9.849561
    assert coverage["minimum_percent"] == 0.374674
    assert coverage["maximum_percent"] == 42.328559
    assert coverage["median_percent"] == 6.622938
    assert coverage["below_one_percent"] == EXPECTED_BELOW_ONE_PERCENT
    assert len(coverage["per_frame"]) == 60
    assert set(coverage["definitions"]) == {
        "pooled_fraction",
        "per_frame_fraction",
        "percent",
        "median",
        "below_one_percent",
    }
    assert all(coverage["definitions"].values())
    assert sum(row["anomaly_pixels"] for row in coverage["per_frame"]) == 5_446_413
    assert all(row["total_pixels"] == 921_600 for row in coverage["per_frame"])


def test_categories_and_object_scale(audit_summary: audit.AuditResult) -> None:
    categories = audit_summary["categories"]
    assert categories["counts"] == {
        "animals": 31,
        "obstacles": 15,
        "cones": 8,
        "lost_tires": 3,
        "vehicle": 3,
    }
    assert categories["total_frames"] == 60
    assert categories["classification"] == "object_category_not_scene"

    scale = audit_summary["object_scale"]
    assert scale["roi_area_below_1024"] == 35
    assert scale["both_dimensions_below_32"] == 20
    assert scale["either_dimension_below_32"] == 46
    assert scale["median_roi_equivalent_square_px"] == 86.7
    assert scale["median_roi_width_px"] == 85.0
    assert scale["median_roi_height_px"] == 107.0
    assert scale["median_mask_equivalent_square_px"] == 51.2
    assert scale["denominator"] == 201
    assert set(scale["definitions"]) == {
        "roi_area",
        "both_dimensions_below_32",
        "either_dimension_below_32",
        "roi_equivalent_square",
        "roi_bounding_box",
        "mask_equivalent_square",
    }
    assert all(scale["definitions"].values())


def test_instance_mapping_lists_are_complete(audit_summary: audit.AuditResult) -> None:
    mapping = audit_summary["instance_mapping"]
    assert mapping["frames_checked"] == 46
    assert mapping["frames_agreeing"] == 35
    assert mapping["frames_disagreeing"] == 11
    expected_frames, expected_mismatches = _independent_mapping()
    assert mapping["disagreeing_frames"] == expected_frames
    assert len(mapping["disagreeing_frames"]) == 11
    assert {
        (row["frame_name"], row["mask_value"], row["index_position"], row["index_id"])
        for row in mapping["mismatches"]
    } == expected_mismatches
    assert len(mapping["mismatches"]) == 48
    assert mapping["existing_test_check"] == {
        "name": "max(mask) == len(instances)",
        "passes": True,
    }


def test_roi_lists_are_complete_and_match_definitions(audit_summary: audit.AuditResult) -> None:
    roi = audit_summary["roi"]
    expected_oob, expected_non_tight, expected_centroids = _independent_roi_findings()
    assert roi["instances_checked"] == 201
    assert roi["out_of_bounds"] == 11
    assert roi["non_tight"] == 17
    assert roi["centroids_inside"] == 201
    assert roi["centroids_inside"] == expected_centroids
    assert {
        (row["frame_name"], row["mask_value"]) for row in roi["out_of_bounds_instances"]
    } == expected_oob
    assert {
        (row["frame_name"], row["mask_value"]) for row in roi["non_tight_instances"]
    } == expected_non_tight
    assert len(roi["out_of_bounds_instances"]) == 11
    assert len(roi["non_tight_instances"]) == 17
    assert set(roi["definitions"]) == {"out_of_bounds", "non_tight", "centroid_containment"}
    assert all(roi["definitions"].values())


def test_duplicates_are_method_limited(audit_summary: audit.AuditResult) -> None:
    duplicates = audit_summary["duplicates"]
    assert duplicates["exact_pairs"] == []
    assert duplicates["decoded_pairs"] == []
    assert duplicates["dhash_pairs"] == []
    assert duplicates["dhash_method"] == audit.DHASH_METHOD
    assert len(duplicates["limitations"]) >= 3
    limitations = " ".join(duplicates["limitations"]).lower()
    assert "method-limited" in limitations
    assert "not proof" in limitations


def test_credits_licensing_and_source_groups(audit_summary: audit.AuditResult) -> None:
    credits = audit_summary["credits"]
    assert credits["coverage"] == 60
    assert len(credits["entries"]) == 60
    assert credits["missing_entries"] == []
    assert len(credits["missing_licence_tokens"]) == 24
    assert credits["missing_licence_tokens"] == sorted(credits["missing_licence_tokens"])
    assert credits["missing_source_urls"] == [
        "obstacles12_rocks2.webp",
        "obstacles12_rocks4.webp",
        "obstacles12_rocks5.webp",
        "obstacles12_rocks6.webp",
    ]
    assert len(credits["source_groups"]) == 4
    assert {
        frozenset(group["frames"]) for group in credits["source_groups"]
    } == EXPECTED_SOURCE_GROUPS
    assert sum(group["frame_count"] for group in credits["source_groups"]) == 13
    assert sum(1 for group in credits["source_groups"] if group["source_url"] is None) == 1
    assert all(group["frame_count"] == len(group["frames"]) for group in credits["source_groups"])

    entries = {entry["frame_name"]: entry for entry in credits["entries"]}
    assert entries["animals01_Guiguinto_railway_station_Calves.webp"]["licence_tokens"] == ["CC0"]
    assert entries["animals28.webp"]["licence_tokens"] == []
    animals13_url = entries["animals13_jeune_bovin_sur_la_route.webp"]["source_url"]
    assert animals13_url is not None
    assert animals13_url.startswith("https://commons.wikimedia.org/")
    assert entries["lost_tires03.webp"]["source_url"] == (
        "https://www.youtube.com/watch?v=2ysuwejHZEg"
    )
    for entry in credits["entries"]:
        if entry["source_url"] is not None:
            assert "creativecommons.org" not in entry["source_url"]
        assert entry["credit_text"]
        assert entry["attribution"]

    assert credits["annotation_licence_claim"] == "CC BY-SA 4.0"
    assert "data/credits.txt" in credits["annotation_licence_sources"]
    assert "docs/dataset.md" in credits["annotation_licence_sources"]
    assert credits["annotation_licence_terms_url"] == audit.ANNOTATION_LICENCE_TERMS_URL
    assert credits["code_licence"] == "MIT"
    assert credits["code_licence_source"] == "LICENSE"
    assert credits["code_licence_scope"] == "source code; data and annotations excluded"
    assert credits["legal_conclusion"] == "not_made"


def test_provenance_claims_limitations_and_open_items(audit_summary: audit.AuditResult) -> None:
    provenance = audit_summary["provenance"]
    assert "Lis et al." in provenance["citation"]
    assert "ICCV 2019" in provenance["citation"]
    assert provenance["release_identifier"] is None
    assert provenance["upstream_status"] == "upstream_unverified"
    assert provenance["scene_identity"] == "unresolved"
    assert provenance["filename_prefix_is_scene_id"] is False
    assert provenance["local_attribution_is_redistribution_proof"] is False
    assert provenance["normal_road_source_selected"] is False
    assert provenance["p0_status"] == {
        "P0-1": "open",
        "P0-2": "open",
        "P0-3": "open",
        "P0-4": "open",
    }
    assert provenance["g10_status"] == "open"
    assert any(
        item["item_id"] == "adr-0010-threshold-contradiction"
        and item["evidence_class"] == "unresolved"
        and item["status"] == "open"
        for item in provenance["unresolved_items"]
    )

    claims = audit_summary["claims"]
    assert len(claims) >= 15
    assert len({claim["claim_id"] for claim in claims}) == len(claims)
    assert all(claim["evidence_class"] in ALLOWED_EVIDENCE for claim in claims)
    assert all(claim["text"] for claim in claims)
    assert all("value" in claim for claim in claims)
    assert {
        "fingerprint.match",
        "inventory.counts",
        "coverage.pooled",
        "credits.source_groups",
        "provenance.adr0010",
    } <= {claim["claim_id"] for claim in claims}

    documented = audit_summary["documented_claims"]
    assert {claim["claim_id"] for claim in documented} == {
        "coverage-rounding",
        "object-scale-87x87",
        "scene-prefix-grouping",
        "per-image-licence-completeness",
        "benchmark-scene-folds",
        "instance-id-equality",
    }
    assert {claim["treatment"] for claim in documented} <= {
        "report_both",
        "report_gap",
        "mark_unresolved",
    }
    assert all(claim["computed_value"] for claim in documented)
    assert all(claim["computed_definition"] for claim in documented)

    limitations = audit_summary["limitations"]
    assert len(limitations) >= 5
    assert len({item["limitation_id"] for item in limitations}) == len(limitations)
    assert all(item["evidence_class"] in ALLOWED_EVIDENCE for item in limitations)
    limitation_ids = {item["limitation_id"] for item in limitations}
    assert "visual-registration-unverified" in limitation_ids
    assert "duplicates-method-limited" in limitation_ids
    assert "upstream-provenance-unverified" in limitation_ids


def test_report_has_ten_sections_digest_and_complete_parity(
    audit_summary: audit.AuditResult, report_text: str, summary_digest: str
) -> None:
    headings = [line for line in report_text.splitlines() if line.startswith("## ")]
    assert tuple(headings) == audit.REPORT_HEADINGS
    assert len(headings) == 10
    assert f"Source JSON SHA-256: `{summary_digest}`" in report_text
    assert str(REPO_ROOT) not in report_text
    assert "report_sha256" not in report_text
    assert "report_hash" not in report_text
    assert "9.849561" in report_text
    assert "0.374674" in report_text
    assert "42.328559" in report_text
    assert "6.622938" in report_text
    assert "86.7" in report_text
    assert "85.0" in report_text
    assert "107.0" in report_text
    assert "51.2" in report_text
    assert "CC BY-SA 4.0" in report_text
    assert "MIT" in report_text
    assert "not_made" in report_text
    assert "adr-0010-threshold-contradiction" in report_text
    assert "P0-1" in report_text
    assert "G10" in report_text
    assert "not assessed" in report_text
    assert "No class map, split, split hash, manifest" in report_text

    for claim in audit_summary["claims"]:
        assert claim["claim_id"] in report_text
    for documented in audit_summary["documented_claims"]:
        assert documented["claim_id"] in report_text
        assert documented["treatment"] in report_text
    for item in audit_summary["provenance"]["unresolved_items"]:
        assert item["item_id"] in report_text

    for row in audit_summary["instance_mapping"]["mismatches"]:
        assert (
            f"| {row['frame_name']} | {row['mask_value']} | "
            f"{row['index_position']} | {row['index_id']} | computed_local |"
        ) in report_text
    for affected in audit_summary["roi"]["out_of_bounds_instances"]:
        assert (
            f"| {affected['frame_name']} | {affected['mask_value']} | computed_local |"
            in report_text
        )
    for affected in audit_summary["roi"]["non_tight_instances"]:
        assert (
            f"| {affected['frame_name']} | {affected['mask_value']} | computed_local |"
            in report_text
        )
    for entry in audit_summary["credits"]["entries"]:
        assert f"| {entry['frame_name']} |" in report_text

    assert report_text == audit.render_report(
        json.loads(audit.serialize_summary(audit_summary)), summary_digest
    )


def test_generate_and_check_temporary_root(tmp_path: Path) -> None:
    output_root = _new_output_root(tmp_path)
    canonical_before = _snapshot((CANONICAL_JSON, CANONICAL_REPORT))

    assert audit.main(["--output-root", str(output_root)]) == 0
    assert audit.main(["--output-root", str(output_root)]) == 0

    files = sorted(path.name for path in output_root.iterdir())
    assert files == [audit.JSON_NAME, audit.REPORT_NAME]
    json_path = output_root / audit.JSON_NAME
    report_path = output_root / audit.REPORT_NAME
    payload_bytes = json_path.read_bytes()
    payload = json.loads(payload_bytes)
    audit.validate_summary(payload)
    assert payload["environment"]["command"] == "make data-audit"
    assert payload["fingerprint"]["status"] == "match"
    digest = hashlib.sha256(payload_bytes).hexdigest()
    assert digest in report_path.read_text(encoding="utf-8")
    assert report_path.read_text(encoding="utf-8") == audit.render_report(payload, digest)
    assert not (output_root / f"{audit.JSON_NAME}{audit.TEMP_SUFFIX}").exists()
    assert not (output_root / f"{audit.REPORT_NAME}{audit.TEMP_SUFFIX}").exists()
    assert _snapshot((CANONICAL_JSON, CANONICAL_REPORT)) == canonical_before

    first = _snapshot((json_path, report_path))
    assert audit.main(["--output-root", str(output_root)]) == 0
    assert _snapshot((json_path, report_path)) == first
    assert audit.main(["--check", "--output-root", str(output_root)]) == 0
    assert _snapshot((json_path, report_path)) == first
    assert sorted(path.name for path in output_root.iterdir()) == files


def test_output_policy_rejects_wrong_missing_and_traversal_roots(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    assert audit.main(["--output-root", str(missing)]) == audit.EXIT_CONTRACT_ERROR
    assert not missing.exists()

    assert audit.main(["--output-root", str(REPO_ROOT / "docs")]) == audit.EXIT_OUTPUT_POLICY_ERROR
    traversal = tmp_path / "output" / ".."
    assert audit.main(["--output-root", str(traversal)]) == audit.EXIT_OUTPUT_POLICY_ERROR


def test_output_policy_rejects_symlink_escape_and_target_symlink(tmp_path: Path) -> None:
    repo_link_root = REPO_ROOT / f".audit-policy-{uuid.uuid4().hex}"
    outside = tmp_path / "outside"
    outside.mkdir()
    repo_link_root.mkdir()
    link = repo_link_root / "link"
    link.symlink_to(outside, target_is_directory=True)
    try:
        assert audit.main(["--output-root", str(link)]) == audit.EXIT_OUTPUT_POLICY_ERROR
    finally:
        link.unlink(missing_ok=True)
        repo_link_root.rmdir()

    output_root = _new_output_root(tmp_path)
    target = tmp_path / "target.txt"
    target.write_text("untouched", encoding="utf-8")
    (output_root / audit.JSON_NAME).symlink_to(target)
    assert audit.main(["--output-root", str(output_root)]) == audit.EXIT_OUTPUT_POLICY_ERROR
    assert target.read_text(encoding="utf-8") == "untouched"


def test_fingerprint_drift_exits_two_with_no_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data_copy = _copy_data(tmp_path)
    (data_copy / "temporary-drift.txt").write_text("drift\n", encoding="utf-8")
    output_root = _new_output_root(tmp_path)
    assert (
        audit.main(["--data-root", str(data_copy), "--output-root", str(output_root)])
        == audit.EXIT_DATA_ERROR
    )
    error = capsys.readouterr().err
    assert "fingerprint mismatch" in error
    assert audit.HISTORICAL_FINGERPRINT in error
    assert "677 files" in error
    assert list(output_root.iterdir()) == []


def test_missing_corrupt_and_invalid_inputs_exit_two_with_no_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing_copy = _copy_data(tmp_path / "missing")
    first_name = json.loads((missing_copy / "frame_list.json").read_text(encoding="utf-8"))[0]
    (missing_copy / "frames" / first_name).unlink()
    missing_output = _new_output_root(tmp_path / "missing")
    assert (
        audit.main(["--data-root", str(missing_copy), "--output-root", str(missing_output)])
        == audit.EXIT_DATA_ERROR
    )
    assert first_name in capsys.readouterr().err
    assert list(missing_output.iterdir()) == []

    corrupt_copy = _copy_data(tmp_path / "corrupt")
    (corrupt_copy / "frames" / first_name).write_bytes(b"not a webp")
    corrupt_output = _new_output_root(tmp_path / "corrupt")
    assert (
        audit.main(["--data-root", str(corrupt_copy), "--output-root", str(corrupt_output)])
        == audit.EXIT_DATA_ERROR
    )
    assert first_name in capsys.readouterr().err
    assert list(corrupt_output.iterdir()) == []

    invalid_copy = _copy_data(tmp_path / "invalid")
    semantic_path = (
        invalid_copy / "frames" / f"{Path(first_name).stem}.labels" / "labels_semantic.png"
    )
    with Image.open(semantic_path) as image:
        semantic = np.asarray(image).copy()
    semantic[0, 0] = 1
    Image.fromarray(semantic).save(semantic_path)
    invalid_output = _new_output_root(tmp_path / "invalid")
    assert (
        audit.main(["--data-root", str(invalid_copy), "--output-root", str(invalid_output)])
        == audit.EXIT_DATA_ERROR
    )
    assert "semantic values" in capsys.readouterr().err
    assert list(invalid_output.iterdir()) == []


def test_instance_semantic_mismatch_exits_two_and_does_not_modify_mask(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data_copy = _copy_data(tmp_path)
    frame_name = _instance_frame_names()[0]
    label_dir = data_copy / "frames" / f"{Path(frame_name).stem}.labels"
    instance_path = label_dir / "labels_instance.png"
    semantic_path = label_dir / "labels_semantic.png"
    instance = np.asarray(Image.open(instance_path)).copy()
    semantic = np.asarray(Image.open(semantic_path))
    candidates = np.argwhere((instance == 0) & (semantic == 0))
    assert candidates.size > 0
    y, x = (int(value) for value in candidates[0])
    instance[y, x] = 1
    Image.fromarray(instance).save(instance_path)
    before = hashlib.sha256(instance_path.read_bytes()).hexdigest()

    output_root = _new_output_root(tmp_path)
    assert (
        audit.main(["--data-root", str(data_copy), "--output-root", str(output_root)])
        == audit.EXIT_DATA_ERROR
    )
    error = capsys.readouterr().err
    assert "instance/semantic invariant failed" in error
    assert frame_name in error
    assert "extra=1" in error
    assert "missing=0" in error
    assert hashlib.sha256(instance_path.read_bytes()).hexdigest() == before
    assert list(output_root.iterdir()) == []


def test_schema_render_and_write_failures_exit_three_before_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_root = _new_output_root(tmp_path)
    assert audit.main(["--output-root", str(output_root)]) == 0
    pair_before = _snapshot((output_root / audit.JSON_NAME, output_root / audit.REPORT_NAME))

    def fail_validate(summary: object) -> None:
        raise audit.AuditContractError("simulated schema validation failure")

    monkeypatch.setattr(audit, "validate_summary", fail_validate)
    assert audit.main(["--output-root", str(output_root)]) == audit.EXIT_CONTRACT_ERROR
    assert (
        _snapshot((output_root / audit.JSON_NAME, output_root / audit.REPORT_NAME)) == pair_before
    )
    assert not (output_root / f"{audit.JSON_NAME}{audit.TEMP_SUFFIX}").exists()
    assert not (output_root / f"{audit.REPORT_NAME}{audit.TEMP_SUFFIX}").exists()
    monkeypatch.undo()

    def fail_render(summary: object, digest: str) -> str:
        raise audit.AuditContractError("simulated render failure")

    monkeypatch.setattr(audit, "render_report", fail_render)
    assert audit.main(["--output-root", str(output_root)]) == audit.EXIT_CONTRACT_ERROR
    assert (
        _snapshot((output_root / audit.JSON_NAME, output_root / audit.REPORT_NAME)) == pair_before
    )
    assert not (output_root / f"{audit.JSON_NAME}{audit.TEMP_SUFFIX}").exists()
    assert not (output_root / f"{audit.REPORT_NAME}{audit.TEMP_SUFFIX}").exists()
    monkeypatch.undo()

    real_write_temp = audit._write_temp
    calls = {"count": 0}

    def fail_second_temp(path: Path, payload: bytes) -> None:
        calls["count"] += 1
        if calls["count"] == 2:
            raise audit.AuditContractError("simulated write failure")
        real_write_temp(path, payload)

    monkeypatch.setattr(audit, "_write_temp", fail_second_temp)
    assert audit.main(["--output-root", str(output_root)]) == audit.EXIT_CONTRACT_ERROR
    assert calls["count"] == 2
    assert (
        _snapshot((output_root / audit.JSON_NAME, output_root / audit.REPORT_NAME)) == pair_before
    )
    assert not (output_root / f"{audit.JSON_NAME}{audit.TEMP_SUFFIX}").exists()
    assert not (output_root / f"{audit.REPORT_NAME}{audit.TEMP_SUFFIX}").exists()


def test_normal_failure_preserves_previous_pair_and_removes_temps(
    tmp_path: Path,
) -> None:
    output_root = _new_output_root(tmp_path)
    assert audit.main(["--output-root", str(output_root)]) == 0
    pair_before = _snapshot((output_root / audit.JSON_NAME, output_root / audit.REPORT_NAME))

    data_copy = _copy_data(tmp_path)
    (data_copy / "drift.txt").write_text("drift\n", encoding="utf-8")
    assert (
        audit.main(["--data-root", str(data_copy), "--output-root", str(output_root)])
        == audit.EXIT_DATA_ERROR
    )
    assert (
        _snapshot((output_root / audit.JSON_NAME, output_root / audit.REPORT_NAME)) == pair_before
    )
    assert not (output_root / f"{audit.JSON_NAME}{audit.TEMP_SUFFIX}").exists()
    assert not (output_root / f"{audit.REPORT_NAME}{audit.TEMP_SUFFIX}").exists()


def test_second_replacement_failure_exits_three_and_cleans_temps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_root = _new_output_root(tmp_path)
    assert audit.main(["--output-root", str(output_root)]) == 0
    real_replace = audit.os.replace
    calls = {"count": 0}

    def fail_second(source: str | Path, destination: str | Path) -> None:
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("simulated second replacement failure")
        real_replace(source, destination)

    monkeypatch.setattr(audit.os, "replace", fail_second)
    assert audit.main(["--output-root", str(output_root)]) == audit.EXIT_CONTRACT_ERROR
    assert calls["count"] == 2
    assert not (output_root / f"{audit.JSON_NAME}{audit.TEMP_SUFFIX}").exists()
    assert not (output_root / f"{audit.REPORT_NAME}{audit.TEMP_SUFFIX}").exists()
    assert (output_root / audit.JSON_NAME).exists()
    assert (output_root / audit.REPORT_NAME).exists()


def test_check_modes_detect_mismatches_and_write_nothing(
    tmp_path: Path,
) -> None:
    assert audit.main(["--output-root", str(_new_output_root(tmp_path / "base"))]) == 0
    base = tmp_path / "base" / "output"
    digest_before = _snapshot((base / audit.JSON_NAME, base / audit.REPORT_NAME))
    assert audit.main(["--check", "--output-root", str(base)]) == 0
    assert _snapshot((base / audit.JSON_NAME, base / audit.REPORT_NAME)) == digest_before

    report_mismatch = tmp_path / "report_mismatch"
    shutil.copytree(base, report_mismatch)
    with (report_mismatch / audit.REPORT_NAME).open("a", encoding="utf-8") as handle:
        handle.write("tampered\n")
    assert audit.main(["--check", "--output-root", str(report_mismatch)]) == 1

    mixed_pair = tmp_path / "mixed_pair"
    shutil.copytree(base, mixed_pair)
    payload = json.loads((mixed_pair / audit.JSON_NAME).read_text(encoding="utf-8"))
    payload["environment"]["commit"] = "0" * 40
    (mixed_pair / audit.JSON_NAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    assert audit.main(["--check", "--output-root", str(mixed_pair)]) == 1

    json_mismatch = tmp_path / "json_mismatch"
    shutil.copytree(base, json_mismatch)
    payload = json.loads((json_mismatch / audit.JSON_NAME).read_text(encoding="utf-8"))
    payload["inventory"]["frames"][0]["frame_sha256"] = "f" * 64
    (json_mismatch / audit.JSON_NAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    assert audit.main(["--check", "--output-root", str(json_mismatch)]) == 1

    invalid_schema = tmp_path / "invalid_schema"
    invalid_schema.mkdir()
    (invalid_schema / audit.JSON_NAME).write_text("{}\n", encoding="utf-8")
    (invalid_schema / audit.REPORT_NAME).write_text("not a report\n", encoding="utf-8")
    assert audit.main(["--check", "--output-root", str(invalid_schema)]) == 3

    empty = tmp_path / "empty"
    empty.mkdir()
    assert audit.main(["--check", "--output-root", str(empty)]) == 3


def test_check_data_drift_exits_two(tmp_path: Path) -> None:
    data_copy = _copy_data(tmp_path)
    output_root = _new_output_root(tmp_path)
    assert audit.main(["--data-root", str(data_copy), "--output-root", str(output_root)]) == 0
    (data_copy / "drift.txt").write_text("drift\n", encoding="utf-8")
    assert (
        audit.main(["--check", "--data-root", str(data_copy), "--output-root", str(output_root)])
        == audit.EXIT_DATA_ERROR
    )
    assert not (output_root / f"{audit.JSON_NAME}{audit.TEMP_SUFFIX}").exists()
    assert not (output_root / f"{audit.REPORT_NAME}{audit.TEMP_SUFFIX}").exists()


def test_generation_creates_only_two_filenames_and_no_forbidden_artifacts(tmp_path: Path) -> None:
    output_root = _new_output_root(tmp_path)
    assert audit.main(["--output-root", str(output_root)]) == 0
    entries = sorted(path.name for path in output_root.iterdir())
    assert entries == [audit.JSON_NAME, audit.REPORT_NAME]
    assert not any(name.endswith((".png", ".csv", ".overlay", ".figure")) for name in entries)
    assert not (REPO_ROOT / "docs" / "validation" / ".audit-staging").exists()
