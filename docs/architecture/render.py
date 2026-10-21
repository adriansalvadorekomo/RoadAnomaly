"""Render the Structurizr C4 views to committed PNGs.

Structurizr CLI does not export PNG directly; the official workflow is a static
site rendered in a headless browser. This script pins the CLI, exports the
static site, hides the viewer chrome and captures each view with Chromium.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image

CLI_VERSION = "v2025.11.09"
CLI_URL = f"https://github.com/structurizr/cli/releases/download/{CLI_VERSION}/structurizr-cli.zip"
CACHE_ROOT = Path.home() / ".cache" / "roadanomaly"
VIEWS = {
    "c1-system-context": (1400, 900),
    "c2-offline-pipeline": (1400, 3000),
}
PADDING = 32


def _find_cli() -> Path:
    configured = os.environ.get("STRUCTURIZR_CLI")
    if configured:
        path = Path(configured).expanduser()
        if path.is_dir():
            path = path / "structurizr.sh"
        if path.is_file():
            return path
        raise SystemExit(f"STRUCTURIZR_CLI does not point to a CLI: {path}")

    cache = CACHE_ROOT / f"structurizr-cli-{CLI_VERSION}"
    script = cache / "structurizr.sh"
    if script.is_file():
        return script

    cache.parent.mkdir(parents=True, exist_ok=True)
    archive = CACHE_ROOT / f"structurizr-cli-{CLI_VERSION}.zip"
    if not archive.is_file():
        print(f"downloading {CLI_URL}")
        urllib.request.urlretrieve(CLI_URL, archive)
    cache.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(cache)
    script.chmod(0o755)
    return script


def _find_browser() -> str:
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        path = shutil.which(name)
        if path:
            return path
    raise SystemExit("install Chromium (or set PATH) to render the C4 diagrams")


def _patch_viewer(index: Path) -> None:
    html = index.read_text(encoding="utf-8")
    head = """
    <style>
      #introductionModal, .modal-backdrop { display: none !important; }
      .structurizrDiagramMetadata { display: none !important; }
      body { overflow: hidden; }
    </style>
    """
    body = """
    <script>
      window.addEventListener('load', function () {
        document.querySelectorAll('.modal-backdrop').forEach((el) => el.remove());
        document.body.classList.remove('modal-open');
      });
    </script>
    """
    html = html.replace("</head>", f"{head}</head>", 1)
    html = html.replace("</body>", f"{body}</body>", 1)
    index.write_text(html, encoding="utf-8")


def _crop(path: Path) -> tuple[int, int]:
    image = Image.open(path).convert("RGB")
    non_white = image.convert("L").point(lambda value: 0 if value > 250 else 255)
    box = non_white.getbbox()
    if box is None:
        raise SystemExit(f"{path} contains no visible diagram")
    left = max(0, box[0] - PADDING)
    top = max(0, box[1] - PADDING)
    right = min(image.width, box[2] + PADDING)
    bottom = min(image.height, box[3] + PADDING)
    cropped = image.crop((left, top, right, bottom))
    cropped.save(path, optimize=True)
    return cropped.size


def main() -> None:
    arch_dir = Path(__file__).resolve().parent
    workspace = arch_dir / "workspace.dsl"
    output_dir = arch_dir / "diagrams"
    output_dir.mkdir(parents=True, exist_ok=True)

    cli = _find_cli()
    subprocess.run(
        [str(cli), "validate", "-w", str(workspace)],
        check=True,
    )

    browser = _find_browser()
    with tempfile.TemporaryDirectory(prefix="roadanomaly-c4-") as temporary:
        site = Path(temporary) / "site"
        site.mkdir()
        subprocess.run(
            [
                str(cli),
                "export",
                "-w",
                str(workspace),
                "-f",
                "static",
                "-o",
                str(site),
            ],
            check=True,
        )
        _patch_viewer(site / "index.html")

        rendered: dict[str, dict[str, object]] = {}
        for key, (width, height) in VIEWS.items():
            png = output_dir / f"{key}.png"
            raw = Path(temporary) / f"{key}.raw.png"
            url = (site / "index.html").as_uri() + f"#{key}"
            subprocess.run(
                [
                    browser,
                    "--headless=new",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--hide-scrollbars",
                    "--force-device-scale-factor=2",
                    f"--window-size={width},{height}",
                    "--virtual-time-budget=8000",
                    "--run-all-compositor-stages-before-draw",
                    f"--screenshot={raw}",
                    url,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            rendered[key] = {
                "file": png.name,
                "width": None,
                "height": None,
            }
            png.write_bytes(raw.read_bytes())
            image_width, image_height = _crop(png)
            rendered[key]["width"] = image_width
            rendered[key]["height"] = image_height
            print(f"wrote {png} ({image_width}x{image_height})")

    manifest = {
        "renderer": f"structurizr-cli {CLI_VERSION} + headless Chromium (static site)",
        "workspace_sha256": hashlib.sha256(workspace.read_bytes()).hexdigest(),
        "views": rendered,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {output_dir / 'manifest.json'}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        sys.exit(f"render command failed: {error}")
