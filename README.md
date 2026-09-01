# piper-mat

`piper-mat` rozwija Piper w kierunku powtarzalnego procesu przygotowania, trenowania, oceny, publikacji i wdrożenia własnego polskiego modelu głosu **`pl_PL-mateusz-medium`**.

Repozytorium zawiera bazowy kod Piper oraz warstwę projektu głosu: konfiguracje eksperymentów, narzędzia walidacji danych, trenowanie etapowe, ocenę jakości, karty artefaktów i proces wydawania modelu.

## Stan projektu

Projekt jest w fazie rozwoju. Infrastruktura procesu jest w dużej części przygotowana, natomiast stabilne wydanie modelu wymaga zakończenia właściwego trenowania i wykonania pełnej oceny na rzeczywistych danych.

Aktualne zadania i kryteria ukończenia są utrzymywane wyłącznie w [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Model docelowy

```text
pl_PL-mateusz-medium
```

Finalny głos Piper składa się co najmniej z pary:

```text
pl_PL-mateusz-medium.onnx
pl_PL-mateusz-medium.onnx.json
```

Model i konfiguracja muszą pochodzić z tego samego eksperymentu i być wersjonowane razem.

## Główna ścieżka pracy

```text
zbiór danych
  ↓
walidacja
  ↓
podział treningowy, walidacyjny i testowy
  ↓
trenowanie
  ↓
wybór punktu kontrolnego
  ↓
eksport ONNX
  ↓
ocena jakości i wydajności
  ↓
wydanie
  ↓
wdrożenie
```

Nie należy pomijać etapów walidacji i oceny tylko dlatego, że model poprawnie generuje dźwięk.

## Szybki start

### Windows 11

Najprostsza ścieżka prowadzi przez kreator:

```text
START_PIPER_MAT_GUI.bat
```

Szczegółowa instrukcja znajduje się w [`docs/WINDOWS_GUI.md`](docs/WINDOWS_GUI.md).

### Linux

Podstawowe przygotowanie repozytorium:

```bash
git clone https://github.com/MatPomGit/piper-mat.git
cd piper-mat
git lfs pull
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[train]'
```

Dalsza procedura zależy od tego, czy przygotowywany jest zbiór danych, środowisko trenowania czy kolejne wznowienie eksperymentu. Kanoniczne instrukcje znajdują się w dokumentacji, dlatego README nie powiela pełnych procedur.

## Dokumentacja

Najważniejsze rozdziały:

- [`docs/index.md`](docs/index.md) - punkt wejścia do dokumentacji,
- [`docs/DATASET.md`](docs/DATASET.md) - przygotowanie i walidacja zbioru danych,
- [`docs/TRAINING.md`](docs/TRAINING.md) - podstawy trenowania,
- [`docs/STAGED_TRAINING.md`](docs/STAGED_TRAINING.md) - trenowanie etapowe i wznowienia,
- [`docs/CHECKPOINTS.md`](docs/CHECKPOINTS.md) - zarządzanie punktami kontrolnymi,
- [`docs/EVALUATION.md`](docs/EVALUATION.md) - ocena jakości,
- [`docs/RELEASES.md`](docs/RELEASES.md) - przygotowanie wydania,
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) - wdrożenie modelu,
- [`docs/ALIGNMENTS.md`](docs/ALIGNMENTS.md) - dopasowania fonemów i integracja synchronizacji ust,
- [`docs/TERMINOLOGIA.md`](docs/TERMINOLOGIA.md) - terminologia projektu.

Dokumentację MkDocs można sprawdzić poleceniem:

```bash
mkdocs build --strict
```

## Struktura repozytorium

```text
piper-mat/
├── .github/workflows/   kontrole ciągłej integracji
├── checkpoints/         kontrolowane punkty kontrolne
├── configs/             konfiguracje eksperymentów
├── dataset/             dane i karta zbioru danych
├── docs/                dokumentacja
├── models/              karty modeli
├── samples/             próbki referencyjne i syntetyczne
├── scripts/             narzędzia procesu projektu głosu
├── src/piper/           kod Piper
├── tests/               testy i korpus regresyjny
├── train.ps1            trenowanie etapowe w Windows
└── train.sh             trenowanie etapowe w systemach uniksowych
```

Duże punkty kontrolne i finalne modele ONNX powinny być przechowywane przez mechanizm przeznaczony dla dużych artefaktów albo publikowane jako wydania, zamiast trafiać bezpośrednio do zwykłej historii Git.

## Karty artefaktów

Opis zbioru danych znajduje się w [`dataset/DATASET_CARD.md`](dataset/DATASET_CARD.md), a opis finalnego modelu w [`models/pl_PL-mateusz-medium/MODEL_CARD.md`](models/pl_PL-mateusz-medium/MODEL_CARD.md).

Pola `TODO` w kartach oznaczają brak danych, które muszą zostać uzyskane z rzeczywistego eksperymentu. Nie należy zastępować ich wartościami szacunkowymi przedstawianymi jako pomiary.

## Integracja z awatarem

Projekt przewiduje wykorzystanie informacji fonemicznych do synchronizacji mowy z animacją twarzy:

```text
tekst → Piper TTS → dźwięk i czas fonemów → wizemy → koartykulacja → animacja twarzy
```

Rozwój tej warstwy jest prowadzony po ustabilizowaniu podstawowego modelu głosu i jest opisany w planie rozwoju.

## Standardy projektu

Dokumentacja użytkowa jest prowadzona po polsku. Przy pierwszym użyciu specjalistycznego pojęcia stosowana jest polska nazwa wraz z angielskim odpowiednikiem w nawiasie. Kanoniczne odpowiedniki znajdują się w [`docs/TERMINOLOGIA.md`](docs/TERMINOLOGIA.md).

Kod Pythona rozwijany w projekcie powinien przestrzegać PEP 8 i PEP 257. Szczegółowe zasady zmian znajdują się w [`AGENTS.md`](AGENTS.md).

## Pochodzenie i licencja

Kod Piper zachowany w repozytorium pochodzi z projektu `OHF-Voice/piper1-gpl` i jest objęty licencją GPL-3.0-or-later. Pełny tekst licencji znajduje się w `COPYING`.

Licencja kodu nie określa automatycznie licencji zbioru danych ani wytrenowanego modelu. Warunki tych artefaktów muszą być określone osobno przed ich publiczną dystrybucją.

## Autor projektu głosu

Mateusz Pomianek
