# Metadane

## Definicja

Metadane (metadata) są informacjami opisującymi inne dane, na przykład powiązaniem nazwy nagrania z jego transkrypcją.

## Znaczenie w `piper-mat`

Plik `dataset/metadata.csv` mówi procesowi trenowania, jaki tekst odpowiada każdemu WAV. Jego poprawność jest równie ważna jak poprawność nagrań.

## Co zmienia w praktyce

W projekcie wiersz ma postać `000001.wav|Treść wypowiedzi.` i jest zapisany jako tekst UTF-8. Praktyczne kontrole obejmują brakujące pliki, puste teksty, duplikaty i zgodność liczby rekordów z nagraniami.

## Przykład z repozytorium

`python scripts/validate_dataset.py --metadata dataset/metadata.csv --audio-dir dataset/wavs` sprawdza metadane i audio.

## Typowe błędy interpretacyjne

Metadane nie są wyłącznie właściwościami WAV. Poprawna pisownia zdania nie pomaga, jeśli zdanie nie odpowiada nagraniu.

## Powiązane artykuły i procedury

[Zbiór danych](zbior-danych.md), [podział danych](podzial-zbioru-danych.md), [procedura danych](../DATASET.md).
