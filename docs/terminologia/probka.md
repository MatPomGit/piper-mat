# Próbka

## Definicja

Próbka (sample) może oznaczać pojedynczą wartość sygnału audio albo jeden przykład zbioru danych. Kontekst musi wskazywać właściwe znaczenie.

## Znaczenie w `piper-mat`

W audio kolejne próbki tworzą przebieg fali. W danych treningowych próbką bywa cały rekord: nagranie wraz z transkrypcją.

## Co zmienia w praktyce

Przy 22 050 Hz jedna sekunda kanału zawiera 22 050 próbek sygnału, a 0,1 s zawiera 2205. Zbiór 1000 próbek danych oznacza natomiast 1000 wypowiedzi, niezależnie od ich długości.

## Przykład z repozytorium

W `docs/ALIGNMENTS.md` liczba próbek sygnału jest przeliczana na sekundy przez podzielenie przez częstotliwość próbkowania.

## Typowe błędy interpretacyjne

Nie wolno bez doprecyzowania mieszać próbki sygnału z przykładem danych. Próbka audio nie oznacza automatycznie pliku WAV.

## Powiązane artykuły i procedury

[Częstotliwość próbkowania](czestotliwosc-probkowania.md), [zbiór danych](zbior-danych.md), [dopasowania](../ALIGNMENTS.md).
