# Podział zbioru danych

## Definicja

Podział zbioru danych (data split) przypisuje elementy do rozłącznych części treningowej, walidacyjnej i testowej.

## Znaczenie w `piper-mat`

W `piper-mat` zamrożony plik podziału zapewnia, że kolejne modele są porównywane na tych samych wypowiedziach i nie uczą się na danych przeznaczonych do końcowej oceny.

## Użycie w procesie

Podział tworzy się deterministycznie przed serią eksperymentów. Zbiór treningowy aktualizuje parametry, walidacyjny wspiera wybór modelu, a testowy służy do końcowej oceny.

## Parametry, jednostki i formaty

Artefaktem jest `dataset/splits.json`. Należy zapisać ziarno `--seed`, liczebność części i SHA-256 pliku wejściowego oraz wyniku. Udziały muszą odpowiadać zastosowanej procedurze.

## Praktyczne wartości i ich skutki

| Podział 1 000 wypowiedzi | Liczebność części |
| --- | --- |
| 80/10/10 | 800 treningowych, 100 walidacyjnych i 100 testowych. |
| 90/5/5 | 900 treningowych, 50 walidacyjnych i 50 testowych. |
| 95/2,5/2,5 | 950 treningowych oraz po 25 walidacyjnych i testowych; części oceniające mogą być zbyt małe do stabilnych wniosków. |

Nie są to obowiązkowe proporcje. Ważniejsze jest zachowanie tego samego `splits.json` w porównywanych eksperymentach i niedopuszczenie tego samego nagrania do kilku części.

## Przykład z repozytorium

```bash
python scripts/create_splits.py \
  --metadata dataset/metadata.csv \
  --output dataset/splits.json \
  --seed 20260831
```

## Typowe błędy interpretacyjne

- Losowanie nowego podziału dla każdego porównywanego modelu.
- Strojenie decyzji na podstawie zbioru testowego.
- Założenie, że samo ziarno identyfikuje podział bez wersji danych i skryptu.

## Powiązane artykuły i procedury

- [Zbiór danych](zbior-danych.md)
- [Trenowanie](trenowanie.md)
- [Procedura danych](../DATASET.md)
- [Ocena](../EVALUATION.md)
