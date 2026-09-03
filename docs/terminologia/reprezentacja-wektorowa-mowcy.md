# Reprezentacja wektorowa mówcy

## Definicja

Reprezentacja wektorowa mówcy (speaker embedding) jest listą liczb opisującą cechy głosu przydatne do porównywania mówców.

## Znaczenie w `piper-mat`

W ocenie `piper-mat` stały model pomocniczy tworzy wektory dla nagrań rzeczywistych i syntetycznych. Ich porównanie pomaga sprawdzić podobieństwo głosu.

## Co zmienia w praktyce

Wektor może mieć na przykład 192, 256 albo 512 wymiarów, zależnie od modelu pomocniczego. Konkretna liczba nie oznacza jakości. Wektory często porównuje się podobieństwem cosinusowym od `-1` do `1`.

## Przykład z repozytorium

Procedura użycia reprezentacji znajduje się w sekcji `docs/EVALUATION.md#podobienstwo-glosu`.

## Typowe błędy interpretacyjne

Nie jest identyfikatorem mówcy ani próbką audio. Wyników z różnych modeli tworzących wektory nie należy porównywać bez kalibracji.

## Powiązane artykuły i procedury

[Podobieństwo głosu](podobienstwo-glosu-mowcy.md), [ocena](ocena.md), [procedura oceny](../EVALUATION.md#podobienstwo-glosu).
