# piper-mat

`piper-mat` jest forkiem Piper ukierunkowanym na przygotowanie, trening, walidację i publikację polskiego głosu `pl_PL-mateusz-medium`.

Repozytorium obejmuje kod Pipera, konfigurację eksperymentu, metadane datasetu, walidację jakości danych, narzędzia ewaluacyjne oraz dokumentację procesu wydawania modelu.

## Główne obszary

- `dataset/` — metadane i karta datasetu,
- `configs/` — wersjonowana konfiguracja treningu,
- `models/` — karta finalnego modelu,
- `scripts/` — walidacja, splity, ewaluacja i testy jakości,
- `tests/` — zamrożony korpus regresyjny języka polskiego,
- `docs/` — dokumentacja procesu badawczego i wdrożeniowego.

## Aktualny cel

Najbliższym celem jest uzyskanie powtarzalnego pipeline'u:

`validate -> split -> train -> export -> smoke test -> evaluate -> package`.

Aktualny stan i pozostałe zadania są opisane w [roadmapie](ROADMAP.md).

## Licencja

Kod pochodzący z Piper jest udostępniany zgodnie z GPL-3.0-or-later. Licencje datasetu oraz finalnego modelu głosu należy traktować oddzielnie i wskazać w odpowiednich kartach artefaktów.
