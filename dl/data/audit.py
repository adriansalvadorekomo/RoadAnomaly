"""Read-only, reproducible audit of the RoadAnomaly benchmark dataset.

The audit turns local files under ``data/`` into one schema-validated JSON
summary.  The Markdown report is a pure renderer over the validated JSON bytes.
Nothing is fitted, selected, scored or promoted, and ``data/`` is never written.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import re
import statistics
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, TypedDict

import numpy as np
from PIL import Image

# --------------------------------------------------------------------------- constants

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    REPO_ROOT / "specs" / "003-dataset-understanding" / "contracts" / "audit-summary.schema.json"
)

AUDIT_VERSION = "1.0"
CANONICAL_COMMAND = "make data-audit"
CHECK_COMMAND = "make data-audit-check"
JSON_NAME = "roadanomaly-eda.json"
REPORT_NAME = "roadanomaly-eda.md"
TEMP_SUFFIX = ".tmp"

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FRAME_PIXELS = FRAME_WIDTH * FRAME_HEIGHT
EXPECTED_FRAME_COUNT = 60
EXPECTED_LABEL_DIR_COUNT = 60
EXPECTED_INSTANCE_FRAME_COUNT = 46
EXPECTED_SEMANTIC_ONLY_FRAME_COUNT = 14
EXPECTED_INSTANCE_COUNT = 201
EXPECTED_TOTAL_ANOMALY_PIXELS = 5_446_413
EXPECTED_TOTAL_PIXELS = 55_296_000

HISTORICAL_FINGERPRINT = "7c16ab39607d68a66bc2f4ac321933f64221d62980119ea780af5abf2a99f4e2"
HISTORICAL_FILE_COUNT = 677
HISTORICAL_TOTAL_BYTES = 13_135_474
FINGERPRINT_RECIPE = (
    "regular files under data/ (no symlinks), sorted by POSIX relative path; for each: "
    "UTF-8 path + NUL + raw 32-byte SHA-256 of content; no trailing NUL/newline; lowercase hex"
)

SEMANTIC_VALUES = [0, 2]
NORMAL_COLOUR = [0, 0, 0]
ANOMALY_COLOUR = [255, 69, 0]
INSTANCE_CLASS_ID = 2

ANNOTATION_LICENCE_TERMS_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
DHASH_METHOD = "9x8 grayscale dHash, 64 bits; Hamming distance <= 6"
BELOW_ONE_PERCENT_LIMIT = 1.0

EXIT_SUCCESS = 0
EXIT_OUTPUT_MISMATCH = 1
EXIT_DATA_ERROR = 2
EXIT_CONTRACT_ERROR = 3
EXIT_OUTPUT_POLICY_ERROR = 4

_FRAME_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+\.webp$")
_LICENCE_TOKEN_RE = re.compile(
    r"\bCC0\b|\bCC[ -]BY(?:[ -]SA)?(?:[ -]\d+(?:\.\d+)?)?|\bpublic domain\b",
    re.IGNORECASE,
)
_URL_RE = re.compile(r"https?://\S+")
_HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

REPORT_HEADINGS = (
    "## 1. Scope and method",
    "## 2. Environment and reproduction",
    "## 3. Fingerprint",
    "## 4. Inventory and integrity",
    "## 5. Instance/semantic consistency",
    "## 6. Coverage, categories and object scale",
    "## 7. Instance mapping, ROI and duplicates",
    "## 8. Credits, licensing and provenance",
    "## 9. Documented claims, limitations and unresolved items",
    "## 10. Validation and output integrity",
)

COVERAGE_DEFINITIONS = {
    "pooled_fraction": "total anomaly pixels / total pixels over all 60 frames",
    "per_frame_fraction": "anomaly pixels / (1280 x 720)",
    "percent": "100 x fraction",
    "median": "median of the 60 per-frame fractions",
    "below_one_percent": "per-frame percent < 1.0",
}

SCALE_DEFINITIONS = {
    "roi_area": "(x1 - x0) x (y1 - y0), half-open extents",
    "both_dimensions_below_32": "width < 32 and height < 32",
    "either_dimension_below_32": "width < 32 or height < 32",
    "roi_equivalent_square": "sqrt(ROI area)",
    "roi_bounding_box": "median ROI width and height",
    "mask_equivalent_square": "sqrt(count of nonzero instance-mask pixels)",
}

ROI_DEFINITIONS = {
    "out_of_bounds": "x0 < 0 or y0 < 0 or x1 > 1280 or y1 > 720, half-open extents",
    "non_tight": (
        "pixel box not strictly inside half-open ROI: "
        "bx0 < x0 or by0 < y0 or bx1 >= x1 or by1 >= y1"
    ),
    "centroid_containment": ("0 <= (bx0 + bx1) / 2 < 1280 and 0 <= (by0 + by1) / 2 < 720"),
}

NULLABLE_PATHS = {
    ("provenance", "release_identifier"),
    ("credits", "entries", "[]", "source_url"),
    ("credits", "source_groups", "[]", "source_url"),
    ("claims", "[]", "definition"),
    ("claims", "[]", "source"),
    ("limitations", "[]", "source"),
}

# --------------------------------------------------------------------------- typed records


class EnvironmentRecord(TypedDict):
    commit: str
    python: str
    numpy: str
    pillow: str
    jsonschema: str
    command: str
    audit_version: str


class FingerprintRecord(TypedDict):
    historical: str
    recipe: str
    recipe_version: str
    provenance: str
    computed: str
    matches: bool
    historical_file_count: int
    historical_total_bytes: int
    current_file_count: int
    current_total_bytes: int
    status: str


class AnnotationIntegrityRecord(TypedDict):
    semantic_values: list[int]
    colour_mapping: dict[str, list[int]]
    colour_mapping_valid: bool
    instance_class_id: int
    instance_ids_contiguous: bool
    label_files_complete: bool
    frame_decodable: bool


class FrameRecord(TypedDict):
    frame_name: str
    frame_path: str
    width: int
    height: int
    mode: str
    frame_sha256: str
    label_dir: str
    annotation_kind: str


class InventoryRecord(TypedDict):
    frame_list_count: int
    frame_count: int
    label_dir_count: int
    instance_frame_count: int
    semantic_only_frame_count: int
    annotation_integrity: AnnotationIntegrityRecord
    frames: list[FrameRecord]


class InstanceSemanticRecord(TypedDict):
    frames_checked: int
    frames_exact_match: int
    frames_mismatched: int
    mismatched_frames: list[str]
    extra_instance_pixels: int
    missing_instance_pixels: int
    semantic_only_frames_excluded: int
    definition: str


class FrameCoverage(TypedDict):
    frame_name: str
    anomaly_pixels: int
    total_pixels: int
    fraction: float
    percent: float


class CoverageRecord(TypedDict):
    total_anomaly_pixels: int
    total_pixels: int
    pooled_fraction: float
    pooled_percent: float
    minimum_percent: float
    maximum_percent: float
    median_percent: float
    below_one_percent: list[str]
    per_frame: list[FrameCoverage]
    definitions: dict[str, str]


class CategoryRecord(TypedDict):
    counts: dict[str, int]
    total_frames: int
    classification: str


class ScaleRecord(TypedDict):
    roi_area_below_1024: int
    both_dimensions_below_32: int
    either_dimension_below_32: int
    median_roi_equivalent_square_px: float
    median_roi_width_px: float
    median_roi_height_px: float
    median_mask_equivalent_square_px: float
    denominator: int
    definitions: dict[str, str]


class MappingMismatch(TypedDict):
    frame_name: str
    mask_value: int
    index_position: int
    index_id: int


class ExistingTestCheck(TypedDict):
    name: str
    passes: bool


class MappingRecord(TypedDict):
    frames_checked: int
    frames_agreeing: int
    frames_disagreeing: int
    disagreeing_frames: list[str]
    mismatches: list[MappingMismatch]
    existing_test_check: ExistingTestCheck


class AffectedInstance(TypedDict):
    frame_name: str
    mask_value: int


class RoiRecord(TypedDict):
    instances_checked: int
    out_of_bounds: int
    non_tight: int
    centroids_inside: int
    out_of_bounds_instances: list[AffectedInstance]
    non_tight_instances: list[AffectedInstance]
    definitions: dict[str, str]


class FramePair(TypedDict):
    frame_a: str
    frame_b: str


class DHashPair(TypedDict):
    frame_a: str
    frame_b: str
    distance: int


class DuplicateRecord(TypedDict):
    exact_pairs: list[FramePair]
    decoded_pairs: list[FramePair]
    dhash_pairs: list[DHashPair]
    dhash_method: str
    limitations: list[str]


class CreditEntry(TypedDict):
    frame_name: str
    credit_text: str
    licence_tokens: list[str]
    source_url: str | None
    attribution: str


class SourceGroup(TypedDict):
    group_id: str
    source_url: str | None
    frames: list[str]
    frame_count: int


class CreditRecord(TypedDict):
    entries: list[CreditEntry]
    coverage: int
    missing_entries: list[str]
    missing_licence_tokens: list[str]
    missing_source_urls: list[str]
    source_groups: list[SourceGroup]
    annotation_licence_claim: str
    annotation_licence_sources: list[str]
    annotation_licence_terms_url: str
    code_licence: str
    code_licence_source: str
    code_licence_scope: str
    legal_conclusion: str


class UnresolvedItem(TypedDict):
    item_id: str
    statement: str
    evidence_class: str
    source: str
    status: str


class ProvenanceRecord(TypedDict):
    citation: str
    release_identifier: None
    upstream_status: str
    scene_identity: str
    filename_prefix_is_scene_id: bool
    local_attribution_is_redistribution_proof: bool
    normal_road_source_selected: bool
    unresolved_items: list[UnresolvedItem]
    p0_status: dict[str, str]
    g10_status: str


class DocumentedClaim(TypedDict):
    claim_id: str
    documented_text: str
    documented_source: str
    computed_value: str
    computed_definition: str
    treatment: str


class Claim(TypedDict):
    claim_id: str
    text: str
    evidence_class: str
    value: object
    definition: str | None
    source: str | None


class Limitation(TypedDict):
    limitation_id: str
    statement: str
    evidence_class: str
    source: str | None


class AuditResult(TypedDict):
    schema_version: str
    environment: EnvironmentRecord
    fingerprint: FingerprintRecord
    inventory: InventoryRecord
    instance_semantic: InstanceSemanticRecord
    coverage: CoverageRecord
    categories: CategoryRecord
    object_scale: ScaleRecord
    instance_mapping: MappingRecord
    roi: RoiRecord
    duplicates: DuplicateRecord
    credits: CreditRecord
    provenance: ProvenanceRecord
    documented_claims: list[DocumentedClaim]
    limitations: list[Limitation]
    claims: list[Claim]


AUDIT_ROOT_FIELDS = (
    "schema_version",
    "environment",
    "fingerprint",
    "inventory",
    "instance_semantic",
    "coverage",
    "categories",
    "object_scale",
    "instance_mapping",
    "roi",
    "duplicates",
    "credits",
    "provenance",
    "documented_claims",
    "limitations",
    "claims",
)

# --------------------------------------------------------------------------- errors and outputs


class AuditError(Exception):
    """Base class for actionable audit failures."""


class AuditDataError(AuditError):
    """Input, fingerprint or annotation-integrity failure (exit 2)."""


class AuditContractError(AuditError):
    """Schema, rendering, serialization or I/O failure (exit 3)."""


class AuditOutputPolicyError(AuditError):
    """Output-root or filename policy violation (exit 4)."""


@dataclass(frozen=True)
class OutputPaths:
    """The only two canonical output files and their temporary siblings."""

    root: Path
    json_path: Path
    report_path: Path
    json_tmp: Path
    report_tmp: Path

    @classmethod
    def for_root(cls, output_root: str | Path) -> OutputPaths:
        root = _resolve_output_root(output_root)
        json_path = root / JSON_NAME
        report_path = root / REPORT_NAME
        json_tmp = root / f"{JSON_NAME}{TEMP_SUFFIX}"
        report_tmp = root / f"{REPORT_NAME}{TEMP_SUFFIX}"
        for target in (json_path, report_path, json_tmp, report_tmp):
            if target.exists() and target.is_symlink():
                raise AuditOutputPolicyError(f"output target is a symlink: {target}")
            if target.parent.resolve(strict=True) != root:
                raise AuditOutputPolicyError(f"output target escapes the configured root: {target}")
        return cls(
            root=root,
            json_path=json_path,
            report_path=report_path,
            json_tmp=json_tmp,
            report_tmp=report_tmp,
        )


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _resolve_output_root(output_root: str | Path) -> Path:
    raw = Path(output_root).expanduser()
    if ".." in raw.parts:
        raise AuditOutputPolicyError(f"output root contains a traversal component: {raw}")
    try:
        if not raw.exists():
            raise AuditContractError(f"output root does not exist: {raw}")
        if not raw.is_dir():
            raise AuditContractError(f"output root is not a directory: {raw}")
        resolved = raw.resolve(strict=True)
    except AuditContractError:
        raise
    except OSError as exc:
        raise AuditContractError(f"cannot inspect output root {raw}: {exc}") from exc

    repo_root = REPO_ROOT.resolve()
    raw_absolute = raw.absolute()
    inside_repo = _is_within(raw_absolute, repo_root) or _is_within(resolved, repo_root)
    if inside_repo:
        canonical = (repo_root / "docs" / "validation").resolve(strict=True)
        if resolved != canonical:
            raise AuditOutputPolicyError(
                f"in-repository output root must be docs/validation, got {raw}"
            )
        if raw.is_symlink():
            raise AuditOutputPolicyError(f"in-repository output root may not be a symlink: {raw}")
        current = repo_root
        for part in resolved.relative_to(repo_root).parts:
            current = current / part
            if current.is_symlink():
                raise AuditOutputPolicyError(f"output root traverses a symlink: {current}")
    return resolved


def _write_temp(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o644)
    except OSError as exc:
        if path.is_symlink():
            raise AuditOutputPolicyError(f"temporary output path is a symlink: {path}") from exc
        raise AuditContractError(f"cannot create temporary file {path}: {exc}") from exc
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise AuditContractError(f"cannot write temporary file {path}: {exc}") from exc


def _remove_temp(path: Path) -> None:
    try:
        if path.exists() or path.is_symlink():
            path.unlink()
    except OSError as exc:
        raise AuditContractError(f"cannot remove temporary file {path}: {exc}") from exc


def write_outputs(json_bytes: bytes, report_bytes: bytes, paths: OutputPaths) -> None:
    """Write the two documents through temporary siblings and per-file replacement."""
    for target in (paths.json_path, paths.report_path):
        if target.exists() and target.is_symlink():
            raise AuditOutputPolicyError(f"canonical output path is a symlink: {target}")
    _remove_temp(paths.json_tmp)
    _remove_temp(paths.report_tmp)
    try:
        _write_temp(paths.json_tmp, json_bytes)
        _write_temp(paths.report_tmp, report_bytes)
        try:
            os.replace(paths.json_tmp, paths.json_path)
        except OSError as exc:
            raise AuditContractError(f"cannot replace {paths.json_path}: {exc}") from exc
        try:
            os.replace(paths.report_tmp, paths.report_path)
        except OSError as exc:
            raise AuditContractError(f"cannot replace {paths.report_path}: {exc}") from exc
    finally:
        _remove_temp(paths.json_tmp)
        _remove_temp(paths.report_tmp)


# --------------------------------------------------------------------------- schema and serialization


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    try:
        text = SCHEMA_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise AuditContractError(f"cannot read audit schema {SCHEMA_PATH}: {exc}") from exc
    try:
        schema = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AuditContractError(f"audit schema is invalid JSON: {exc}") from exc
    if not isinstance(schema, dict):
        raise AuditContractError("audit schema root must be a JSON object")
    return schema


def validate_summary(summary: Mapping[str, Any]) -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - declared dependency
        raise AuditContractError("jsonschema is unavailable; install requirements/dev.txt") from exc
    schema = load_schema()
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
    except jsonschema.SchemaError as exc:
        raise AuditContractError(f"audit schema is not valid Draft 2020-12: {exc.message}") from exc
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(summary), key=lambda err: list(err.absolute_path))
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path) or "<root>"
        raise AuditContractError(
            f"audit summary schema validation failed at {location}: {first.message}"
        )


def _ensure_complete(summary: AuditResult) -> None:
    if tuple(summary.keys()) != AUDIT_ROOT_FIELDS:
        missing = [name for name in AUDIT_ROOT_FIELDS if name not in summary]
        extra = [name for name in summary if name not in AUDIT_ROOT_FIELDS]
        raise AuditContractError(
            f"audit summary root fields are incomplete: missing={missing} extra={extra}"
        )
    _check_complete_value(summary, ())


def _check_complete_value(value: object, path: tuple[str, ...]) -> None:
    if value is None:
        if path not in NULLABLE_PATHS and path[:3] != ("claims", "[]", "value"):
            location = "/".join(path) or "<root>"
            raise AuditContractError(f"audit summary has a null mandatory value at {location}")
        return
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            location = "/".join(path) or "<root>"
            raise AuditContractError(f"audit summary has an empty mandatory value at {location}")
        if stripped.upper() in {"TODO", "TBD", "FIXME", "PLACEHOLDER"}:
            location = "/".join(path) or "<root>"
            raise AuditContractError(f"audit summary has a placeholder at {location}")
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            _check_complete_value(child, (*path, str(key)))
        return
    if isinstance(value, list):
        for child in value:
            _check_complete_value(child, (*path, "[]"))


def serialize_summary(summary: AuditResult) -> bytes:
    """Serialize deterministically: UTF-8, sorted keys, two-space JSON, one LF."""
    _ensure_complete(summary)
    try:
        text = json.dumps(
            summary,
            sort_keys=True,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise AuditContractError(f"cannot serialize audit summary: {exc}") from exc
    return (text + "\n").encode("utf-8")


# --------------------------------------------------------------------------- environment and fingerprint


def _git_commit(repo_root: Path) -> str:
    git_path = repo_root / ".git"
    try:
        if git_path.is_file():
            marker = git_path.read_text(encoding="utf-8").strip()
            if not marker.startswith("gitdir: "):
                raise AuditContractError(f"unsupported .git file: {git_path}")
            git_dir = (git_path.parent / marker.removeprefix("gitdir: ")).resolve()
        elif git_path.is_dir():
            git_dir = git_path
        else:
            raise AuditContractError(f"no git metadata found at {git_path}")
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref: "):
            ref = head.removeprefix("ref: ").strip()
            ref_path = git_dir / ref
            if ref_path.is_file():
                commit = ref_path.read_text(encoding="utf-8").strip()
            else:
                packed = git_dir / "packed-refs"
                commit = ""
                if packed.is_file():
                    for line in packed.read_text(encoding="utf-8").splitlines():
                        parts = line.split()
                        if len(parts) == 2 and parts[1] == ref:
                            commit = parts[0]
                            break
            if not commit:
                raise AuditContractError(f"cannot resolve git ref {ref}")
        else:
            commit = head
    except AuditContractError:
        raise
    except OSError as exc:
        raise AuditContractError(f"cannot read git commit from {git_path}: {exc}") from exc
    if not _HEX40_RE.fullmatch(commit):
        raise AuditContractError(f"git commit is not a 40-character lowercase SHA: {commit!r}")
    return commit


def _package_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError as exc:
        raise AuditContractError(f"required distribution is not installed: {distribution}") from exc


def build_environment() -> EnvironmentRecord:
    return EnvironmentRecord(
        commit=_git_commit(REPO_ROOT),
        python=platform.python_version(),
        numpy=np.__version__,
        pillow=Image.__version__,
        jsonschema=_package_version("jsonschema"),
        command=CANONICAL_COMMAND,
        audit_version=AUDIT_VERSION,
    )


def _fingerprint(data_root: Path) -> tuple[str, int, int]:
    try:
        files: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(data_root, followlinks=False):
            dirnames[:] = sorted(
                name for name in dirnames if not (Path(dirpath) / name).is_symlink()
            )
            for name in filenames:
                path = Path(dirpath) / name
                if path.is_symlink():
                    continue
                if path.is_file():
                    files.append(path)
        files.sort(key=lambda item: item.relative_to(data_root).as_posix().encode("utf-8"))
        digest = hashlib.sha256()
        total_bytes = 0
        for path in files:
            relative = path.relative_to(data_root).as_posix().encode("utf-8")
            content = path.read_bytes()
            total_bytes += len(content)
            digest.update(relative)
            digest.update(b"\0")
            digest.update(hashlib.sha256(content).digest())
    except OSError as exc:
        raise AuditDataError(f"cannot fingerprint {data_root}: {exc}") from exc
    return digest.hexdigest(), len(files), total_bytes


# --------------------------------------------------------------------------- image and label loading


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AuditDataError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AuditDataError(f"invalid JSON in {path}: {exc}") from exc
    except OSError as exc:
        raise AuditDataError(f"cannot read {path}: {exc}") from exc


def _resolve_data_root(data_root: str | Path) -> Path:
    root = Path(data_root).expanduser()
    if not root.is_absolute():
        root = Path.cwd() / root
    if not root.exists():
        raise AuditDataError(f"data root does not exist: {root}")
    if not root.is_dir():
        raise AuditDataError(f"data root is not a directory: {root}")
    return root.resolve()


def _sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise AuditDataError(f"cannot read {path}: {exc}") from exc


def _dhash(image: Image.Image) -> int:
    small = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    pixels = np.asarray(small, dtype=np.int16)
    bits = (pixels[:, 1:] > pixels[:, :-1]).reshape(-1)
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value


def _load_frame(path: Path) -> tuple[FrameRecord, str, int]:
    try:
        with Image.open(path) as image:
            if image.format != "WEBP":
                raise AuditDataError(f"{path}: expected a WebP frame, got {image.format!r}")
            if image.size != (FRAME_WIDTH, FRAME_HEIGHT):
                raise AuditDataError(
                    f"{path}: frame size is {image.size}, expected {(FRAME_WIDTH, FRAME_HEIGHT)}"
                )
            if image.mode != "RGB":
                raise AuditDataError(f"{path}: frame mode is {image.mode!r}, expected 'RGB'")
            image.load()
            decoded = hashlib.sha256(image.tobytes()).hexdigest()
            dhash = _dhash(image)
    except AuditDataError:
        raise
    except (OSError, ValueError, Image.UnidentifiedImageError) as exc:
        raise AuditDataError(f"cannot decode frame {path}: {exc}") from exc
    return (
        FrameRecord(
            frame_name=path.name,
            frame_path=f"frames/{path.name}",
            width=FRAME_WIDTH,
            height=FRAME_HEIGHT,
            mode="RGB",
            frame_sha256=_sha256_file(path),
            label_dir=f"frames/{path.stem}.labels",
            annotation_kind="semantic_only",
        ),
        decoded,
        dhash,
    )


def _load_semantic(path: Path, frame_path: Path) -> np.ndarray:
    try:
        with Image.open(path) as image:
            if image.size != (FRAME_WIDTH, FRAME_HEIGHT):
                raise AuditDataError(
                    f"{path}: semantic mask size {image.size} does not match {frame_path}"
                )
            array = np.asarray(image)
    except AuditDataError:
        raise
    except (OSError, ValueError, Image.UnidentifiedImageError) as exc:
        raise AuditDataError(f"cannot decode semantic mask {path}: {exc}") from exc
    if array.ndim != 2:
        raise AuditDataError(f"{path}: semantic mask must be a 2-D array, got shape {array.shape}")
    if not np.issubdtype(array.dtype, np.integer):
        raise AuditDataError(f"{path}: semantic mask must contain integers")
    values = sorted({int(value) for value in np.unique(array)})
    if values != SEMANTIC_VALUES:
        raise AuditDataError(f"{path}: semantic values are {values}, expected {SEMANTIC_VALUES}")
    if int(np.count_nonzero(array == 2)) == 0:
        raise AuditDataError(f"{path}: semantic mask has no anomaly pixels")
    return array


def _validate_colour(path: Path, semantic: np.ndarray, frame_path: Path) -> None:
    try:
        with Image.open(path) as image:
            if image.size != (FRAME_WIDTH, FRAME_HEIGHT):
                raise AuditDataError(
                    f"{path}: colour mask size {image.size} does not match {frame_path}"
                )
            colour = np.asarray(image.convert("RGB"))
    except AuditDataError:
        raise
    except (OSError, ValueError, Image.UnidentifiedImageError) as exc:
        raise AuditDataError(f"cannot decode colour mask {path}: {exc}") from exc
    if colour.shape != (FRAME_HEIGHT, FRAME_WIDTH, 3):
        raise AuditDataError(f"{path}: colour mask has shape {colour.shape}")
    normal = colour[semantic == 0]
    anomaly = colour[semantic == 2]
    if normal.size and not np.all(normal == NORMAL_COLOUR):
        raise AuditDataError(f"{path}: normal pixels are not RGB {NORMAL_COLOUR}")
    if anomaly.size and not np.all(anomaly == ANOMALY_COLOUR):
        raise AuditDataError(f"{path}: anomaly pixels are not RGB {ANOMALY_COLOUR}")


def _parse_instances(path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    if not isinstance(payload, dict) or not isinstance(payload.get("instances"), list):
        raise AuditDataError(f"{path}: expected an object with an 'instances' list")
    instances = payload["instances"]
    if not instances:
        raise AuditDataError(f"{path}: instance list is empty")
    for position, item in enumerate(instances, start=1):
        if not isinstance(item, dict):
            raise AuditDataError(f"{path}: instance {position} is not an object")
        if item.get("cls") != INSTANCE_CLASS_ID:
            raise AuditDataError(
                f"{path}: instance {position} has cls={item.get('cls')!r}, expected 2"
            )
        if not isinstance(item.get("id"), int):
            raise AuditDataError(f"{path}: instance {position} has a non-integer id")
        roi = item.get("roi_rect")
        if (
            not isinstance(roi, list)
            or len(roi) != 2
            or any(not isinstance(point, list) or len(point) != 2 for point in roi)
            or any(not isinstance(value, int) for point in roi for value in point)
        ):
            raise AuditDataError(f"{path}: instance {position} has an invalid roi_rect")
    return instances


def _load_instance_mask(path: Path, instances: list[dict[str, Any]]) -> np.ndarray:
    try:
        with Image.open(path) as image:
            if image.size != (FRAME_WIDTH, FRAME_HEIGHT):
                raise AuditDataError(
                    f"{path}: instance mask size {image.size} does not match frame"
                )
            array = np.asarray(image)
    except AuditDataError:
        raise
    except (OSError, ValueError, Image.UnidentifiedImageError) as exc:
        raise AuditDataError(f"cannot decode instance mask {path}: {exc}") from exc
    if array.ndim != 2:
        raise AuditDataError(f"{path}: instance mask must be a 2-D array, got shape {array.shape}")
    if not np.issubdtype(array.dtype, np.integer):
        raise AuditDataError(f"{path}: instance mask must contain integers")
    values = sorted({int(value) for value in np.unique(array) if int(value) != 0})
    expected = list(range(1, len(instances) + 1))
    if values != expected:
        raise AuditDataError(
            f"{path}: instance mask values are {values}, expected contiguous {expected}"
        )
    if int(array.max()) != len(instances):
        raise AuditDataError(
            f"{path}: max instance value {int(array.max())} differs from {len(instances)} entries"
        )
    return array


def _classify_frames(
    data_root: Path,
    frame_names: list[str],
) -> tuple[list[str], list[str]]:
    instance_names: list[str] = []
    semantic_only: list[str] = []
    for name in frame_names:
        label_dir = data_root / "frames" / f"{Path(name).stem}.labels"
        has_index = (label_dir / "index.json").is_file()
        has_instance_mask = (label_dir / "labels_instance.png").is_file()
        if has_index and not has_instance_mask:
            raise AuditDataError(f"{label_dir}: index.json exists without labels_instance.png")
        if has_instance_mask and not has_index:
            raise AuditDataError(f"{label_dir}: labels_instance.png exists without index.json")
        if has_index:
            instance_names.append(name)
        else:
            semantic_only.append(name)
    return instance_names, semantic_only


# --------------------------------------------------------------------------- credit parsing


@dataclass(frozen=True)
class _CreditBlock:
    stems: tuple[str, ...]
    lines: tuple[str, ...]


def _parse_credit_blocks(text: str, known_stems: set[str]) -> list[_CreditBlock]:
    blocks: list[_CreditBlock] = []
    current_stems: list[str] = []
    current_lines: list[str] = []
    previous_indented = False

    def finish() -> None:
        nonlocal current_stems, current_lines
        if current_stems:
            blocks.append(_CreditBlock(tuple(current_stems), tuple(current_lines)))
        current_stems = []
        current_lines = []

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            finish()
            previous_indented = False
            continue
        if raw_line[0].isspace():
            if current_stems:
                current_lines.append(stripped)
                previous_indented = True
            continue
        if raw_line in known_stems:
            if previous_indented:
                finish()
            current_stems.append(raw_line)
            previous_indented = False
            continue
        finish()
        previous_indented = False
    finish()
    return blocks


def _clean_url(url: str) -> str:
    return url.rstrip(".,;")


def _parse_credits(data_root: Path, frame_names: list[str]) -> CreditRecord:
    path = data_root / "credits.txt"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise AuditDataError(f"missing credits file: {path}") from exc
    except OSError as exc:
        raise AuditDataError(f"cannot read credits file {path}: {exc}") from exc

    stems = [name.removesuffix(".webp") for name in frame_names]
    stem_to_name = dict(zip(stems, frame_names, strict=True))
    blocks = _parse_credit_blocks(text, set(stems))
    entries_by_stem: dict[str, CreditEntry] = {}
    block_for_stem: dict[str, _CreditBlock] = {}

    for block in blocks:
        credit_text = "\n".join(block.lines)
        if not credit_text:
            raise AuditDataError(f"credit block for {block.stems[0]} has no attribution text")
        urls = [_clean_url(match) for match in _URL_RE.findall(credit_text)]
        non_cc_urls = [url for url in urls if "creativecommons.org" not in url.lower()]
        source_url = non_cc_urls[-1] if non_cc_urls else None
        licence_tokens = [match.group(0) for match in _LICENCE_TOKEN_RE.finditer(credit_text)]
        attribution = block.lines[0]
        for stem in block.stems:
            if stem not in stem_to_name:
                raise AuditDataError(
                    f"credit entry {stem!r} does not match a frame in frame_list.json"
                )
            if stem in entries_by_stem:
                raise AuditDataError(f"duplicate credit entry for {stem}")
            entries_by_stem[stem] = CreditEntry(
                frame_name=stem_to_name[stem],
                credit_text=credit_text,
                licence_tokens=licence_tokens,
                source_url=source_url,
                attribution=attribution,
            )
            block_for_stem[stem] = block

    missing_entries = [
        name for name in frame_names if name.removesuffix(".webp") not in entries_by_stem
    ]
    if missing_entries:
        raise AuditDataError(
            f"credits.txt has no entry for {len(missing_entries)} frame(s): {missing_entries}"
        )
    if len(entries_by_stem) != EXPECTED_FRAME_COUNT:
        raise AuditDataError(
            f"credits.txt has {len(entries_by_stem)} unique entries, expected {EXPECTED_FRAME_COUNT}"
        )

    entries = [entries_by_stem[name.removesuffix(".webp")] for name in frame_names]
    missing_licence_tokens = sorted(
        entry["frame_name"] for entry in entries if not entry["licence_tokens"]
    )
    missing_source_urls = sorted(
        entry["frame_name"] for entry in entries if entry["source_url"] is None
    )

    frame_order = {name: index for index, name in enumerate(frame_names)}
    grouped: dict[tuple[str, object], list[str]] = {}
    for block_index, block in enumerate(blocks):
        credit_text = "\n".join(block.lines)
        urls = [_clean_url(match) for match in _URL_RE.findall(credit_text)]
        non_cc_urls = [url for url in urls if "creativecommons.org" not in url.lower()]
        source_url = non_cc_urls[-1] if non_cc_urls else None
        key: tuple[str, object] = (
            ("url", source_url) if source_url is not None else ("block", block_index)
        )
        grouped.setdefault(key, []).extend(block.stems)

    groups: list[SourceGroup] = []
    for (kind, url), group_stems in sorted(
        grouped.items(),
        key=lambda item: (
            min(
                frame_order[stem_to_name[stem.removesuffix(".webp")]]
                for stem in item[1]
                if stem in stem_to_name
            ),
            str(item[0][1] or ""),
        ),
    ):
        names = [stem_to_name[stem] for stem in group_stems if stem in stem_to_name]
        names.sort(key=frame_order.__getitem__)
        if len(names) <= 1:
            continue
        group_id = f"source-group-{len(groups) + 1:03d}"
        groups.append(
            SourceGroup(
                group_id=group_id,
                source_url=None if kind == "block" else str(url),
                frames=names,
                frame_count=len(names),
            )
        )

    return CreditRecord(
        entries=entries,
        coverage=len(entries),
        missing_entries=[],
        missing_licence_tokens=missing_licence_tokens,
        missing_source_urls=missing_source_urls,
        source_groups=groups,
        annotation_licence_claim="CC BY-SA 4.0",
        annotation_licence_sources=[
            "data/credits.txt",
            "docs/dataset.md",
            "README.md",
        ],
        annotation_licence_terms_url=ANNOTATION_LICENCE_TERMS_URL,
        code_licence="MIT",
        code_licence_source="LICENSE",
        code_licence_scope="source code; data and annotations excluded",
        legal_conclusion="not_made",
    )


# --------------------------------------------------------------------------- computation


def _expect(label: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise AuditDataError(
            f"baseline mismatch for {label}: got {actual!r}, expected {expected!r}"
        )


def _load_frame_names(path: Path) -> list[str]:
    payload = _read_json(path)
    if not isinstance(payload, list) or not all(isinstance(name, str) for name in payload):
        raise AuditDataError(f"{path}: expected a JSON list of frame names")
    if len(payload) != EXPECTED_FRAME_COUNT:
        raise AuditDataError(
            f"{path}: declares {len(payload)} frames, expected {EXPECTED_FRAME_COUNT}"
        )
    if len(set(payload)) != len(payload):
        raise AuditDataError(f"{path}: duplicate frame names")
    bad = [name for name in payload if not _FRAME_NAME_RE.fullmatch(name)]
    if bad:
        raise AuditDataError(f"{path}: invalid frame names: {bad}")
    return payload


def _check_inventory_paths(data_root: Path, frame_names: list[str]) -> list[Path]:
    frames_dir = data_root / "frames"
    if not frames_dir.is_dir():
        raise AuditDataError(f"missing frames directory: {frames_dir}")
    try:
        disk_frames = {
            path.name
            for path in frames_dir.iterdir()
            if path.suffix == ".webp" and path.is_file() and not path.is_symlink()
        }
    except OSError as exc:
        raise AuditDataError(f"cannot list {frames_dir}: {exc}") from exc
    missing = [name for name in frame_names if name not in disk_frames]
    orphaned = sorted(disk_frames - set(frame_names))
    if missing or orphaned:
        raise AuditDataError(f"frame inventory mismatch: missing={missing} orphaned={orphaned}")
    label_dirs = {
        path.name
        for path in frames_dir.iterdir()
        if path.name.endswith(".labels") and path.is_dir() and not path.is_symlink()
    }
    expected_dirs = {f"{Path(name).stem}.labels" for name in frame_names}
    missing_dirs = sorted(expected_dirs - label_dirs)
    orphan_dirs = sorted(label_dirs - expected_dirs)
    if missing_dirs or orphan_dirs:
        raise AuditDataError(
            f"label-directory mismatch: missing={missing_dirs} orphaned={orphan_dirs}"
        )
    if len(label_dirs) != EXPECTED_LABEL_DIR_COUNT:
        raise AuditDataError(
            f"found {len(label_dirs)} label directories, expected {EXPECTED_LABEL_DIR_COUNT}"
        )
    return [data_root / "frames" / name for name in frame_names]


def _find_pairs(records: list[tuple[str, str, int]]) -> list[FramePair]:
    by_digest: dict[str, list[str]] = {}
    for name, digest, _dhash in records:
        by_digest.setdefault(digest, []).append(name)
    pairs: list[FramePair] = []
    for names in by_digest.values():
        names.sort()
        for left in range(len(names)):
            for right in range(left + 1, len(names)):
                pairs.append(FramePair(frame_a=names[left], frame_b=names[right]))
    pairs.sort(key=lambda pair: (pair["frame_a"], pair["frame_b"]))
    return pairs


def _dhash_pairs(records: list[tuple[str, str, int]]) -> list[DHashPair]:
    pairs: list[DHashPair] = []
    for left in range(len(records)):
        for right in range(left + 1, len(records)):
            distance = (records[left][2] ^ records[right][2]).bit_count()
            if distance <= 6:
                frame_a, frame_b = sorted((records[left][0], records[right][0]))
                pairs.append(DHashPair(frame_a=frame_a, frame_b=frame_b, distance=distance))
    pairs.sort(key=lambda pair: (pair["frame_a"], pair["frame_b"], pair["distance"]))
    return pairs


def _build_claims(
    *,
    fingerprint: FingerprintRecord,
    inventory: InventoryRecord,
    instance_semantic: InstanceSemanticRecord,
    coverage: CoverageRecord,
    categories: CategoryRecord,
    object_scale: ScaleRecord,
    mapping: MappingRecord,
    roi: RoiRecord,
    duplicates: DuplicateRecord,
    credits: CreditRecord,
    provenance: ProvenanceRecord,
    documented_claims: list[DocumentedClaim],
    limitations: list[Limitation],
) -> list[Claim]:
    groups_frame_count = sum(group["frame_count"] for group in credits["source_groups"])
    claims: list[Claim] = [
        Claim(
            claim_id="fingerprint.match",
            text="The computed local fingerprint matches the historical baseline.",
            evidence_class="computed_local",
            value={
                "historical": fingerprint["historical"],
                "computed": fingerprint["computed"],
                "status": fingerprint["status"],
            },
            definition=fingerprint["recipe"],
            source="data/",
        ),
        Claim(
            claim_id="inventory.counts",
            text="60 frames, 60 label directories, 46 instance-annotated and 14 semantic-only frames.",
            evidence_class="computed_local",
            value={
                "frame_list_count": inventory["frame_list_count"],
                "frame_count": inventory["frame_count"],
                "label_dir_count": inventory["label_dir_count"],
                "instance_frame_count": inventory["instance_frame_count"],
                "semantic_only_frame_count": inventory["semantic_only_frame_count"],
            },
            definition="frame_list.json order and <frame>.labels directory membership",
            source="data/frame_list.json",
        ),
        Claim(
            claim_id="inventory.annotation_integrity",
            text="Frame decoding, semantic values, colour mapping, contiguous instance IDs and cls=2 were checked.",
            evidence_class="computed_local",
            value=inventory["annotation_integrity"],
            definition="All annotation_integrity flags are true only after their checks pass.",
            source="data/frames/*.labels",
        ),
        Claim(
            claim_id="instance_semantic.exact",
            text="All 46 instance frames satisfy the instance/semantic invariant; 14 semantic-only frames are excluded.",
            evidence_class="computed_local",
            value={
                "frames_checked": instance_semantic["frames_checked"],
                "frames_exact_match": instance_semantic["frames_exact_match"],
                "frames_mismatched": instance_semantic["frames_mismatched"],
                "extra_instance_pixels": instance_semantic["extra_instance_pixels"],
                "missing_instance_pixels": instance_semantic["missing_instance_pixels"],
                "semantic_only_frames_excluded": instance_semantic["semantic_only_frames_excluded"],
            },
            definition=instance_semantic["definition"],
            source="data/frames/*.labels",
        ),
        Claim(
            claim_id="coverage.pooled",
            text="Pooled anomaly coverage is 9.849561 percent.",
            evidence_class="computed_local",
            value={
                "fraction": coverage["pooled_fraction"],
                "percent": coverage["pooled_percent"],
                "total_anomaly_pixels": coverage["total_anomaly_pixels"],
                "total_pixels": coverage["total_pixels"],
            },
            definition=coverage["definitions"]["pooled_fraction"],
            source="data/frames/*.labels/labels_semantic.png",
        ),
        Claim(
            claim_id="coverage.range",
            text="Per-frame anomaly coverage ranges from 0.374674 to 42.328559 percent.",
            evidence_class="computed_local",
            value={
                "minimum_percent": coverage["minimum_percent"],
                "maximum_percent": coverage["maximum_percent"],
                "median_percent": coverage["median_percent"],
            },
            definition=coverage["definitions"]["per_frame_fraction"],
            source="data/frames/*.labels/labels_semantic.png",
        ),
        Claim(
            claim_id="coverage.below_one_percent",
            text="Six frames have per-frame anomaly coverage below one percent.",
            evidence_class="computed_local",
            value=coverage["below_one_percent"],
            definition=coverage["definitions"]["below_one_percent"],
            source="data/frames/*.labels/labels_semantic.png",
        ),
        Claim(
            claim_id="categories.counts",
            text="Filename prefixes count five object categories; they are not scene IDs.",
            evidence_class="computed_local",
            value={
                "counts": categories["counts"],
                "total_frames": categories["total_frames"],
                "classification": categories["classification"],
            },
            definition="prefix before the first digit in the frame stem",
            source="data/frame_list.json",
        ),
        Claim(
            claim_id="object_scale.counts",
            text="Object-scale counts expose all three small-object definitions.",
            evidence_class="computed_local",
            value={
                "roi_area_below_1024": object_scale["roi_area_below_1024"],
                "both_dimensions_below_32": object_scale["both_dimensions_below_32"],
                "either_dimension_below_32": object_scale["either_dimension_below_32"],
                "denominator": object_scale["denominator"],
            },
            definition=object_scale["definitions"]["roi_area"],
            source="data/frames/*.labels/index.json",
        ),
        Claim(
            claim_id="object_scale.medians",
            text="ROI and mask-pixel equivalent-square medians accompany the documented 87 x 87 claim.",
            evidence_class="computed_local",
            value={
                "median_roi_equivalent_square_px": object_scale["median_roi_equivalent_square_px"],
                "median_roi_width_px": object_scale["median_roi_width_px"],
                "median_roi_height_px": object_scale["median_roi_height_px"],
                "median_mask_equivalent_square_px": object_scale[
                    "median_mask_equivalent_square_px"
                ],
            },
            definition=object_scale["definitions"]["roi_equivalent_square"],
            source="data/frames/*.labels",
        ),
        Claim(
            claim_id="instance_mapping.agreement",
            text="The k-th index-entry order mapping agrees in 35 frames and disagrees in 11.",
            evidence_class="computed_local",
            value={
                "frames_checked": mapping["frames_checked"],
                "frames_agreeing": mapping["frames_agreeing"],
                "frames_disagreeing": mapping["frames_disagreeing"],
                "disagreeing_frames": mapping["disagreeing_frames"],
                "weaker_existing_test": mapping["existing_test_check"],
            },
            definition="mask value k equals instances[k-1].id",
            source="data/frames/*.labels/index.json",
        ),
        Claim(
            claim_id="roi.bounds",
            text="ROI findings are reported without clipping: 11 out of bounds, 17 non-tight, 201 centroids inside.",
            evidence_class="computed_local",
            value={
                "instances_checked": roi["instances_checked"],
                "out_of_bounds": roi["out_of_bounds"],
                "non_tight": roi["non_tight"],
                "centroids_inside": roi["centroids_inside"],
            },
            definition=roi["definitions"]["out_of_bounds"],
            source="data/frames/*.labels/index.json",
        ),
        Claim(
            claim_id="duplicates.methods",
            text="Exact, decoded-pixel and dHash duplicate checks found no baseline pairs; the methods are limited.",
            evidence_class="computed_local",
            value={
                "exact_pairs": duplicates["exact_pairs"],
                "decoded_pairs": duplicates["decoded_pairs"],
                "dhash_pairs": duplicates["dhash_pairs"],
                "dhash_method": duplicates["dhash_method"],
            },
            definition=duplicates["dhash_method"],
            source="data/frames/*.webp",
        ),
        Claim(
            claim_id="credits.coverage",
            text="All 60 frames have credit entries; 24 lack an explicit per-image licence token.",
            evidence_class="computed_local",
            value={
                "coverage": credits["coverage"],
                "missing_entries": credits["missing_entries"],
                "missing_licence_tokens": credits["missing_licence_tokens"],
                "missing_source_urls": credits["missing_source_urls"],
            },
            definition="one credit block per frame stem in data/credits.txt",
            source="data/credits.txt",
        ),
        Claim(
            claim_id="credits.source_groups",
            text="Four attribution-derived source groups cover 13 frames, including one group without a URL.",
            evidence_class="computed_local",
            value={
                "group_count": len(credits["source_groups"]),
                "frame_count": groups_frame_count,
                "groups": credits["source_groups"],
            },
            definition="frames sharing the same non-licence source URL, or the same URL-less credit block",
            source="data/credits.txt",
        ),
        Claim(
            claim_id="credits.annotation_licence",
            text="The annotations are documented locally as CC BY-SA 4.0; no legal conclusion is made.",
            evidence_class="documented_local",
            value={
                "claim": credits["annotation_licence_claim"],
                "sources": credits["annotation_licence_sources"],
                "terms_url": credits["annotation_licence_terms_url"],
                "legal_conclusion": credits["legal_conclusion"],
            },
            definition="local documented claim; not independently verified",
            source="data/credits.txt",
        ),
        Claim(
            claim_id="credits.code_licence",
            text="The source code is documented locally as MIT; data and annotations are excluded.",
            evidence_class="documented_local",
            value={
                "claim": credits["code_licence"],
                "source": credits["code_licence_source"],
                "scope": credits["code_licence_scope"],
                "legal_conclusion": credits["legal_conclusion"],
            },
            definition="local documented claim; not independently verified",
            source="LICENSE",
        ),
        Claim(
            claim_id="provenance.upstream",
            text="Upstream release provenance is unverified and scene identity is unresolved.",
            evidence_class="upstream_unverified",
            value={
                "citation": provenance["citation"],
                "release_identifier": provenance["release_identifier"],
                "upstream_status": provenance["upstream_status"],
                "scene_identity": provenance["scene_identity"],
                "filename_prefix_is_scene_id": provenance["filename_prefix_is_scene_id"],
                "local_attribution_is_redistribution_proof": provenance[
                    "local_attribution_is_redistribution_proof"
                ],
            },
            definition="no local release, version or checksum identifier",
            source="data/readme.md",
        ),
        Claim(
            claim_id="provenance.p0_g10",
            text="P0-1 through P0-4 and G10 remain open.",
            evidence_class="unresolved",
            value={
                "p0_status": provenance["p0_status"],
                "g10_status": provenance["g10_status"],
            },
            definition="open scientific and source-readiness items",
            source="docs/validation/requirements-matrix.md",
        ),
        Claim(
            claim_id="provenance.adr0010",
            text="The ADR-0010 threshold contradiction remains open and is not reworded into a decision.",
            evidence_class="unresolved",
            value=provenance["unresolved_items"],
            definition="unresolved item; status open",
            source="docs/adr/0010-model-lineup-and-evaluation-contract.md",
        ),
        Claim(
            claim_id="limitations.report",
            text="The report records method and evidence limits rather than converting them into certainty.",
            evidence_class="computed_local",
            value=[limitation["limitation_id"] for limitation in limitations],
            definition="limitations list",
            source="dl/data/audit.py",
        ),
        Claim(
            claim_id="documented_claims.comparisons",
            text="Six documented claims are compared with computed values without rewriting the source documents.",
            evidence_class="computed_local",
            value=[claim["claim_id"] for claim in documented_claims],
            definition="side-by-side documented and computed value",
            source="docs/dataset.md",
        ),
    ]
    for documented in documented_claims:
        claims.append(
            Claim(
                claim_id=f"documented.{documented['claim_id']}",
                text=documented["documented_text"],
                evidence_class=(
                    "unresolved"
                    if documented["treatment"] == "mark_unresolved"
                    else "documented_local"
                ),
                value=documented["computed_value"],
                definition=documented["computed_definition"],
                source=documented["documented_source"],
            )
        )
    return claims


def compute_audit(data_root: str | Path) -> AuditResult:
    """Compute the complete MVP audit from local files, read-only."""
    root = _resolve_data_root(data_root)
    environment = build_environment()
    frame_list_path = root / "frame_list.json"
    frame_names = _load_frame_names(frame_list_path)
    frame_paths = _check_inventory_paths(root, frame_names)
    instance_names, semantic_only_names = _classify_frames(root, frame_names)

    frames: list[FrameRecord] = []
    frame_coverage: list[FrameCoverage] = []
    raw_coverage_fractions: list[float] = []
    exact_records: list[tuple[str, str, int]] = []
    decoded_records: list[tuple[str, str, int]] = []
    mismatch_diagnostics: list[tuple[str, int, int]] = []
    instance_semantic_mismatches: list[str] = []
    extra_pixels = 0
    missing_pixels = 0
    mapping_mismatches: list[MappingMismatch] = []
    disagreeing_frames: list[str] = []
    roi_areas: list[float] = []
    roi_widths: list[float] = []
    roi_heights: list[float] = []
    roi_equivalent: list[float] = []
    mask_equivalent: list[float] = []
    out_of_bounds_instances: list[AffectedInstance] = []
    non_tight_instances: list[AffectedInstance] = []
    centroids_inside = 0
    total_instances = 0
    total_anomaly_pixels = 0
    existing_test_passes = True
    checked_instance_frames = 0
    exact_instance_frames = 0

    for frame_path, frame_name in zip(frame_paths, frame_names, strict=True):
        stem = Path(frame_name).stem
        label_dir = root / "frames" / f"{stem}.labels"
        record, decoded_sha256, dhash = _load_frame(frame_path)
        exact_records.append((frame_name, record["frame_sha256"], dhash))
        decoded_records.append((frame_name, decoded_sha256, dhash))
        semantic_path = label_dir / "labels_semantic.png"
        colour_path = label_dir / "labels_semantic_color.png"
        if not semantic_path.is_file():
            raise AuditDataError(f"missing semantic mask: {semantic_path}")
        if not colour_path.is_file():
            raise AuditDataError(f"missing colour mask: {colour_path}")
        semantic = _load_semantic(semantic_path, frame_path)
        _validate_colour(colour_path, semantic, frame_path)
        anomaly_pixels = int(np.count_nonzero(semantic == 2))
        total_anomaly_pixels += anomaly_pixels
        raw_fraction = anomaly_pixels / FRAME_PIXELS
        raw_coverage_fractions.append(raw_fraction)
        fraction = round(raw_fraction, 8)
        percent = round(100.0 * raw_fraction, 6)
        frame_coverage.append(
            FrameCoverage(
                frame_name=frame_name,
                anomaly_pixels=anomaly_pixels,
                total_pixels=FRAME_PIXELS,
                fraction=fraction,
                percent=percent,
            )
        )

        index_path = label_dir / "index.json"
        if index_path.is_file():
            record["annotation_kind"] = "instance"
            instances = _parse_instances(index_path)
            mask_path = label_dir / "labels_instance.png"
            if not mask_path.is_file():
                raise AuditDataError(f"missing instance mask: {mask_path}")
            instance_mask = _load_instance_mask(mask_path, instances)
            total_instances += len(instances)
            checked_instance_frames += 1
            if int(instance_mask.max()) != len(instances):
                existing_test_passes = False

            union = instance_mask != 0
            anomaly = semantic == 2
            extra = union & ~anomaly
            missing = anomaly & ~union
            extra_count = int(np.count_nonzero(extra))
            missing_count = int(np.count_nonzero(missing))
            if extra_count or missing_count:
                instance_semantic_mismatches.append(frame_name)
                mismatch_diagnostics.append((frame_name, extra_count, missing_count))
                extra_pixels += extra_count
                missing_pixels += missing_count
            else:
                exact_instance_frames += 1

            frame_mismatches = 0
            for mask_value, item in enumerate(instances, start=1):
                index_id = int(item["id"])
                if index_id != mask_value:
                    mapping_mismatches.append(
                        MappingMismatch(
                            frame_name=frame_name,
                            mask_value=mask_value,
                            index_position=mask_value,
                            index_id=index_id,
                        )
                    )
                    frame_mismatches += 1
            if frame_mismatches:
                disagreeing_frames.append(frame_name)

            for mask_value, item in enumerate(instances, start=1):
                (x0, y0), (x1, y1) = item["roi_rect"]
                width = int(x1) - int(x0)
                height = int(y1) - int(y0)
                if width <= 0 or height <= 0:
                    raise AuditDataError(
                        f"{index_path}: instance {mask_value} has non-positive ROI "
                        f"width={width} height={height}"
                    )
                roi_area = float(width * height)
                roi_areas.append(roi_area)
                roi_widths.append(float(width))
                roi_heights.append(float(height))
                roi_equivalent.append(math.sqrt(roi_area))
                pixels = np.argwhere(instance_mask == mask_value)
                if pixels.size == 0:
                    raise AuditDataError(f"{mask_path}: instance value {mask_value} has no pixels")
                by0 = int(pixels[:, 0].min())
                bx0 = int(pixels[:, 1].min())
                by1 = int(pixels[:, 0].max())
                bx1 = int(pixels[:, 1].max())
                mask_equivalent.append(math.sqrt(float(len(pixels))))
                if not (0 <= (bx0 + bx1) / 2 < FRAME_WIDTH and 0 <= (by0 + by1) / 2 < FRAME_HEIGHT):
                    # Counted, never clipped; a baseline mismatch is raised below.
                    pass
                else:
                    centroids_inside += 1
                if int(x0) < 0 or int(y0) < 0 or int(x1) > FRAME_WIDTH or int(y1) > FRAME_HEIGHT:
                    out_of_bounds_instances.append(
                        AffectedInstance(frame_name=frame_name, mask_value=mask_value)
                    )
                if bx0 < int(x0) or by0 < int(y0) or bx1 >= int(x1) or by1 >= int(y1):
                    non_tight_instances.append(
                        AffectedInstance(frame_name=frame_name, mask_value=mask_value)
                    )
        else:
            record["annotation_kind"] = "semantic_only"
        frames.append(record)

    # The invariant is a hard failure and is reported before fingerprint drift, so an
    # altered mask gets the actionable per-frame diagnostic rather than a hash mismatch.
    if mismatch_diagnostics:
        details = "; ".join(
            f"{name}: extra={extra} missing={missing}"
            for name, extra, missing in mismatch_diagnostics
        )
        raise AuditDataError(
            "instance/semantic invariant failed for "
            f"{len(mismatch_diagnostics)} frame(s): {details}"
        )

    # Fingerprint drift is checked after structural integrity and before baseline
    # equality checks, preserving the drift diagnostic for an added/changed data file.
    computed_fingerprint, current_file_count, current_total_bytes = _fingerprint(root)
    if (
        computed_fingerprint != HISTORICAL_FINGERPRINT
        or current_file_count != HISTORICAL_FILE_COUNT
        or current_total_bytes != HISTORICAL_TOTAL_BYTES
    ):
        raise AuditDataError(
            "fingerprint mismatch: "
            f"historical={HISTORICAL_FINGERPRINT} "
            f"({HISTORICAL_FILE_COUNT} files, {HISTORICAL_TOTAL_BYTES} bytes); "
            f"computed={computed_fingerprint} "
            f"({current_file_count} files, {current_total_bytes} bytes)"
        )

    # Accepted baseline regression checks. A match is required; nothing is repaired.
    instance_frame_count = len(instance_names)
    semantic_only_count = len(semantic_only_names)
    _expect("frame_list_count", len(frame_names), EXPECTED_FRAME_COUNT)
    _expect("frame_count", len(frames), EXPECTED_FRAME_COUNT)
    _expect(
        "label_dir_count", len({frame["label_dir"] for frame in frames}), EXPECTED_LABEL_DIR_COUNT
    )
    _expect("instance_frame_count", instance_frame_count, EXPECTED_INSTANCE_FRAME_COUNT)
    _expect("semantic_only_frame_count", semantic_only_count, EXPECTED_SEMANTIC_ONLY_FRAME_COUNT)
    _expect("instance_count", total_instances, EXPECTED_INSTANCE_COUNT)
    _expect("frames_checked", checked_instance_frames, EXPECTED_INSTANCE_FRAME_COUNT)
    _expect("frames_exact_match", exact_instance_frames, EXPECTED_INSTANCE_FRAME_COUNT)
    _expect("frames_mismatched", len(instance_semantic_mismatches), 0)
    _expect("extra_instance_pixels", extra_pixels, 0)
    _expect("missing_instance_pixels", missing_pixels, 0)
    _expect("total_anomaly_pixels", total_anomaly_pixels, EXPECTED_TOTAL_ANOMALY_PIXELS)
    _expect("categories.total_frames", len(frames), EXPECTED_FRAME_COUNT)
    _expect("roi.instances_checked", total_instances, EXPECTED_INSTANCE_COUNT)
    _expect("roi.centroids_inside", centroids_inside, EXPECTED_INSTANCE_COUNT)
    _expect("roi.out_of_bounds", len(out_of_bounds_instances), 11)
    _expect("roi.non_tight", len(non_tight_instances), 17)
    _expect("mapping.frames_agreeing", instance_frame_count - len(disagreeing_frames), 35)
    _expect("mapping.frames_disagreeing", len(disagreeing_frames), 11)
    _expect("mapping.mismatches", len(mapping_mismatches), 48)
    exact_pairs = _find_pairs(exact_records)
    decoded_pairs = _find_pairs(decoded_records)
    dhash_pairs = _dhash_pairs(decoded_records)
    _expect("duplicate.exact", len(exact_pairs), 0)
    _expect("duplicate.decoded", len(decoded_pairs), 0)
    _expect("duplicate.dhash", len(dhash_pairs), 0)

    coverage = CoverageRecord(
        total_anomaly_pixels=total_anomaly_pixels,
        total_pixels=EXPECTED_TOTAL_PIXELS,
        pooled_fraction=round(total_anomaly_pixels / EXPECTED_TOTAL_PIXELS, 8),
        pooled_percent=round(100.0 * total_anomaly_pixels / EXPECTED_TOTAL_PIXELS, 6),
        minimum_percent=round(100.0 * min(raw_coverage_fractions), 6),
        maximum_percent=round(100.0 * max(raw_coverage_fractions), 6),
        median_percent=round(100.0 * statistics.median(raw_coverage_fractions), 6),
        below_one_percent=sorted(
            row["frame_name"]
            for row, raw_fraction in zip(frame_coverage, raw_coverage_fractions, strict=True)
            if 100.0 * raw_fraction < BELOW_ONE_PERCENT_LIMIT
        ),
        per_frame=frame_coverage,
        definitions=dict(COVERAGE_DEFINITIONS),
    )
    _expect("coverage.pooled_fraction", coverage["pooled_fraction"], 0.09849561)
    _expect("coverage.pooled_percent", coverage["pooled_percent"], 9.849561)
    _expect("coverage.minimum_percent", coverage["minimum_percent"], 0.374674)
    _expect("coverage.maximum_percent", coverage["maximum_percent"], 42.328559)
    _expect("coverage.median_percent", coverage["median_percent"], 6.622938)
    _expect("coverage.below_one_percent", len(coverage["below_one_percent"]), 6)

    prefix_counts: dict[str, int] = {}
    for name in frame_names:
        prefix = re.split(r"\d", Path(name).stem, maxsplit=1)[0]
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
    _expect(
        "categories.counts",
        prefix_counts,
        {"animals": 31, "obstacles": 15, "cones": 8, "lost_tires": 3, "vehicle": 3},
    )
    categories = CategoryRecord(
        counts={
            key: prefix_counts[key]
            for key in ("animals", "obstacles", "cones", "lost_tires", "vehicle")
        },
        total_frames=len(frame_names),
        classification="object_category_not_scene",
    )

    object_scale = ScaleRecord(
        roi_area_below_1024=sum(1 for area in roi_areas if area < 1024.0),
        both_dimensions_below_32=sum(
            1
            for width, height in zip(roi_widths, roi_heights, strict=True)
            if width < 32.0 and height < 32.0
        ),
        either_dimension_below_32=sum(
            1
            for width, height in zip(roi_widths, roi_heights, strict=True)
            if width < 32.0 or height < 32.0
        ),
        median_roi_equivalent_square_px=round(float(statistics.median(roi_equivalent)), 1),
        median_roi_width_px=round(float(statistics.median(roi_widths)), 1),
        median_roi_height_px=round(float(statistics.median(roi_heights)), 1),
        median_mask_equivalent_square_px=round(float(statistics.median(mask_equivalent)), 1),
        denominator=len(roi_areas),
        definitions=dict(SCALE_DEFINITIONS),
    )
    _expect("object_scale.roi_area_below_1024", object_scale["roi_area_below_1024"], 35)
    _expect("object_scale.both_dimensions_below_32", object_scale["both_dimensions_below_32"], 20)
    _expect("object_scale.either_dimension_below_32", object_scale["either_dimension_below_32"], 46)
    _expect(
        "object_scale.median_roi_equivalent_square_px",
        object_scale["median_roi_equivalent_square_px"],
        86.7,
    )
    _expect("object_scale.median_roi_width_px", object_scale["median_roi_width_px"], 85.0)
    _expect("object_scale.median_roi_height_px", object_scale["median_roi_height_px"], 107.0)
    _expect(
        "object_scale.median_mask_equivalent_square_px",
        object_scale["median_mask_equivalent_square_px"],
        51.2,
    )
    _expect("object_scale.denominator", object_scale["denominator"], EXPECTED_INSTANCE_COUNT)

    mapping_mismatches.sort(key=lambda item: (item["frame_name"], item["mask_value"]))
    disagreeing_frames.sort()
    mapping = MappingRecord(
        frames_checked=checked_instance_frames,
        frames_agreeing=checked_instance_frames - len(disagreeing_frames),
        frames_disagreeing=len(disagreeing_frames),
        disagreeing_frames=disagreeing_frames,
        mismatches=mapping_mismatches,
        existing_test_check=ExistingTestCheck(
            name="max(mask) == len(instances)",
            passes=existing_test_passes,
        ),
    )

    out_of_bounds_instances.sort(key=lambda item: (item["frame_name"], item["mask_value"]))
    non_tight_instances.sort(key=lambda item: (item["frame_name"], item["mask_value"]))
    roi = RoiRecord(
        instances_checked=total_instances,
        out_of_bounds=len(out_of_bounds_instances),
        non_tight=len(non_tight_instances),
        centroids_inside=centroids_inside,
        out_of_bounds_instances=out_of_bounds_instances,
        non_tight_instances=non_tight_instances,
        definitions=dict(ROI_DEFINITIONS),
    )

    duplicates = DuplicateRecord(
        exact_pairs=exact_pairs,
        decoded_pairs=decoded_pairs,
        dhash_pairs=dhash_pairs,
        dhash_method=DHASH_METHOD,
        limitations=[
            "Exact file hashes detect byte-identical frames only.",
            "Decoded-pixel hashes detect identical RGB buffers after decoding, not near duplicates.",
            "The 9x8 grayscale dHash at Hamming distance <= 6 is method-limited; absence of "
            "reported pairs is not proof that no near-duplicate exists.",
            "No model-based perceptual duplicate check was performed.",
        ],
    )

    credits = _parse_credits(root, frame_names)
    _expect("credits.coverage", credits["coverage"], EXPECTED_FRAME_COUNT)
    _expect("credits.missing_licence_tokens", len(credits["missing_licence_tokens"]), 24)
    _expect("credits.missing_source_urls", len(credits["missing_source_urls"]), 4)
    _expect("credits.source_groups", len(credits["source_groups"]), 4)
    _expect(
        "credits.source_group_frames",
        sum(group["frame_count"] for group in credits["source_groups"]),
        13,
    )
    _expect(
        "credits.source_group_without_url",
        sum(1 for group in credits["source_groups"] if group["source_url"] is None),
        1,
    )
    _expect(
        "credits.missing_source_urls",
        credits["missing_source_urls"],
        sorted(name for name in frame_names if Path(name).stem.startswith("obstacles12_")),
    )

    annotation_integrity = AnnotationIntegrityRecord(
        semantic_values=list(SEMANTIC_VALUES),
        colour_mapping={
            "normal": list(NORMAL_COLOUR),
            "anomaly": list(ANOMALY_COLOUR),
        },
        colour_mapping_valid=True,
        instance_class_id=INSTANCE_CLASS_ID,
        instance_ids_contiguous=True,
        label_files_complete=True,
        frame_decodable=True,
    )
    inventory = InventoryRecord(
        frame_list_count=len(frame_names),
        frame_count=len(frames),
        label_dir_count=len({frame["label_dir"] for frame in frames}),
        instance_frame_count=instance_frame_count,
        semantic_only_frame_count=semantic_only_count,
        annotation_integrity=annotation_integrity,
        frames=frames,
    )
    instance_semantic = InstanceSemanticRecord(
        frames_checked=checked_instance_frames,
        frames_exact_match=exact_instance_frames,
        frames_mismatched=0,
        mismatched_frames=[],
        extra_instance_pixels=0,
        missing_instance_pixels=0,
        semantic_only_frames_excluded=semantic_only_count,
        definition="union(instance values 1..N) == semantic value 2, per instance frame",
    )
    fingerprint = FingerprintRecord(
        historical=HISTORICAL_FINGERPRINT,
        recipe=FINGERPRINT_RECIPE,
        recipe_version="historical-v1",
        provenance="local_reconstruction",
        computed=computed_fingerprint,
        matches=True,
        historical_file_count=HISTORICAL_FILE_COUNT,
        historical_total_bytes=HISTORICAL_TOTAL_BYTES,
        current_file_count=current_file_count,
        current_total_bytes=current_total_bytes,
        status="match",
    )

    provenance = ProvenanceRecord(
        citation="Lis et al., Detecting the Unexpected via Image Resynthesis, ICCV 2019",
        release_identifier=None,
        upstream_status="upstream_unverified",
        scene_identity="unresolved",
        filename_prefix_is_scene_id=False,
        local_attribution_is_redistribution_proof=False,
        normal_road_source_selected=False,
        unresolved_items=[
            UnresolvedItem(
                item_id="adr-0010-threshold-contradiction",
                statement="ADR-0010 leaves the threshold contradiction unresolved.",
                evidence_class="unresolved",
                source="docs/adr/0010-model-lineup-and-evaluation-contract.md",
                status="open",
            )
        ],
        p0_status={"P0-1": "open", "P0-2": "open", "P0-3": "open", "P0-4": "open"},
        g10_status="open",
    )

    documented_claims: list[DocumentedClaim] = [
        DocumentedClaim(
            claim_id="coverage-rounding",
            documented_text="Anomaly coverage is 9.8 percent of all pixels.",
            documented_source="docs/dataset.md",
            computed_value=(
                f"pooled {coverage['pooled_percent']:.6f} percent; "
                f"{coverage['minimum_percent']:.6f}-{coverage['maximum_percent']:.6f} percent "
                f"per frame; median {coverage['median_percent']:.6f} percent"
            ),
            computed_definition="pooled anomaly pixels / total pixels, six-decimal percent",
            treatment="report_both",
        ),
        DocumentedClaim(
            claim_id="object-scale-87x87",
            documented_text=(
                "Median instance is approximately 87 x 87 px; 35 of 201 are smaller than "
                "32 x 32 px."
            ),
            documented_source="docs/dataset.md",
            computed_value=(
                f"ROI area < 1024: {object_scale['roi_area_below_1024']}/{object_scale['denominator']}; "
                f"both dimensions < 32: {object_scale['both_dimensions_below_32']}/{object_scale['denominator']}; "
                f"either dimension < 32: {object_scale['either_dimension_below_32']}/{object_scale['denominator']}; "
                f"median ROI equivalent square {object_scale['median_roi_equivalent_square_px']:.1f} px; "
                f"median ROI bbox {object_scale['median_roi_width_px']:.1f} x "
                f"{object_scale['median_roi_height_px']:.1f} px; median mask equivalent square "
                f"{object_scale['median_mask_equivalent_square_px']:.1f} px"
            ),
            computed_definition=(
                "ROI area < 1024; both/either dimension < 32; sqrt(ROI area); "
                "median ROI bbox; sqrt(mask pixel count)"
            ),
            treatment="report_both",
        ),
        DocumentedClaim(
            claim_id="scene-prefix-grouping",
            documented_text="Filename prefixes are the natural scene grouping.",
            documented_source="docs/dataset.md",
            computed_value=(
                "No scene IDs or source scene metadata exist locally; prefix counts are "
                "object categories only ("
                + ", ".join(f"{name} {count}" for name, count in categories["counts"].items())
                + ")."
            ),
            computed_definition="filename prefix before the first digit",
            treatment="report_gap",
        ),
        DocumentedClaim(
            claim_id="per-image-licence-completeness",
            documented_text="Per-image terms are recorded in credits.txt.",
            documented_source="data/credits.txt",
            computed_value=(
                f"{len(credits['missing_licence_tokens'])}/{credits['coverage']} frames lack an "
                f"explicit licence token; {len(credits['missing_source_urls'])}/"
                f"{credits['coverage']} lack a source URL; missing tokens remain unresolved."
            ),
            computed_definition="explicit CC0, CC BY/CC BY-SA or public-domain token per credit block",
            treatment="mark_unresolved",
        ),
        DocumentedClaim(
            claim_id="benchmark-scene-folds",
            documented_text=(
                "Scene-grouped benchmark folds can support the separately reported "
                "threshold-tuned regime."
            ),
            documented_source="docs/dataset.md",
            computed_value=(
                "No benchmark scene identities exist locally; no folds, scene assignments or "
                "split hash are created."
            ),
            computed_definition="benchmark scene identity and fold assignment",
            treatment="report_gap",
        ),
        DocumentedClaim(
            claim_id="instance-id-equality",
            documented_text="The instance-mask pixel value equals the instance id.",
            documented_source="docs/dataset.md",
            computed_value=(
                f"{mapping['frames_agreeing']}/{mapping['frames_checked']} frames agree under the "
                f"k-th-entry order mapping; {mapping['frames_disagreeing']}/"
                f"{mapping['frames_checked']} disagree; {len(mapping['mismatches'])} "
                "value/entry mismatches are listed."
            ),
            computed_definition="mask value k equals instances[k-1].id",
            treatment="report_both",
        ),
    ]

    limitations: list[Limitation] = [
        Limitation(
            limitation_id="historical-fingerprint-local-reconstruction",
            statement=(
                "The historical fingerprint recipe is a local reconstruction; matching it does "
                "not prove the original Stage 2 implementation byte layout."
            ),
            evidence_class="upstream_unverified",
            source="specs/003-dataset-understanding/spec.md",
        ),
        Limitation(
            limitation_id="visual-registration-unverified",
            statement=(
                "Visual registration of frames, semantic masks and instance annotations was not "
                "assessed in the MVP."
            ),
            evidence_class="unresolved",
            source=None,
        ),
        Limitation(
            limitation_id="duplicates-method-limited",
            statement=(
                "Exact, decoded-pixel and dHash checks are method-limited; no reported pair is "
                "not proof that no near-duplicate exists."
            ),
            evidence_class="computed_local",
            source="data/frames/*.webp",
        ),
        Limitation(
            limitation_id="source-groups-attribution-derived",
            statement=(
                "Source groups are attribution-derived groups, not scene identities, split units "
                "or source rankings."
            ),
            evidence_class="computed_local",
            source="data/credits.txt",
        ),
        Limitation(
            limitation_id="upstream-provenance-unverified",
            statement=(
                "No local release, version or checksum identifier verifies upstream provenance."
            ),
            evidence_class="upstream_unverified",
            source="data/readme.md",
        ),
        Limitation(
            limitation_id="per-image-licence-tokens-unresolved",
            statement=(
                "Missing per-image licence tokens remain unresolved and are not evidence that an "
                "image is unlicensed."
            ),
            evidence_class="unresolved",
            source="data/credits.txt",
        ),
        Limitation(
            limitation_id="environment-commit-provenance",
            statement=(
                "environment.commit is recorded provenance, not a revalidated git ancestry claim."
            ),
            evidence_class="computed_local",
            source="specs/003-dataset-understanding/contracts/audit-cli.md",
        ),
    ]

    claims = _build_claims(
        fingerprint=fingerprint,
        inventory=inventory,
        instance_semantic=instance_semantic,
        coverage=coverage,
        categories=categories,
        object_scale=object_scale,
        mapping=mapping,
        roi=roi,
        duplicates=duplicates,
        credits=credits,
        provenance=provenance,
        documented_claims=documented_claims,
        limitations=limitations,
    )

    return AuditResult(
        schema_version="1.0",
        environment=environment,
        fingerprint=fingerprint,
        inventory=inventory,
        instance_semantic=instance_semantic,
        coverage=coverage,
        categories=categories,
        object_scale=object_scale,
        instance_mapping=mapping,
        roi=roi,
        duplicates=duplicates,
        credits=credits,
        provenance=provenance,
        documented_claims=documented_claims,
        limitations=limitations,
        claims=claims,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m dl.data.audit")
    parser.add_argument(
        "--check", action="store_true", help="validate committed evidence without writing"
    )
    parser.add_argument("--data-root", default=None, help="data directory (default: data)")
    parser.add_argument(
        "--output-root",
        default=None,
        help="existing output directory (default: docs/validation)",
    )
    args = parser.parse_args(argv)

    data_root = Path(args.data_root) if args.data_root else REPO_ROOT / "data"
    output_root = Path(args.output_root) if args.output_root else REPO_ROOT / "docs" / "validation"
    try:
        paths = OutputPaths.for_root(output_root)
        if args.check:
            return run_check(data_root, paths)
        return run_generate(data_root, paths)
    except AuditDataError as exc:
        print(f"data error: {exc}", file=sys.stderr)
        return EXIT_DATA_ERROR
    except AuditContractError as exc:
        print(f"contract error: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR
    except AuditOutputPolicyError as exc:
        print(f"output policy error: {exc}", file=sys.stderr)
        return EXIT_OUTPUT_POLICY_ERROR


def run_generate(data_root: str | Path, paths: OutputPaths) -> int:
    summary = compute_audit(data_root)
    json_bytes = serialize_summary(summary)
    validate_summary(summary)
    validated_summary = json.loads(json_bytes)
    if not isinstance(validated_summary, dict):
        raise AuditContractError("serialized audit summary root must be an object")
    source_digest = hashlib.sha256(json_bytes).hexdigest()
    report = render_report(validated_summary, source_digest)
    write_outputs(json_bytes, report.encode("utf-8"), paths)
    print(f"wrote {paths.json_path}")
    print(f"wrote {paths.report_path}")
    return EXIT_SUCCESS


def run_check(data_root: str | Path, paths: OutputPaths) -> int:
    try:
        json_bytes = paths.json_path.read_bytes()
        report_bytes = paths.report_path.read_bytes()
    except OSError as exc:
        raise AuditContractError(f"cannot read committed audit pair: {exc}") from exc
    try:
        committed = json.loads(json_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditContractError(f"committed JSON is invalid: {exc}") from exc
    if not isinstance(committed, dict):
        raise AuditContractError("committed JSON root must be an object")
    validate_summary(committed)
    if committed.get("environment", {}).get("command") != CANONICAL_COMMAND:
        print(
            "committed output mismatch: environment.command is not make data-audit", file=sys.stderr
        )
        return EXIT_OUTPUT_MISMATCH

    recomputed = compute_audit(data_root)
    committed_commit = committed["environment"]["commit"]
    recomputed["environment"]["commit"] = committed_commit
    if recomputed != committed:
        print(
            "committed output mismatch: recomputed audit differs from the committed JSON",
            file=sys.stderr,
        )
        return EXIT_OUTPUT_MISMATCH

    source_digest = hashlib.sha256(json_bytes).hexdigest()
    expected_report = render_report(committed, source_digest).encode("utf-8")
    if report_bytes != expected_report:
        print(
            "committed output mismatch: report is not a fresh render of the committed JSON",
            file=sys.stderr,
        )
        return EXIT_OUTPUT_MISMATCH
    text = report_bytes.decode("utf-8")
    if source_digest not in text:
        print("committed output mismatch: report lacks the source JSON SHA-256", file=sys.stderr)
        return EXIT_OUTPUT_MISMATCH
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    if tuple(headings) != REPORT_HEADINGS:
        print("committed output mismatch: report section headings are incomplete", file=sys.stderr)
        return EXIT_OUTPUT_MISMATCH
    if "report_sha256" in text or "report_hash" in text:
        print("committed output mismatch: report contains a report-hash field", file=sys.stderr)
        return EXIT_OUTPUT_MISMATCH
    print("audit check: ok")
    return EXIT_SUCCESS


# --------------------------------------------------------------------------- report rendering


def _md_cell(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if value.is_integer():
            return str(value)
        return repr(value)
    text = str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_md_cell(cell) for cell in row) + " |")
    return lines


def _claim_by_id(summary: Mapping[str, Any], claim_id: str) -> Mapping[str, Any]:
    for claim in summary["claims"]:
        if claim["claim_id"] == claim_id:
            return claim
    raise AuditContractError(f"report requires missing claim: {claim_id}")


def _claim_value_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (bool, int, float)) or value is None:
        return _md_cell(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def render_report(validated_summary: Mapping[str, Any], source_json_sha256: str) -> str:
    """Render the ten-section Markdown report from a validated JSON summary."""
    if not _HEX64_RE.fullmatch(source_json_sha256):
        raise AuditContractError("source JSON SHA-256 must be 64 lowercase hex characters")
    summary = validated_summary
    env = summary["environment"]
    fingerprint = summary["fingerprint"]
    inventory = summary["inventory"]
    integrity = inventory["annotation_integrity"]
    instance_semantic = summary["instance_semantic"]
    coverage = summary["coverage"]
    categories = summary["categories"]
    object_scale = summary["object_scale"]
    mapping = summary["instance_mapping"]
    roi = summary["roi"]
    duplicates = summary["duplicates"]
    credits = summary["credits"]
    provenance = summary["provenance"]
    source_groups_claim = _claim_by_id(summary, "credits.source_groups")
    source_group_value = source_groups_claim["value"]
    if not isinstance(source_group_value, dict):
        raise AuditContractError("credits.source_groups claim value must be an object")
    source_group_count = source_group_value["group_count"]
    source_group_frames = source_group_value["frame_count"]

    first_frame = inventory["frames"][0]
    lines: list[str] = [
        f"Source JSON SHA-256: `{source_json_sha256}` (`computed_local`)",
        "",
        "## 1. Scope and method",
        "",
        f"This audit covers only the {inventory['frame_list_count']} held-out RoadAnomaly "
        "benchmark frames and is read-only over `data/` (`computed_local`). The benchmark is "
        "evaluation-only: no "
        "model was fitted, selected, tuned, scored or promoted (`documented_local`).",
        "",
        "Evidence classes are visible on every quantitative, provenance and licensing "
        "statement: `computed_local`, `documented_local`, `upstream_unverified` or "
        "`unresolved`. Visual registration, overlays, aggregate figures, the review ledger "
        "and normal-road readiness are post-MVP extensions and are not assessed here "
        "(`unresolved`).",
        "",
        "## 2. Environment and reproduction",
        "",
        *_table(
            ("Item", "Value", "Evidence"),
            [
                ("Source commit", env["commit"], "computed_local"),
                ("Python", env["python"], "computed_local"),
                ("NumPy", env["numpy"], "computed_local"),
                ("Pillow", env["pillow"], "computed_local"),
                ("jsonschema", env["jsonschema"], "computed_local"),
                ("Audit version", env["audit_version"], "computed_local"),
                ("Canonical command", env["command"], "computed_local"),
                ("Check command", CHECK_COMMAND, "documented_local"),
            ],
        ),
        "",
        "`environment.commit` is recorded provenance, not a revalidated git ancestry "
        "claim (`upstream_unverified`). Matplotlib and figure versions are not claimed or "
        "required (`unresolved`).",
        "",
        "## 3. Fingerprint",
        "",
        f"Recipe (`documented_local`): `{fingerprint['recipe']}`.",
        "",
        *_table(
            ("Property", "Value", "Evidence"),
            [
                ("Historical value", f"`{fingerprint['historical']}`", "computed_local"),
                (
                    "Historical counts",
                    f"{fingerprint['historical_file_count']} files, "
                    f"{fingerprint['historical_total_bytes']} bytes",
                    "computed_local",
                ),
                ("Computed value", f"`{fingerprint['computed']}`", "computed_local"),
                (
                    "Current counts",
                    f"{fingerprint['current_file_count']} files, "
                    f"{fingerprint['current_total_bytes']} bytes",
                    "computed_local",
                ),
                ("Status", fingerprint["status"], "computed_local"),
                ("Provenance", fingerprint["provenance"], "upstream_unverified"),
            ],
        ),
        "",
        "The historical recipe is a local reconstruction. Matching it does not prove the "
        "original Stage 2 implementation byte layout (`upstream_unverified`). Current "
        "counts do not replace the historical baseline (`computed_local`).",
        "",
        "## 4. Inventory and integrity",
        "",
        *_table(
            ("Property", "Value", "Evidence"),
            [
                ("Frame-list entries", inventory["frame_list_count"], "computed_local"),
                ("Frames on disk", inventory["frame_count"], "computed_local"),
                ("Label directories", inventory["label_dir_count"], "computed_local"),
                ("Instance-annotated frames", inventory["instance_frame_count"], "computed_local"),
                ("Semantic-only frames", inventory["semantic_only_frame_count"], "computed_local"),
                (
                    "Image size",
                    f"{first_frame['width']} x {first_frame['height']}",
                    "computed_local",
                ),
                ("Image mode", first_frame["mode"], "computed_local"),
            ],
        ),
        "",
        *_table(
            ("Integrity check", "Value", "Evidence"),
            [
                ("Semantic values", integrity["semantic_values"], "computed_local"),
                ("Colour mapping", integrity["colour_mapping"], "computed_local"),
                ("Colour mapping valid", integrity["colour_mapping_valid"], "computed_local"),
                ("Instance class ID", integrity["instance_class_id"], "computed_local"),
                ("Contiguous instance IDs", integrity["instance_ids_contiguous"], "computed_local"),
                ("Label files complete", integrity["label_files_complete"], "computed_local"),
                ("Frame decodable", integrity["frame_decodable"], "computed_local"),
            ],
        ),
        "",
        *_table(
            ("Frame", "Annotation", "Size", "Mode", "Frame SHA-256", "Evidence"),
            [
                (
                    frame["frame_name"],
                    frame["annotation_kind"],
                    f"{frame['width']} x {frame['height']}",
                    frame["mode"],
                    f"`{frame['frame_sha256']}`",
                    "computed_local",
                )
                for frame in inventory["frames"]
            ],
        ),
        "",
        "## 5. Instance/semantic consistency",
        "",
        f"Definition (`documented_local`): `{instance_semantic['definition']}`.",
        "",
        *_table(
            ("Property", "Value", "Evidence"),
            [
                ("Frames checked", instance_semantic["frames_checked"], "computed_local"),
                ("Frames exact", instance_semantic["frames_exact_match"], "computed_local"),
                ("Frames mismatched", instance_semantic["frames_mismatched"], "computed_local"),
                (
                    "Extra instance pixels",
                    instance_semantic["extra_instance_pixels"],
                    "computed_local",
                ),
                (
                    "Missing instance pixels",
                    instance_semantic["missing_instance_pixels"],
                    "computed_local",
                ),
                (
                    "Semantic-only frames excluded",
                    instance_semantic["semantic_only_frames_excluded"],
                    "computed_local",
                ),
            ],
        ),
        "",
        "A mismatch is a hard exit-2 failure and is never serialized as this success "
        "shape (`computed_local`).",
        "",
        "## 6. Coverage, categories and object scale",
        "",
        *_table(
            ("Coverage property", "Value", "Evidence"),
            [
                ("Total anomaly pixels", coverage["total_anomaly_pixels"], "computed_local"),
                ("Total pixels", coverage["total_pixels"], "computed_local"),
                (
                    "Pooled fraction",
                    f"{coverage['pooled_fraction']:.8f}",
                    "computed_local",
                ),
                (
                    "Pooled percent",
                    f"{coverage['pooled_percent']:.6f}",
                    "computed_local",
                ),
                (
                    "Minimum per-frame percent",
                    f"{coverage['minimum_percent']:.6f}",
                    "computed_local",
                ),
                (
                    "Maximum per-frame percent",
                    f"{coverage['maximum_percent']:.6f}",
                    "computed_local",
                ),
                (
                    "Median per-frame percent",
                    f"{coverage['median_percent']:.6f}",
                    "computed_local",
                ),
                (
                    "Frames below 1 percent",
                    ", ".join(coverage["below_one_percent"]),
                    "computed_local",
                ),
            ],
        ),
        "",
        "Definitions (`documented_local`): "
        + "; ".join(f"`{key}` = {value}" for key, value in coverage["definitions"].items())
        + ".",
        "",
        *_table(
            ("Frame", "Anomaly pixels", "Fraction", "Percent", "Evidence"),
            [
                (
                    row["frame_name"],
                    row["anomaly_pixels"],
                    f"{row['fraction']:.8f}",
                    f"{row['percent']:.6f}",
                    "computed_local",
                )
                for row in coverage["per_frame"]
            ],
        ),
        "",
        *_table(
            ("Object category", "Frames", "Evidence"),
            [(name, count, "computed_local") for name, count in categories["counts"].items()],
        ),
        "",
        f"Classification (`computed_local`): `{categories['classification']}`. Filename "
        "prefixes are object categories, not scene IDs or split units.",
        "",
        *_table(
            ("Object-scale property", "Value", "Evidence"),
            [
                ("ROI area below 1024", object_scale["roi_area_below_1024"], "computed_local"),
                (
                    "Both dimensions below 32",
                    object_scale["both_dimensions_below_32"],
                    "computed_local",
                ),
                (
                    "Either dimension below 32",
                    object_scale["either_dimension_below_32"],
                    "computed_local",
                ),
                (
                    "Median ROI equivalent square (px)",
                    f"{object_scale['median_roi_equivalent_square_px']:.1f}",
                    "computed_local",
                ),
                (
                    "Median ROI width (px)",
                    f"{object_scale['median_roi_width_px']:.1f}",
                    "computed_local",
                ),
                (
                    "Median ROI height (px)",
                    f"{object_scale['median_roi_height_px']:.1f}",
                    "computed_local",
                ),
                (
                    "Median mask equivalent square (px)",
                    f"{object_scale['median_mask_equivalent_square_px']:.1f}",
                    "computed_local",
                ),
                ("Denominator", object_scale["denominator"], "computed_local"),
            ],
        ),
        "",
        "Definitions (`documented_local`): "
        + "; ".join(f"`{key}` = {value}" for key, value in object_scale["definitions"].items())
        + ".",
        "",
        "No single small-object definition is presented as the only truth (`computed_local`).",
        "",
        "## 7. Instance mapping, ROI and duplicates",
        "",
        *_table(
            ("Mapping property", "Value", "Evidence"),
            [
                ("Frames checked", mapping["frames_checked"], "computed_local"),
                ("Frames agreeing", mapping["frames_agreeing"], "computed_local"),
                ("Frames disagreeing", mapping["frames_disagreeing"], "computed_local"),
                (
                    "Disagreeing frames",
                    ", ".join(mapping["disagreeing_frames"]),
                    "computed_local",
                ),
                (
                    "Weaker existing test",
                    f"{mapping['existing_test_check']['name']} = "
                    f"{mapping['existing_test_check']['passes']}",
                    "computed_local",
                ),
            ],
        ),
        "",
        "The order mapping is `mask value k == instances[k-1].id`; it is not promoted "
        "above the weaker existing check (`computed_local`).",
        "",
        *_table(
            ("Frame", "Mask value", "Index position", "Index id", "Evidence"),
            [
                (
                    row["frame_name"],
                    row["mask_value"],
                    row["index_position"],
                    row["index_id"],
                    "computed_local",
                )
                for row in mapping["mismatches"]
            ],
        ),
        "",
        *_table(
            ("ROI property", "Value", "Evidence"),
            [
                ("Instances checked", roi["instances_checked"], "computed_local"),
                ("Out of bounds", roi["out_of_bounds"], "computed_local"),
                ("Non-tight", roi["non_tight"], "computed_local"),
                ("Centroids inside", roi["centroids_inside"], "computed_local"),
            ],
        ),
        "",
        "Definitions (`documented_local`): "
        + "; ".join(f"`{key}` = {value}" for key, value in roi["definitions"].items())
        + ".",
        "",
        *_table(
            ("Out-of-bounds frame", "Mask value", "Evidence"),
            [
                (row["frame_name"], row["mask_value"], "computed_local")
                for row in roi["out_of_bounds_instances"]
            ],
        ),
        "",
        *_table(
            ("Non-tight frame", "Mask value", "Evidence"),
            [
                (row["frame_name"], row["mask_value"], "computed_local")
                for row in roi["non_tight_instances"]
            ],
        ),
        "",
        "ROIs and masks are reported without clipping or rewriting (`computed_local`).",
        "",
        f"Duplicate method (`documented_local`): `{duplicates['dhash_method']}`.",
        "",
        *_table(
            ("Duplicate method", "Pairs", "Evidence"),
            [
                ("Exact raw-file SHA-256", duplicates["exact_pairs"], "computed_local"),
                ("Decoded RGB pixel buffer", duplicates["decoded_pairs"], "computed_local"),
                ("dHash distance <= 6", duplicates["dhash_pairs"], "computed_local"),
            ],
        ),
        "",
        *[
            f"- Limitation (`computed_local`): {statement}"
            for statement in duplicates["limitations"]
        ],
        "",
        "## 8. Credits, licensing and provenance",
        "",
        *_table(
            ("Credit property", "Value", "Evidence"),
            [
                ("Frames with credit entries", credits["coverage"], "computed_local"),
                ("Missing entries", credits["missing_entries"], "computed_local"),
                (
                    "Missing per-image licence tokens",
                    ", ".join(credits["missing_licence_tokens"]),
                    "unresolved",
                ),
                (
                    "Missing source URLs",
                    ", ".join(credits["missing_source_urls"]),
                    "unresolved",
                ),
                (
                    "Source groups / frames",
                    f"{source_group_count} / {source_group_frames}",
                    "computed_local",
                ),
            ],
        ),
        "",
        "Missing per-image tokens remain `unresolved`, not evidence that an image is "
        "unlicensed (`unresolved`). Source groups are attribution-derived, not scene IDs "
        "(`computed_local`).",
        "",
        *_table(
            ("Group", "Source URL", "Frames", "Frame count", "Evidence"),
            [
                (
                    group["group_id"],
                    group["source_url"] if group["source_url"] is not None else "null",
                    ", ".join(group["frames"]),
                    group["frame_count"],
                    "computed_local",
                )
                for group in credits["source_groups"]
            ],
        ),
        "",
        *_table(
            ("Frame", "Licence tokens", "Source URL", "Attribution", "Evidence"),
            [
                (
                    entry["frame_name"],
                    ", ".join(entry["licence_tokens"]) if entry["licence_tokens"] else "none",
                    entry["source_url"] if entry["source_url"] is not None else "null",
                    entry["attribution"],
                    "computed_local" if entry["licence_tokens"] else "unresolved",
                )
                for entry in credits["entries"]
            ],
        ),
        "",
        *_table(
            ("Licensing claim", "Value", "Evidence"),
            [
                ("Annotation licence", credits["annotation_licence_claim"], "documented_local"),
                (
                    "Annotation sources",
                    ", ".join(credits["annotation_licence_sources"]),
                    "documented_local",
                ),
                (
                    "Annotation terms URL",
                    credits["annotation_licence_terms_url"],
                    "documented_local",
                ),
                ("Code licence", credits["code_licence"], "documented_local"),
                ("Code licence source", credits["code_licence_source"], "documented_local"),
                ("Code licence scope", credits["code_licence_scope"], "documented_local"),
                ("Legal conclusion", credits["legal_conclusion"], "documented_local"),
            ],
        ),
        "",
        "The annotation and code licence statements are local documented claims, not legal "
        "advice or independently verified terms (`documented_local`). Local attribution is "
        "not proof of redistribution rights (`upstream_unverified`).",
        "",
        *_table(
            ("Provenance property", "Value", "Evidence"),
            [
                ("Citation", provenance["citation"], "documented_local"),
                (
                    "Release identifier",
                    provenance["release_identifier"]
                    if provenance["release_identifier"] is not None
                    else "null",
                    "upstream_unverified",
                ),
                ("Upstream status", provenance["upstream_status"], "upstream_unverified"),
                ("Scene identity", provenance["scene_identity"], "unresolved"),
                (
                    "Filename prefix is scene ID",
                    provenance["filename_prefix_is_scene_id"],
                    "computed_local",
                ),
                (
                    "Local attribution is redistribution proof",
                    provenance["local_attribution_is_redistribution_proof"],
                    "upstream_unverified",
                ),
                (
                    "Normal-road source selected",
                    provenance["normal_road_source_selected"],
                    "computed_local",
                ),
            ],
        ),
        "",
        "## 9. Documented claims, limitations and unresolved items",
        "",
        *_table(
            (
                "Documented claim (`documented_local`)",
                "Computed value (`computed_local`)",
                "Definition",
                "Treatment",
            ),
            [
                (
                    f"{claim['documented_text']} ({claim['documented_source']})",
                    claim["computed_value"],
                    claim["computed_definition"],
                    claim["treatment"],
                )
                for claim in summary["documented_claims"]
            ],
        ),
        "",
        *_table(
            ("Limitation", "Statement", "Evidence", "Source"),
            [
                (
                    limitation["limitation_id"],
                    limitation["statement"],
                    limitation["evidence_class"],
                    limitation["source"] if limitation["source"] is not None else "null",
                )
                for limitation in summary["limitations"]
            ],
        ),
        "",
        *_table(
            ("Unresolved item", "Statement", "Evidence", "Source", "Status"),
            [
                (
                    item["item_id"],
                    item["statement"],
                    item["evidence_class"],
                    item["source"],
                    item["status"],
                )
                for item in provenance["unresolved_items"]
            ],
        ),
        "",
        *_table(
            ("Open item", "Status", "Evidence"),
            [(item_id, status, "unresolved") for item_id, status in provenance["p0_status"].items()]
            + [("G10", provenance["g10_status"], "unresolved")],
        ),
        "",
        "P0-1 through P0-4, G10 and the ADR-0010 threshold contradiction remain open "
        "(`unresolved`). The audit makes no model, metric, threshold, class-map, split or "
        "promotion decision (`documented_local`).",
        "",
        "## 10. Validation and output integrity",
        "",
        *_table(
            ("Validation item", "Value", "Evidence"),
            [
                (
                    "Schema",
                    "Draft 2020-12 validation passed before rendering",
                    "computed_local",
                ),
                ("Canonical command", env["command"], "computed_local"),
                ("Source JSON SHA-256", f"`{source_json_sha256}`", "computed_local"),
                ("Output set", "`roadanomaly-eda.json`, `roadanomaly-eda.md`", "computed_local"),
                ("Check mode", CHECK_COMMAND, "documented_local"),
            ],
        ),
        "",
        "The JSON is authoritative; this report is derived from validated JSON bytes and "
        "adds only the source digest above (`computed_local`). The two output files are "
        "replaced individually, so a crash or second-replacement failure can leave a mixed "
        "pair that check mode detects (`computed_local`).",
        "",
        "No class map, split, split hash, manifest, experiment record, figure, overlay, "
        "review ledger or normal-road readiness report was created (`computed_local`).",
        "",
        "**Claim classification** (`computed_local`)",
        "",
        *_table(
            ("Claim ID", "Text", "Evidence", "Value", "Definition", "Source"),
            [
                (
                    claim["claim_id"],
                    claim["text"],
                    claim["evidence_class"],
                    _claim_value_text(claim["value"]),
                    claim["definition"] if claim["definition"] is not None else "null",
                    claim["source"] if claim["source"] is not None else "null",
                )
                for claim in summary["claims"]
            ],
        ),
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
