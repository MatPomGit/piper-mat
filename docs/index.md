# piper-mat

`piper-mat` jest gałęzią rozwojową Piper ukierunkowaną na przygotowanie, trening, walidację i publikację polskiego głosu `pl_PL-mateusz-medium`.

Repozytorium obejmuje kod Pipera, konfigurację eksperymentu, metadane zbioru danych, walidację jakości danych, narzędzia ewaluacyjne oraz dokumentację procesu wydawania modelu.

## Główne obszary

- `dataset/` — metadane i karta zbioru danych,
- `configs/` — wersjonowana konfiguracja treningu,
- `models/` — karta finalnego modelu,
- `scripts/` — walidacja, podziały danych, ewaluacja i testy jakości,
- `tests/` — zamrożony korpus regresyjny języka polskiego,
- `docs/` — dokumentacja procesu badawczego i wdrożeniowego.

## Aktualny cel

Najbliższym celem jest uzyskanie powtarzalnego procesu:

`walidacja → podział danych → trening → eksport → test poprawności → ewaluacja → pakowanie`.

Aktualny stan i pozostałe zadania są opisane w [planie rozwoju](ROADMAP.md).

## Licencja

Kod pochodzący z Piper jest udostępniany zgodnie z GPL-3.0-or-later. Licencje zbioru danych oraz finalnego modelu głosu należy traktować oddzielnie i wskazać w odpowiednich kartach artefaktów.
