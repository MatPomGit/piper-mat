#!/usr/bin/env bash
set -eo pipefail

this_dir="$( cd "$( dirname "$0" )" && pwd )"

# cython extension:
# ./build_monotonic_align.sh

# dev build:
# python3 setup.py build_ext --inplace


# The first column is the name of the audio file (any format supported by [librosa][]), which must be located in `--data.audio_dir` (see below).
# The other column(s) will depend on the [training settings](#settings). By default, the second column is the text that will be passed to [espeak-ng][] for phonemization (similar to `espeak-ng --ipa=3`).

# training script:


python -m piper.train fit \
  --data.voice_name "mateusz" \
  --data.csv_path /dataset/metadata.csv \
  --data.audio_dir /dataset/wavs/ \
  --model.sample_rate 22050 \
  --data.espeak_voice "pl" \
  --data.cache_dir /cache/ \
  --data.config_path /output/pl_PL_mateusz-medium.onyx.json \
  --data.batch_size 8 \
  --ckpt_path /checkpoint/base.ckpt  # optional but highly recommended

# python train.py fit --data.voice_name "mateusz" --data.csv_path "dataset/metadata.csv" --data.audio_dir "dataset/wavs" --model.sample_rate 22050 --data.espeak_voice "pl" --data.cache_dir "cache" --data.config_path "output/pl_PL-mateusz-medium.onnx.json" --data.batch_size 4 --model.warmstart_ckpt "checkpoints/base_clean.ckpt"



