#!/usr/bin/env bash
set -eo pipefail

this_dir="$( cd "$( dirname "$0" )" && pwd )"

# Na Windowsie struktura folderów środowiska wirtualnego różni się od Linuksa – zamiast bin/ plik aktywacyjny znajduje się w katalogu Scripts/.
if [ -d "${this_dir}/.venv" ]; then
    source "${this_dir}/.venv/Scripts/activate"
fi

cd "${this_dir}/src/piper/train/vits/monotonic_align"
mkdir -p monotonic_align
rm -f core.c
cythonize -i core.pyx
mv core*pyd monotonic_align/
