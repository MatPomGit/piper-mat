#!/usr/bin/env bash
set -euo pipefail

readonly PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CONFIG="${CONFIG:-configs/pl_PL-mateusz-medium.json}"

if [[ -x "${PROJECT_DIR}/.venv/bin/python" ]]; then
    PYTHON="${PROJECT_DIR}/.venv/bin/python"
else
    PYTHON="${PYTHON:-python3}"
fi

cd "${PROJECT_DIR}"
exec "${PYTHON}" scripts/train_sessions.py --config "${CONFIG}" "$@"
