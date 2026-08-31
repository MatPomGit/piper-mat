# piper-mat

`piper-mat` jest eksperymentalną gałęzią rozwojową projektu [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl), ukierunkowaną na przygotowanie, trenowanie, walidację i publikację własnego polskiego głosu **`pl_PL-mateusz-medium`** dla silnika Piper TTS.

Repozytorium zachowuje bazową implementację Pipera w `src/piper` oraz dodaje warstwę projektu głosu: konfigurację treningu, walidację zbioru danych, dokumentację eksperymentu, karty zbioru danych i modelu oraz lekkie kontrole ciągłej integracji.

## Stan projektu

Projekt jest w fazie rozwoju. Kod wnioskowania i treningu pochodzi z Pipera, natomiast proces tworzenia `pl_PL-mateusz-medium` jest stopniowo wydzielany do powtarzalnej struktury eksperymentalnej.

Aktualne cele:

1. zwalidować i ustabilizować zbiór danych,
2. prowadzić powtarzalny trening możliwy do zatrzymania między sesjami i wznowienia innego dnia,
3. eksportować model do ONNX i wykonywać test poprawności wnioskowania,
4. oceniać jakość i wydajność modelu,
5. publikować model wraz z `MODEL_CARD.md`, próbkami i informacją licencyjną.

## Struktura repozytorium

```text
piper-mat/
├── .github/workflows/          # lekkie kontrole ciągłej integracji
├── configs/                    # wersjonowane konfiguracje eksperymentów i sesji
├── dataset/                    # metadane i karta zbioru danych
├── docs/                       # dokumentacja Pipera i projektu głosu
├── models/                     # karty modeli bez ciężkich artefaktów treningowych
├── samples/                    # krótkie próbki referencyjne i syntetyczne
├── scripts/                    # trening, walidacja, raporty, eksport i ewaluacja
├── src/piper/                  # bazowy kod Piper
├── tests/                      # testy projektu i testy regresyjne języka polskiego
├── checkpoints/                # bazowe punkty kontrolne
├── train.sh                    # trening etapowy Linux
└── train.ps1                   # trening etapowy Windows PowerShell
```

Duże punkty kontrolne i finalne modele ONNX powinny być publikowane jako wydania GitHub lub w repozytorium modeli na Hugging Face, a nie jako zwykłe pliki śledzone w historii Git.

## Szybki start: trening

### 1. Środowisko

Linux:

```bash
git clone https://github.com/MatPomGit/piper-mat.git
cd piper-mat
git lfs pull
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[train]'
./build_monotonic_align.sh
python3 setup.py build_ext --inplace
```

Windows wymaga zgodnego środowiska kompilacyjnego dla rozszerzenia Cython. Szczegóły znajdują się w `docs/TRAINING.md`, `docs/STAGED_TRAINING.md` i `docs/ALIGNMENTS.md`.

### 2. Kontrola gotowości

```bash
python scripts/check_training_ready.py
```

Skrypt sprawdza konfigurację, plan sesji, Git LFS, zbiór danych, bazowy punkt kontrolny, zależności treningowe, rozszerzenie `monotonic_align` i podstawową ilość wolnego miejsca.

### 3. Walidacja zbioru danych

```bash
python scripts/validate_dataset.py \
  --metadata dataset/metadata.csv \
  --audio-dir dataset/wavs
```

Walidator sprawdza spójność metadanych i parametry plików WAV. Przed właściwym treningiem raport nie powinien zawierać błędów.

### 4. Plan treningu etapowego

Kanoniczna konfiguracja znajduje się w:

```text
configs/pl_PL-mateusz-medium.json
```

Domyślny plan:

```json
"epochs_per_session": [250, 250, 250, 250]
```

oznacza cztery niezależne sesje po 250 dodatkowych epok. Plan można zmienić np. na 3–6 podejść.

### 5. Uruchomienie następnej sesji

Linux:

```bash
./train.sh
```

Windows PowerShell:

```powershell
.\train.ps1
```

Po zakończeniu sesji automatycznie powstają:

- trwały `last.ckpt` używany do kolejnego wznowienia,
- najlepszy punkt według `val_mel`, jeśli jest dostępny,
- najlepszy punkt według `val_mos`, jeśli jest dostępny,
- `REPORT.md`,
- `summary.json`,
- wykresy SVG z metryk TensorBoard,
- aktualny `output/training_state/state.json`.

Po zakończeniu sesji komputer można wyłączyć. W kolejnym dniu uruchamia się to samo polecenie, a trening wznawia pełny stan Lightning z poprzedniego `last.ckpt`.

Stan planu:

```bash
./train.sh --status
```

Windows:

```powershell
.\train.ps1 -Status
```

Szczegółowa procedura znajduje się w `docs/STAGED_TRAINING.md`.

### 6. Eksport ONNX

Po zakończeniu treningu wybierz punkt kontrolny i wyeksportuj model:

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

## Zbiór danych i model

Opis zbioru danych znajduje się w `dataset/DATASET_CARD.md`. Informacje o finalnym modelu i wymagane dane dotyczące treningu znajdują się w `models/pl_PL-mateusz-medium/MODEL_CARD.md`.

Pola oznaczone jako `TODO` muszą zostać uzupełnione na podstawie faktycznego zbioru danych i zakończonego eksperymentu. Nie należy wpisywać wartości szacunkowych jako wyników pomiaru.

## Walidacja jakości

Docelowa ewaluacja obejmuje trzy grupy miar:

- zrozumiałość: WER i CER,
- jakość i podobieństwo głosu: odsłuch ekspercki lub MOS oraz podobieństwo głosu,
- wydajność: RTF, opóźnienie uzyskania pierwszego fragmentu dźwięku, użycie RAM/CPU i rozmiar modelu.

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

Licencja kodu nie określa automatycznie licencji zbioru danych ani wytrenowanego modelu. Warunki dla tych artefaktów muszą być opisane osobno w `dataset/DATASET_CARD.md` i `models/pl_PL-mateusz-medium/MODEL_CARD.md` przed ich publiczną dystrybucją.

## Projekty źródłowe i zależne

- Piper: https://github.com/OHF-Voice/piper1-gpl
- eSpeak NG: https://github.com/espeak-ng/espeak-ng
- głosy Piper: https://huggingface.co/rhasspy/piper-voices

## Autor projektu głosu

Mateusz Pomianek
