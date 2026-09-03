# Mechanizm wczytywania danych

## Definicja

Mechanizm wczytywania danych (data loader) pobiera przykłady ze zbioru, przygotowuje je i układa w partie dla modelu.

## Znaczenie w `piper-mat`

Oddziela odczyt WAV i metadanych od obliczeń modelu. Sprawne wczytywanie zapobiega sytuacji, w której GPU czeka na dane.

## Co zmienia w praktyce

Wpływ mają rozmiar partii, liczba procesów roboczych, kolejność losowania i długość nagrań. `0` procesów oznacza zwykle pracę w procesie głównym, a `2`, `4` lub `8` może przyspieszyć odczyt kosztem RAM. Konkretne opcje należy sprawdzić w bieżącym CLI.

## Przykład z repozytorium

`python -m piper.train fit --help` pokazuje parametry warstwy danych obsługiwane przez używaną wersję.

## Typowe błędy interpretacyjne

Nie jest bazą danych ani samym katalogiem WAV. Więcej procesów nie zawsze oznacza szybszą pracę.

## Powiązane artykuły i procedury

[Partia](partia.md), [zbiór danych](zbior-danych.md), [trenowanie](trenowanie.md).
