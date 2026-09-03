# Podstawowy test poprawności

## Definicja

Podstawowy test poprawności (smoke test) jest krótką kontrolą, czy najważniejsza funkcja w ogóle działa i nie kończy się oczywistym błędem.

## Znaczenie w `piper-mat`

Po eksporcie sprawdza, czy para ONNX i JSON daje się wczytać oraz tworzy niepusty WAV o oczekiwanej częstotliwości. Szybko odrzuca uszkodzony artefakt przed kosztowną oceną.

## Co zmienia w praktyce

Test zwykle trwa sekundy lub minuty i używa jednego albo kilku krótkich zdań. Sprawdza wynik zero-jedynkowo, lecz może dodatkowo kontrolować długość większą od 0, nagłówek WAV i 22 050 Hz.

## Przykład z repozytorium

`python scripts/smoke_test_voice.py --model output/pl_PL-mateusz-medium.onnx` uruchamia test modelu.

## Typowe błędy interpretacyjne

Przejście testu nie dowodzi dobrej wymowy ani naturalności. Nie jest pełnym zestawem regresyjnym.

## Powiązane artykuły i procedury

[ONNX](onnx.md), [ocena](ocena.md), [wdrożenie](../DEPLOYMENT.md#weryfikacja-przed-wdrozeniem).
