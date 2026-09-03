# Zbiór danych

## Definicja

Zbiór danych (dataset) jest uporządkowanym zestawem nagrań, transkrypcji i metadanych używanych do trenowania i oceny.

## Znaczenie w `piper-mat`

W `piper-mat` stanowi źródło wymowy, barwy i warunków akustycznych poznawanych przez model `pl_PL-mateusz-medium`. Jego wersja musi być identyfikowalna, aby wyniki dało się odtworzyć.

## Użycie w procesie

Najpierw sprawdza się zgodność `metadata.csv` z plikami WAV, następnie tworzy zamrożony podział. Karta `dataset/DATASET_CARD.md` dokumentuje pochodzenie, licencję i statystyki.

## Parametry, jednostki i formaty

Wiersz metadanych łączy nazwę WAV i transkrypcję separatorem `|`. Istotne są liczba wypowiedzi, czas w sekundach lub godzinach, format WAV, częstotliwość próbkowania oraz SHA-256 metadanych.

## Praktyczne wartości i ich skutki

| Przykładowa cecha | Znaczenie praktyczne |
| --- | --- |
| 1 000 wypowiedzi po średnio 5 s | Około 83 minuty nagrań przed odrzuceniem błędnych pozycji. |
| WAV, mono, 22 050 Hz | Format zgodny z bieżącą konfiguracją modelu, jeśli potwierdzi go walidator. |
| 10 błędnych transkrypcji na 1 000 | 1% przykładów uczy model niezgodnego powiązania tekstu z mową. |

Liczba plików nie zastępuje czasu nagrań: 1 000 bardzo krótkich wypowiedzi może zawierać mniej materiału niż 300 długich.

## Przykład z repozytorium

```bash
python scripts/validate_dataset.py \
  --metadata dataset/metadata.csv \
  --audio-dir dataset/wavs
```

## Typowe błędy interpretacyjne

- Nazywanie zbiorem danych samych plików audio bez transkrypcji i metadanych.
- Poprawianie transkrypcji tak, że przestaje odpowiadać nagraniu.
- Porównywanie eksperymentów opartych na niezidentyfikowanych wersjach danych.

## Powiązane artykuły i procedury

- [Podział zbioru danych](podzial-zbioru-danych.md)
- [Częstotliwość próbkowania](czestotliwosc-probkowania.md)
- [Procedura danych](../DATASET.md)
- [Karta zbioru](../../dataset/DATASET_CARD.md)
