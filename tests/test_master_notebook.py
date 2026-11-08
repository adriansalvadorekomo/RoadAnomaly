"""The master notebook builder: link rewriting, heading levels and navigation links."""
from scripts import build_master_notebook as master


def test_relink_rewrites_relative_links_only():
    text = ("[a](../5_Evaluation.ipynb) [b](https://example.org/x) [c](#top) "
            "![d](../../reports/f.png) [e](../4_Modeling/)")
    out = master.relink(text, "4_Modeling")
    assert "[a](5_Evaluation.ipynb)" in out and "[b](https://example.org/x)" in out and "[c](#top)" in out
    assert "![d](../reports/f.png)" in out and "[e](4_Modeling/)" in out
    assert master.relink("[r](docs/x.png)", "..") == "[r](../docs/x.png)"   # README links, seen from notebooks/
    assert master.relink("[s](2_Data.ipynb#part)", "") == "[s](2_Data.ipynb#part)"


def test_shift_headings_keeps_the_title_and_skips_code_fences():
    text = "# Title\n## Section\n```python\n# a comment, not a heading\n```\n### Sub"
    assert master.shift_headings(text, 1, keep_first=True) == (
        "# Title\n### Section\n```python\n# a comment, not a heading\n```\n#### Sub")
    assert master.shift_headings("###### deepest", 2) == "###### deepest"   # never beyond level 6


def test_navigation_links_of_standalone_notebooks_are_dropped():
    line = "**CRISP-DM phase 2.** Previous: [`1.md`](1.md) · Next: [`3.ipynb`](3.ipynb)"
    assert master.drop_navigation(line) == "**CRISP-DM phase 2.**"
    assert master.drop_navigation("Previous: kept, not a title line") == "Previous: kept, not a title line"


def test_check_ignores_the_kernel_chosen_in_an_editor():
    built = master.build()
    edited = built.replace('"name": "roadanomaly"', '"name": "python3"')
    assert edited != built and master.comparable(edited) == master.comparable(built)
