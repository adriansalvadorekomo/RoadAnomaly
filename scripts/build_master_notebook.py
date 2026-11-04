"""Build notebooks/0_RoadAnomaly_Master.ipynb: the whole CRISP-DM study in one notebook.

The master is generated from the phase notebooks, which stay the single source of truth: edit a phase
notebook (and re-run it), then rebuild the master with `mise run master`. `--check` exits with an error
when the master is out of date (part of `mise run check`).

What the build does (nothing is executed here; the saved outputs of the phase notebooks are kept):
- phase 1 (notebooks/1_Business_Understanding.md) becomes markdown cells; phases 2 to 6 are copied
  with their code and outputs, in CRISP-DM order;
- each phase keeps its title as a top-level heading (the three modeling notebooks sit under a
  "4 · Modeling" heading), and the headings inside a phase move down accordingly;
- relative links are rewritten for the master's folder, and the "Previous / Next" links of the
  standalone notebooks are dropped, since the phases now follow each other;
- each modeling phase gets a banner naming its binôme, and every one of its code cells starts with a
  comment naming the binôme;
- at the end of each phase, a clean-up cell clears the namespace and the Keras session, so that running
  the master top to bottom behaves like running the phase notebooks one after the other.

Usage: python scripts/build_master_notebook.py [--check]
"""
import argparse
import copy
import json
import posixpath
import re
import sys
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"
MASTER = NOTEBOOKS / "0_RoadAnomaly_Master.ipynb"

BINOMES = {
    "A": ("Ines Trabelsi & Emna Trabelsi", "DeepLabV3+ with transfer learning (frozen ImageNet ResNet50 encoder)",
          "`A_deeplabv3plus`"),
    "B": ("Khaled Gannoun & Adrian Salvador Ekomo Mesi Obono",
          "convolutional autoencoders: a pixel autoencoder (baseline) and a feature-space autoencoder on frozen "
          "VGG16 features (final)", "`B_pixel_ae`, `B_feature_ae`"),
    "C": ("Hejer Mnejja (CNN baseline) & Walid Fehry (U-Nets)",
          "a CNN baseline, a U-Net from scratch and a U-Net with an ImageNet ResNet50 encoder",
          "`C_cnn`, `C_unet`, `C_unet_resnet50`"),
}

# (key, notebook relative to notebooks/, binôme or None, short label for the contents table)
PHASES = [
    ("p2", "2_Data_Understanding.ipynb", None, "2 · Data Understanding", "the data, and the protocol it dictates"),
    ("p3", "3_Data_Preparation.ipynb", None, "3 · Data Preparation", "frozen split, shared loader, the floor to beat"),
    ("p4a", "4_Modeling/A_DeepLabV3Plus.ipynb", "A", "4 · Modeling, Binôme A", "DeepLabV3+"),
    ("p4b", "4_Modeling/B_Autoencoder.ipynb", "B", "4 · Modeling, Binôme B", "autoencoders"),
    ("p4c", "4_Modeling/C_CNN_UNet.ipynb", "C", "4 · Modeling, Binôme C", "CNN and U-Nets"),
    ("p5", "5_Evaluation.ipynb", None, "5 · Evaluation", "the six models on the test split, once"),
    ("p6", "6_XAI.ipynb", None, "6 · XAI", "where (Grad-CAM++) and what (SHAP) for every model"),
]

CLEAN_UP = """# End of {phase}: clean up before the next phase (cell added by scripts/build_master_notebook.py).
# The namespace and the Keras session are cleared, so the next phase starts as in its own kernel. TensorFlow
# settings of the process (GPU memory configuration, deterministic GPU kernels) stay for the whole kernel.
%reset -f
import gc

import keras

keras.backend.clear_session()
gc.collect()"""

LINK = re.compile(r'(\]\()([^)\s]+)(\))|((?:src|href)=")([^"]+)(")')
HEADING = re.compile(r"(#{1,6}) ")
NAVIGATION = re.compile(r"\s*(?:Previous|Next): .*$")


