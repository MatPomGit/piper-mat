# Przesterowanie

## Definicja

Przesterowanie (clipping) występuje, gdy amplituda sygnału przekracza zakres możliwy do zapisania i jej szczyty zostają ucięte.

## Znaczenie w `piper-mat`

Przesterowane nagrania uczą model zniekształconego brzmienia i mogą pogarszać syntezę. Walidacja danych powinna wskazać pliki wymagające ponownego nagrania lub ostrożnej korekty.

## Co zmienia w praktyce

Dla próbek zmiennoprzecinkowych typowy zakres to od `-1.0` do `1.0`; dla PCM 16-bit od `-32768` do `32767`. Szczyt równy granicy nie zawsze dowodzi przesterowania, ale wiele kolejnych próbek na granicy jest sygnałem ostrzegawczym.

## Przykład z repozytorium

Pliki w `dataset/wavs/` sprawdza polecenie `python scripts/validate_dataset.py --metadata dataset/metadata.csv --audio-dir dataset/wavs`.

## Typowe błędy interpretacyjne

Nie jest tym samym co głośne nagranie. Samo ściszenie już uciętego pliku nie odtwarza utraconego kształtu fali.

## Powiązane artykuły i procedury

[Próbka](probka.md), [zbiór danych](zbior-danych.md), [procedura danych](../DATASET.md).
