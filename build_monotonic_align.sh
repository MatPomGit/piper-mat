#!/usr/bin/env bash
set -euo pipefail

readonly PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SOURCE_DIR="${PROJECT_DIR}/src/piper/train/vits/monotonic_align"
readonly TARGET_DIR="${SOURCE_DIR}/monotonic_align"

if [[ -x "${PROJECT_DIR}/.venv/bin/python" ]]; then
    PYTHON="${PROJECT_DIR}/.venv/bin/python"
elif [[ -x "${PROJECT_DIR}/.venv/Scripts/python.exe" ]]; then
    PYTHON="${PROJECT_DIR}/.venv/Scripts/python.exe"
else
    PYTHON="${PYTHON:-python3}"
fi

mkdir -p "${TARGET_DIR}"
cd "${SOURCE_DIR}"
rm -f core.c

"${PYTHON}" -m Cython.Build.Cythonize -i core.pyx

shopt -s nullglob
built_extensions=(core*.so core*.pyd)
if (( ${#built_extensions[@]} == 0 )); then
    echo "BŁĄD: kompilacja nie utworzyła rozszerzenia core (.so lub .pyd)." >&2
    exit 1
fi

rm -f "${TARGET_DIR}"/core*.so "${TARGET_DIR}"/core*.pyd
mv "${built_extensions[@]}" "${TARGET_DIR}/"

cd "${PROJECT_DIR}"
"${PYTHON}" -c "from piper.train.vits.monotonic_align import core; print('monotonic_align: OK')"
