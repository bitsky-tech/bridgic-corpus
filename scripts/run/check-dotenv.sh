#!/bin/bash
# check-dotenv.sh — Validate LLM configuration for bridgic projects.
#
# Checks that required LLM variables are available from either
# environment variables or .env file. Never prints values.
#
# Usage:
#   check-dotenv.sh [PROJECT_DIR]   (defaults to current directory)
#
# Exit codes:
#   0  All variables present
#   1  Missing variables (names printed to stdout)

set -euo pipefail

PROJECT_DIR="${1:-.}"
cd "$PROJECT_DIR"

REQUIRED_VARS=("LLM_API_KEY" "LLM_API_BASE" "LLM_MODEL")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    # 1. Already in environment?
    if [ -n "${!var:-}" ]; then
        continue
    fi
    # 2. Defined in .env with a non-empty value?
    if [ -f .env ] && grep -qE "^${var}=.+" .env; then
        continue
    fi
    MISSING_VARS+=("$var")
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "MISSING_VARS: ${MISSING_VARS[*]}"
    echo "Set them via 'export' or add to .env, then re-run."
    exit 1
fi

echo "=== DOTENV_OK ==="
echo "All required variables present: ${REQUIRED_VARS[*]}"
