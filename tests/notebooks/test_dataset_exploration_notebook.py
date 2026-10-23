from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = ROOT / "dl" / "notebooks" / "road-anomaly-dataset-exploration.ipynb"

REQUIRED_HEADINGS = [
    "## 1. Research objective and dataset description",
    "## 2. Audit status and dataset integrity",
    "## 3. Annotation coverage and category distributions",
    "## 4. Object counts and scale distributions",
    "## 5. Region of Interest (ROI) analysis",
    "## 6. Visual inspection of images and annotations",
    "## 7. Limitations, potential biases, and open questions",
    "## 8. Implications for future Deep Learning experiments",
    "## 9. Evidence-based conclusions and next steps",
    "## 10. Reproducibility and workflow",
]


def _load_notebook() -> dict[str, Any]:
    assert NOTEBOOK_PATH.is_file(), f"missing notebook: {NOTEBOOK_PATH}"
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    assert isinstance(notebook, dict)
    return notebook


def _source(cell: dict[str, Any]) -> str:
    source = cell["source"]
    return "".join(source) if isinstance(source, list) else str(source)


def _code_cells(notebook: dict[str, Any]) -> list[dict[str, Any]]:
    return [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]


def test_notebook_is_structurally_valid_and_stripped() -> None:
    """The committed notebook is valid JSON, uses nbformat 4 and carries no execution state."""
    notebook = _load_notebook()
    assert notebook["nbformat"] == 4
    assert notebook["metadata"]["kernelspec"]["name"] == "python3"
    assert notebook["metadata"]["roadanomaly"]["role"] == "scientific-eda"
    assert notebook["metadata"]["roadanomaly"]["authoritative"] is False

    identifiers = [cell["id"] for cell in notebook["cells"]]
    assert len(identifiers) == len(set(identifiers))
    for cell in notebook["cells"]:
        assert cell["cell_type"] in {"markdown", "code"}
        assert isinstance(cell["source"], list)
        if cell["cell_type"] == "code":
            assert cell["execution_count"] is None
            assert cell["outputs"] == []


def test_notebook_contains_the_ten_required_sections_in_order() -> None:
    """The exploration follows the ten-section scientific contract, in order, exactly once."""
    notebook = _load_notebook()
    headings = [
        _source(cell).splitlines()[0]
        for cell in notebook["cells"]
        if cell["cell_type"] == "markdown" and _source(cell).startswith("## ")
    ]
    assert headings == REQUIRED_HEADINGS


def test_notebook_code_cells_are_syntactically_valid_python() -> None:
    """Every code cell parses as Python without relying on notebook magics or shell escapes."""
    notebook = _load_notebook()
    for index, cell in enumerate(_code_cells(notebook)):
        source = _source(cell)
        assert not source.lstrip().startswith(("!", "%")), f"cell {index} uses an IPython magic"
        ast.parse(source, filename=f"cell-{index}")


def test_notebook_uses_the_canonical_evidence_interface() -> None:
    """The notebook validates the canonical JSON and renders the report instead of recomputing it."""
    notebook = _load_notebook()
    source = "\n".join(_source(cell) for cell in _code_cells(notebook))
    assert "docs" in source and "roadanomaly-eda.json" in source
    assert "roadanomaly-eda.md" in source
    assert 'importlib.import_module("dl.data.audit")' in source
    assert "audit.validate_summary(SUMMARY)" in source
    assert "audit.render_report(SUMMARY, JSON_DIGEST)" in source
    assert "make data-audit" in source
    assert "make data-audit-check" in source


def test_notebook_has_no_training_stack_or_absolute_paths() -> None:
    """The notebook is a read-only analysis client: no model training, fitting or host paths."""
    notebook = _load_notebook()
    code = "\n".join(_source(cell) for cell in _code_cells(notebook))
    forbidden_imports = ("tensorflow", "keras", "torch", "dl.models", "dl.training")
    for name in forbidden_imports:
        assert name not in code.lower(), f"unexpected training dependency: {name}"
    for pattern in (r"\bfit\s*\(", r"\bsavefig\s*\(", r"\bwrite_text\s*\("):
        assert re.search(pattern, code) is None, (
            f"unexpected side effect or training call: {pattern}"
        )
    assert re.search(r"/home/|/Users/|C:\\\\", code) is None
