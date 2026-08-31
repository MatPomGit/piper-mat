#!/usr/bin/env bash
set -euo pipefail

DATASET_DIR="${DATASET_DIR:-/dataset}"
CACHE_DIR="${CACHE_DIR:-/cache}"
OUTPUT_DIR="${OUTPUT_DIR:-/output}"
CHECKPOINT="${CHECKPOINT:-/checkpoint/base.ckpt}"
VOICE_NAME="${VOICE_NAME:-mateusz}"
BATCH_SIZE="${BATCH_SIZE:-8}"

mkdir -p "$CACHE_DIR" "$OUTPUT_DIR"

if [[ ! -f "$DATASET_DIR/metadata.csv" ]]; then
  echo "Brak pliku: $DATASET_DIR/metadata.csv" >&2
  exit 2
fi

if [[ ! -d "$DATASET_DIR/wavs" ]]; then
  echo "Brak katalogu: $DATASET_DIR/wavs" >&2
  exit 2
fi

if [[ ! -f "$CHECKPOINT" ]]; then
  echo "Brak checkpointu bazowego: $CHECKPOINT" >&2
  exit 2
fi

python -m piper.train fit \
  --data.voice_name "$VOICE_NAME" \
  --data.csv_path "$DATASET_DIR/metadata.csv" \
  --data.audio_dir "$DATASET_DIR/wavs/" \
  --model.sample_rate 22050 \
  --data.espeak_voice "pl" \
  --data.cache_dir "$CACHE_DIR/" \
  --data.config_path "$OUTPUT_DIR/pl_PL-mateusz-medium.onnx.json" \
  --data.batch_size "$BATCH_SIZE" \
  --ckpt_path "$CHECKPOINT"
