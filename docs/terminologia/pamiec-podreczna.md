# Pamięć podręczna

## Definicja

Pamięć podręczna (cache) przechowuje wyniki kosztownych operacji, aby nie obliczać ich ponownie.

## Znaczenie w `piper-mat`

W `piper-mat` katalog `cache/` może zawierać przygotowane reprezentacje danych. Przy kolejnym uruchomieniu skraca to przygotowanie trenowania, ale wymaga miejsca na dysku.

## Co zmienia w praktyce

Po zmianie transkrypcji, fonemizatora albo sposobu przygotowania audio stara zawartość może być nieaktualna. Rozmiar może rosnąć od megabajtów do wielu gigabajtów zależnie od zbioru. Usunięcie pamięci podręcznej nie usuwa danych źródłowych, tylko wymusza ponowne obliczenia.

## Przykład z repozytorium

Opcja `--data.cache_dir cache` wskazuje katalog używany przez proces trenowania.

## Typowe błędy interpretacyjne

Nie jest kopią zapasową ani pamięcią RAM. Nie należy bez sprawdzenia przenosić jej między niezgodnymi konfiguracjami.

## Powiązane artykuły i procedury

[Zbiór danych](zbior-danych.md), [trenowanie](../TRAINING.md#kanoniczne-uruchamianie).
