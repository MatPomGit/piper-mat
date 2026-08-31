#!/usr/bin/env bash
set -euo pipefail

CONFIG="${CONFIG:-configs/pl_PL-mateusz-medium.json}"

python scripts/train_sessions.py --config "$CONFIG" "$@"
