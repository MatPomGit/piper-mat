# Maksymalne użycie pamięci RAM

## Definicja

Maksymalne użycie pamięci RAM (peak RAM usage) jest największą ilością pamięci operacyjnej zajętą w czasie pomiaru.

## Znaczenie w `piper-mat`

Pomaga ustalić, czy synteza zmieści się na urządzeniu docelowym i czy po aktualizacji nie pojawiła się regresja.

## Co zmienia w praktyce

Wynik należy podawać w MB, MiB, GB lub GiB wraz z rozróżnieniem jednostki. `1024 MiB` to `1 GiB`, a `1000 MB` to `1 GB`. Warto zanotować stan spoczynkowy i szczyt dla kilku długich zdań.

## Przykład z repozytorium

Procedura `docs/EVALUATION.md` wymaga raportowania maksymalnego użycia RAM obok RTF i czasu syntezy.

## Typowe błędy interpretacyjne

Nie jest rozmiarem pliku ONNX ani użyciem pamięci GPU. Pojedynczy odczyt może pominąć krótki szczyt.

## Powiązane artykuły i procedury

[Monitorowanie](monitorowanie.md), [RTF](wspolczynnik-czasu-rzeczywistego.md), [ocena](../EVALUATION.md).
