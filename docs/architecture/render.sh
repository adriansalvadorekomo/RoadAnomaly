#!/usr/bin/env bash
# Render the C4 views from workspace.dsl and refresh the asset manifest.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"

if [[ ! -x "$PYTHON" ]]; then
  PYTHON=python3
fi

"$PYTHON" "$ROOT/docs/architecture/render.py"
