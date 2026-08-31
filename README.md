# piper-mat

`piper-mat` jest eksperymentalnym forkiem [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl) ukierunkowanym na przygotowanie, trenowanie, walidację i publikację własnego polskiego głosu **`pl_PL-mateusz-medium`** dla silnika Piper TTS.

Repozytorium zachowuje upstreamową implementację Pipera w `src/piper` oraz dodaje warstwę projektu głosu: konfigurację treningu, walidację datasetu, dokumentację eksperymentu, karty datasetu i modelu oraz lekkie kontrole CI.

## Status

Projekt jest w fazie rozwoju. Kod inferencji i treningu pochodzi z Piper, natomiast workflow `pl_PL-mateusz-medium` jest stopniowo wydzielany do powtarzalnej struktury eksperymentalnej.

Aktualne cele:

1. zwalidować i ustabilizować dataset,
2. uzyskać powtarzalny trening na podstawie jawnej konfiguracji,
3. eksportować model do ONNX i wykonywać smoke test inferencji,
4. oceniać jakość i wydajność modelu,
5. publikować model wraz z `MODEL_CARD.md`, próbkami i informacją licencyjną.

## Struktura repozytorium

```text
piper-mat/
├── .github/workflows/          # lekkie kontrole CI
├── configs/                    # wersjonowane konfiguracje eksperymentów
├── dataset/                    # metadane datasetu i karta datasetu
├── docs/                       # dokumentacja Pipera i projektu głosu
├── models/                     # karty modeli, bez ciężkich artefaktów treningowych
├── samples/                    # krótkie próbki referencyjne i syntetyczne
├── scripts/                    # walidacja, eksport i narzędzia projektu głosu
├── src/piper/                  # upstreamowy kod Piper
├── tests/                      # testy upstreamu i przyszłe testy regresyjne PL
├── checkpoints/                # lokalne checkpointy, docelowo poza Git
└── train.sh                    # prosty punkt wejścia do treningu
```

Ciężkie checkpointy i finalne modele ONNX powinny być publikowane jako GitHub Releases lub w repozytorium modeli na Hugging Face, a nie jako zwykłe pliki śledzone w historii Git.

## Szybki start: trening

### 1. Środowisko

Linux:

```bash
git clone https://github.com/MatPomGit/piper-mat.git
cd piper-mat
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[train]'
./build_monotonic_align.sh
python3 setup.py build_ext --inplace
```

Windows wymaga zgodnego środowiska kompilacyjnego dla rozszerzenia Cython. Szczegóły znajdują się w `docs/TRAINING.md` i `docs/ALIGNMENTS.md`.

### 2. Walidacja datasetu

```bash
python scripts/validate_dataset.py \
  --metadata dataset/metadata.csv \
  --audio-dir dataset/wavs
```

Walidator sprawdza spójność metadanych i podstawowe parametry plików WAV. Przed właściwym treningiem raport powinien nie zawierać błędów.

### 3. Konfiguracja eksperymentu

Referencyjna konfiguracja znajduje się w:

```text
configs/pl_PL-mateusz-medium.json
```

Plik zapisuje parametry, które powinny być raportowane przy każdym treningu. `train.sh` pozostaje zgodny z interfejsem `python -m piper.train fit`.

### 4. Trening

```bash
./train.sh
```

Przed uruchomieniem należy wskazać prawidłowe ścieżki do datasetu, cache, katalogu wyjściowego i checkpointu bazowego.

### 5. Eksport ONNX

```bash
python3 -m piper.train.export_onnx \
  --checkpoint /path/to/checkpoint.ckpt \
  --output-file /path/to/pl_PL-mateusz-medium.onnx
```

Finalny głos Piper składa się co najmniej z:

```text
pl_PL-mateusz-medium.onnx
pl_PL-mateusz-medium.onnx.json
MODEL_CARD.md
```

## Dataset i model

Opis datasetu znajduje się w `dataset/DATASET_CARD.md`. Informacje o finalnym modelu i wymagane dane dotyczące treningu znajdują się w `models/pl_PL-mateusz-medium/MODEL_CARD.md`.

Pola oznaczone jako `TODO` muszą zostać uzupełnione na podstawie faktycznego datasetu i zakończonego eksperymentu. Nie należy wpisywać szacowanych wyników jako wyników pomiaru.

## Walidacja jakości

Docelowa ewaluacja obejmuje trzy grupy miar:

- zrozumiałość: WER i CER,
- jakość i podobieństwo głosu: odsłuch ekspercki/MOS oraz speaker similarity,
- wydajność: RTF, opóźnienie pierwszego audio, użycie RAM/CPU i rozmiar modelu.

Plan ewaluacji oraz dalszych prac znajduje się w `docs/ROADMAP.md`.

## Dokumentacja

```bash
python3 -m pip install 'mkdocs>=1.6,<2'
mkdocs serve
```

Weryfikacja dokumentacji:

```bash
mkdocs build --strict
```

## Pochodzenie i licencja

Kod Pipera w tym repozytorium pochodzi z projektu `OHF-Voice/piper1-gpl` i jest objęty licencją **GPL-3.0-or-later**. Pełny tekst licencji znajduje się w `COPYING`.

Licencja kodu nie określa automatycznie licencji datasetu ani wytrenowanego modelu. Warunki dla tych artefaktów muszą być opisane osobno w `dataset/DATASET_CARD.md` i `models/pl_PL-mateusz-medium/MODEL_CARD.md` przed ich publiczną dystrybucją.

## Upstream

- Piper: https://github.com/OHF-Voice/piper1-gpl
- eSpeak NG: https://github.com/espeak-ng/espeak-ng
- Piper voices: https://huggingface.co/rhasspy/piper-voices

## Autor projektu głosu

Mateusz Pomianek
