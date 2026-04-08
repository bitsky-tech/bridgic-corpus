#!/bin/bash
# setup-env.sh — Python virtual environment setup for bridgic projects.
#
# Checks uv, creates pyproject.toml from template if absent,
# installs Python dependencies and browser binaries.
#
# Usage:
#   setup-env.sh [PROJECT_DIR]   (defaults to current directory)
#
# Exit codes:
#   0  Environment ready
#   1  uv not installed

set -euo pipefail

PROJECT_DIR="${1:-.}"
cd "$PROJECT_DIR"

# ──────────────────────────────────────────────
# 1. Check uv
# ──────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
    echo "ERROR: uv is not installed."
    echo "Install it via: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# ──────────────────────────────────────────────
# 2. Create pyproject.toml (skip if exists)
# ──────────────────────────────────────────────
if [ ! -f pyproject.toml ]; then
    PROJECT_NAME=$(basename "$(pwd)")
    cat > pyproject.toml <<TOML
[project]
name = "${PROJECT_NAME}"
version = "0.1.0"
description = "A bridgic automation project"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "bridgic-browser>=0.0.3",
    "bridgic-core>=0.3.0",
    "bridgic-llms-openai>=0.1.3",
    "bridgic-amphibious==0.1.0.dev12",
    "dotenv>=0.9.9",
]

[[tool.uv.index]]
name = "btsk-repo"
url = "http://8.130.156.165:3141/btsk/test/+simple"
explicit = true

[tool.uv.sources]
bridgic-amphibious = { index = "btsk-repo" }
TOML
    echo "Created pyproject.toml"
else
    echo "pyproject.toml already exists, skipping"
fi

# ──────────────────────────────────────────────
# 3. Install dependencies
# ──────────────────────────────────────────────
echo "Running uv sync..."
uv sync

# ──────────────────────────────────────────────
# 4. Install browser binaries
# ──────────────────────────────────────────────
echo "Ensuring Playwright Chromium is installed..."
uv run playwright install chromium

echo ""
echo "=== ENV_READY ==="
echo "python: $(uv run python --version 2>&1)"
echo "uv: $(uv --version 2>&1)"
echo "project_dir: $(pwd)"
