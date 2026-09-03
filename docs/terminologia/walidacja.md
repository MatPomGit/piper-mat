# Walidacja

## Definicja

Walidacja (validation) oznacza sprawdzanie poprawności artefaktu albo ocenę modelu na wydzielonym zbiorze w trakcie trenowania. Kontekst rozstrzyga znaczenie.

## Znaczenie w `piper-mat`

Walidacja danych wykrywa niespójne metadane i WAV. Walidacja modelu dostarcza metryk do wyboru punktu kontrolnego bez korzystania ze zbioru testowego.

## Co zmienia w praktyce

Kontrola może być zero-jedynkowa, na przykład obecność pliku, albo liczbowa, na przykład `val_mel`. Wykonuje się ją przed treningiem, po sesjach i przed wydaniem.

## Przykład z repozytorium

`python scripts/validate_dataset.py --metadata dataset/metadata.csv --audio-dir dataset/wavs` waliduje zbiór.

## Typowe błędy interpretacyjne

Nie każda walidacja jest oceną końcową. Poprawny format nie oznacza dobrej jakości treści.

## Powiązane artykuły i procedury

[Ocena](ocena.md), [zbiory danych](zbiory-treningowy-walidacyjny-testowy.md), [procedura danych](../DATASET.md).
