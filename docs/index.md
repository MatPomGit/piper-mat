# piper-mat

`piper-mat` jest gałęzią rozwojową Piper ukierunkowaną na przygotowanie, trenowanie (training), walidację i publikację polskiego głosu `pl_PL-mateusz-medium`.

Repozytorium obejmuje kod Pipera, konfigurację eksperymentu, metadane zbioru danych (dataset), walidację jakości danych, narzędzia do oceny (evaluation) oraz dokumentację procesu wydawania modelu.

Dokumentacja projektu jest prowadzona po polsku. Przy pierwszym użyciu charakterystycznego terminu technicznego podawana jest jego polska nazwa oraz angielski odpowiednik w nawiasie. Obowiązujące tłumaczenia i zasady redakcyjne znajdują się w [słowniku terminologii](TERMINOLOGIA.md).

## Główne obszary

- `dataset/` — metadane i karta zbioru danych,
- `configs/` — wersjonowana konfiguracja trenowania,
- `models/` — karta finalnego modelu,
- `scripts/` — walidacja, podziały danych, ocena i testy jakości,
- `tests/` — zamrożony korpus regresyjny języka polskiego,
- `docs/` — dokumentacja procesu badawczego i wdrożeniowego.

## Aktualny cel

Najbliższym celem jest uzyskanie powtarzalnego procesu:

`walidacja → podział danych → trenowanie → eksport → podstawowy test poprawności → ocena → pakowanie`.

Aktualny stan i pozostałe zadania są opisane w [planie rozwoju](ROADMAP.md).

## Zasada terminologiczna

Nazwy techniczne wymagane przez kod, np. `batch_size`, `--checkpoint`, `ONNX`, `PyTorch` lub `CUDA`, pozostają bez zmian. Ich znaczenie jest jednak opisywane po polsku, np. „parametr `batch_size` określa rozmiar partii (batch size)”.

## Licencja

Kod pochodzący z Piper jest udostępniany zgodnie z GPL-3.0-or-later. Licencje zbioru danych oraz finalnego modelu głosu należy traktować oddzielnie i wskazać w odpowiednich kartach artefaktów.