def relink(text, base):
    """Rewrite relative links of a text written in folder `base` (relative to notebooks/) for notebooks/."""
    def fix(target):
        if not base or re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:|#|/", target):
            return target
        path, hash_, fragment = target.partition("#")
        new = posixpath.normpath(posixpath.join(base, path))
        if path.endswith("/") and not new.endswith("/"):
            new += "/"
        return new + hash_ + fragment

    def replace(match):
        if match.group(1):
            return match.group(1) + fix(match.group(2)) + match.group(3)
        return match.group(4) + fix(match.group(5)) + match.group(6)

    return LINK.sub(replace, text)


def shift_headings(text, shift, keep_first=False):
    """Move markdown headings down by `shift` levels (outside fenced code blocks)."""
    lines, fenced, first = [], False, keep_first
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and HEADING.match(line):
            if first:
                first = False
            else:
                level = min(len(HEADING.match(line).group(1)) + shift, 6)
                line = "#" * level + line[len(HEADING.match(line).group(1)):]
        lines.append(line)
    return "\n".join(lines)


def drop_navigation(text):
    """Remove the 'Previous: ... · Next: ...' links of a standalone notebook's title cell."""
    return "\n".join(NAVIGATION.sub("", line) if "**CRISP-DM phase" in line else line for line in text.split("\n"))


def markdown(cell_id, text):
    return nbformat.v4.new_markdown_cell(text, id=cell_id)


def phase_cells(key, relative_path, binome):
    """The cells of one phase notebook, adapted for the master."""
    notebook = nbformat.read(NOTEBOOKS / relative_path, as_version=4)
    base = posixpath.dirname(relative_path)
    modeling = binome is not None
    cells = []
    for index, original in enumerate(notebook.cells):
        cell = copy.deepcopy(original)
        cell.id = f"{key}-{index:03d}"
        if cell.cell_type == "markdown":
            text = relink(cell.source, base)
            if index == 0:
                text = drop_navigation(text)
                # the title stays a heading of the phase level: level 1, or level 2 under "4 · Modeling"
                text = shift_headings(text, 1, keep_first=not modeling)
                if modeling:
                    text = shift_headings(text, 1, keep_first=True)
            else:
                text = shift_headings(text, 2 if modeling else 1)
            cell.source = text
        elif cell.cell_type == "code" and modeling:
            cell.source = f"# Binôme {binome} · {BINOMES[binome][0]}\n" + cell.source
        cells.append(cell)
        if index == 0 and modeling:
            members, approach, models = BINOMES[binome]
            cells.append(markdown(f"{key}-binome", (
                f"> **Binôme {binome} · {members}**  \n"
                f"> {approach[0].upper() + approach[1:]}. Saved models: {models}.  \n"
                f"> Every code cell of this part starts with a comment naming the binôme.")))
    return cells


def readme_section(title):
    """One '## title' section of the README, with its links rewritten for notebooks/."""
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    start = text.index(f"## {title}\n")
    end = text.find("\n## ", start + 1)
    return relink(text[start:end if end != -1 else None].strip(), "..")


def business_cells():
    """Phase 1, a markdown file, split into one cell per section."""
    text = drop_navigation((NOTEBOOKS / "1_Business_Understanding.md").read_text(encoding="utf-8"))
    text = shift_headings(text, 1, keep_first=True)
    sections, current = [], []
    for line in text.split("\n"):
        if line.startswith("### ") and current:
            sections.append("\n".join(current).strip())
            current = []
        current.append(line)
    sections.append("\n".join(current).strip())
    return [markdown(f"p1-{i:03d}", s) for i, s in enumerate(sections) if s and s != "---"]


