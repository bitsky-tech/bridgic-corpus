#!/bin/bash
# setup-env.sh — Ensure uv is installed and initialize a uv project.
#
# 1. Checks if uv is on PATH. If not, auto-installs it (macOS/Linux/Windows).
# 2. Runs `uv init --bare` in the working directory if pyproject.toml is absent.
#
# Usage:
#   setup-env.sh [PROJECT_DIR]   (defaults to current directory)
#
# Exit codes:
#   0  uv available and pyproject.toml present
#   1  uv installation failed
#   2  uv init failed

set -euo pipefail

PROJECT_DIR="${1:-.}"
cd "$PROJECT_DIR"

# ──────────────────────────────────────────────
# 1. Ensure uv is installed
# ──────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
    echo "uv not found — installing ..."
    case "$(uname -s)" in
        CYGWIN*|MINGW*|MSYS*|Windows_NT*)
            # Windows (Git Bash / MSYS2 / Cygwin)
            powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex" \
                || { echo "Error: uv installation failed on Windows."; exit 1; }
            ;;
        *)
            # macOS / Linux / other Unix-like
            curl -LsSf https://astral.sh/uv/install.sh | sh \
                || { echo "Error: uv installation failed."; exit 1; }
            ;;
    esac

    # Reload PATH so the current shell can find uv
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

    if ! command -v uv &>/dev/null; then
        echo "Error: uv was installed but not found on PATH."
        echo "You may need to restart your shell or add ~/.local/bin to PATH."
        exit 1
    fi

    echo "uv installed successfully."
fi

echo "uv: $(uv --version 2>&1)"

# ──────────────────────────────────────────────
# 2. Initialize uv project (bare — no main.py, README, etc.)
# ──────────────────────────────────────────────
if [ ! -f pyproject.toml ]; then
    echo "No pyproject.toml found — running uv init --bare ..."
    uv init --bare || { echo "Error: uv init failed."; exit 2; }
    echo "Created pyproject.toml"
else
    echo "pyproject.toml already exists, skipping init"
fi

echo ""
echo "=== ENV_READY ==="
echo "uv: $(uv --version 2>&1)"
echo "project_dir: $(pwd)"
