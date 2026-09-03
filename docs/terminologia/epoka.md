# Epoka

## Definicja

Epoka (epoch) jest jednym pełnym przejściem przez zbiór treningowy.

## Znaczenie w `piper-mat`

Liczba epok opisuje, ile razy model miał możliwość zobaczyć cały zbiór. W treningu etapowym plan podaje dodatkowe epoki wykonywane w każdej sesji.

## Co zmienia w praktyce

Plan `[250, 250, 250, 250]` oznacza cztery sesje po 250 epok, czyli łącznie 1000 dodatkowych epok. Przy 1600 przykładach i partii 16 jedna epoka ma około 100 partii, jeśli każdy przykład jest użyty raz.

## Przykład z repozytorium

Wartość `epochs_per_session` znajduje się w `configs/pl_PL-mateusz-medium.json`.

## Typowe błędy interpretacyjne

Epoka nie jest pojedynczym krokiem ani gwarancją poprawy. Numer epoki wznowionego modelu nie musi zaczynać się od zera.

## Powiązane artykuły i procedury

[Partia](partia.md), [trenowanie](trenowanie.md), [trenowanie etapowe](../STAGED_TRAINING.md#plan-sesji).