def cover():
    rows = ["| Phase | Content | Standalone notebook |", "|---|---|---|",
            "| 1 · Business Understanding | goals, success tests, plan | "
            "[`1_Business_Understanding.md`](1_Business_Understanding.md) |"]
    for _, path, binome, label, content in PHASES:
        who = f": {BINOMES[binome][0]}" if binome else ""
        rows.append(f"| {label}{who} | {content} | [`{path}`]({path}) |")
    return "\n".join([
        "# RoadAnomaly — the complete CRISP-DM study",
        "",
        "**Master notebook.** ESPRIT · Deep Learning module · Group of 6 · final submission 8 November 2026.  ",
        "**Authors:** Ines Trabelsi, Emna Trabelsi, Khaled Gannoun, Adrian Salvador Ekomo Mesi Obono, Hejer Mnejja, "
        "Walid Fehry.",
        "",
        "This notebook puts the whole study in one place, phase by phase, in the order of CRISP-DM:",
        "",
        *rows,
        "",
        "**How it is made.** It is generated by `scripts/build_master_notebook.py` (`mise run master`) from the phase "
        "notebooks above, which stay the source: edit a phase notebook, re-run it, then rebuild this one. The code and "
        "the outputs shown are those of the phase notebooks' last runs; only the binôme banners and comments of phase "
        "4 and the clean-up cells between phases are added.",
        "",
        "**Running it.** Top to bottom it does what `mise run pipeline` does, in a single kernel: it retrains the six "
        "models (about 20 minutes on an RTX 4060), evaluates them on the test split once and explains them, rewriting "
        "`models/`, `reports/figures/` and `reports/results/`. The clean-up cell at the end of each phase clears the "
        "namespace and the Keras session, so each phase starts as in its own kernel.",
    ])


def modeling_intro():
    rows = ["| Binôme | Members | Approach | Saved models |", "|---|---|---|---|"]
    for binome, (members, approach, models) in BINOMES.items():
        rows.append(f"| {binome} | {members} | {approach} | {models} |")
    return "\n".join([
        "# 4 · Modeling — three binômes, six models",
        "",
        "The three approaches use the same split, the same loader and the same protocol (phase 3), and every setting "
        "is chosen on the validation split only. Each part below is marked with its binôme, and the training code "
        "explains why each hyper-parameter was chosen.",
        "",
        *rows,
    ])


def closing():
    return "\n".join([
        "# After the study: deployment",
        "",
        "The six models saved in `models/` are served through the same `Predictor` as in phases 5 and 6:",
        "- **API**: `mise run api`, FastAPI on port 8000 (`/health`, `/models`, `/predict`, `/explain`);",
        "- **Demo**: `mise run app`, Streamlit on port 8501 (Detect, Explain, Compare, Test results, Method);",
        "- **Landing page**: `mise run landing`, the Astro page that tells this study, also online at "
        "https://roadanomaly-landing.vercel.app;",
        "- **Docker**: `mise run docker:up` starts the three together.",
        "",
        "The README has the setup, the GPU notes and the architecture diagram.",
    ])


def build():
    first = nbformat.read(NOTEBOOKS / PHASES[0][1], as_version=4)
    master = nbformat.v4.new_notebook(metadata={
        "kernelspec": {"display_name": "Python (roadanomaly)", "language": "python", "name": "roadanomaly"},
        "language_info": first.metadata.get("language_info", {"name": "python"}),
    })
    cells = [markdown("cover", cover()),
             markdown("architecture", readme_section("Architecture")),
             markdown("tldr", readme_section("TL;DR")),
             *business_cells()]
    for position, (key, path, binome, label, _) in enumerate(PHASES):
        if key == "p4a":
            cells.append(markdown("p4-intro", modeling_intro()))
        cells.extend(phase_cells(key, path, binome))
        if position < len(PHASES) - 1:
            cells.append(nbformat.v4.new_code_cell(CLEAN_UP.format(phase=label), id=f"{key}-clean-up"))
    cells.append(markdown("closing", closing()))
    master.cells = cells
    nbformat.validate(master)
    return nbformat.writes(master) + "\n"


def comparable(text):
    """The notebook without its kernel choice: editors rewrite `kernelspec` when a kernel is picked, which is not
    a change of content."""
    notebook = json.loads(text)
    notebook["metadata"].pop("kernelspec", None)
    return notebook


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="fail if the master is not up to date")
    args = parser.parse_args()
    text = build()
    relative = MASTER.relative_to(ROOT)
    if args.check:
        if not MASTER.exists() or comparable(MASTER.read_text(encoding="utf-8")) != comparable(text):
            sys.exit(f"{relative} is out of date: run `mise run master` (python scripts/build_master_notebook.py)")
        print(f"{relative} is up to date")
        return
    MASTER.write_text(text, encoding="utf-8")
    print(f"wrote {relative} ({MASTER.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
