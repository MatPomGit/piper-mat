# Partia i rozmiar partii

## Definicja

Partia (batch) to grupa przykładów przetwarzanych razem w jednym kroku. Rozmiar partii (batch size) mówi, ile przykładów zawiera ta grupa.

## Znaczenie w `piper-mat`

Podczas trenowania `piper-mat` model oblicza wynik dla całej partii, a następnie aktualizuje parametry. Większa partia zwykle lepiej wykorzystuje GPU, ale zajmuje więcej jego pamięci.

## Co zmienia w praktyce

Wartości `8`, `16` i `32` są praktycznymi punktami startowymi. Zmiana z `16` na `8` zwykle zmniejsza zużycie pamięci, lecz podwaja liczbę partii potrzebnych do przetworzenia tej samej liczby nagrań. Parametr `data.batch_size` pozostaje opisany w procedurze trenowania.

## Przykład z repozytorium

`--data.batch_size 16` w poleceniu z `docs/TRAINING.md` oznacza maksymalnie 16 przykładów w jednej partii.

## Typowe błędy interpretacyjne

Nie oznacza liczby wszystkich nagrań ani liczby epok. Dwukrotnie większa partia nie gwarantuje dwukrotnie szybszego trenowania.

## Powiązane artykuły i procedury

[Trenowanie](trenowanie.md), [procedura trenowania](../TRAINING.md#databatch_size).
