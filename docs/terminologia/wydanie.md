# Wydanie

## Definicja

Wydanie (release) jest oznaczoną wersją modelu i towarzyszących mu plików przeznaczoną do przekazania użytkownikom.

## Znaczenie w `piper-mat`

W `piper-mat` zamienia wynik eksperymentu w identyfikowalny zestaw, który można zweryfikować, wdrożyć i w razie potrzeby wycofać.

## Co zmienia w praktyce

Wydanie powinno zawierać zgodne pliki `.onnx` i `.onnx.json`, kartę modelu, manifest, SHA-256 i próbki. Praktyczne oznaczenia to `v1.0.0`, `v1.1.0-rc1` lub data, jeśli projekt przyjmie taką konwencję.

## Przykład z repozytorium

Procedurę kompletowania artefaktów opisuje `docs/RELEASES.md`.

## Typowe błędy interpretacyjne

Nie jest dowolnym plikiem skopiowanym z `output/`. Numer wersji nie zastępuje manifestu ani wyników oceny.

## Powiązane artykuły i procedury

[Model głosu](model-glosu.md), [suma kontrolna](suma-kontrolna.md), [wydawanie](../RELEASES.md).
