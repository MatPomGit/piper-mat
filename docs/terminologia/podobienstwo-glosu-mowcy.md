# Podobieństwo głosu mówcy

## Definicja

Podobieństwo głosu mówcy (speaker similarity) określa, na ile głos syntetyczny przypomina głos referencyjnej osoby według słuchaczy lub wybranej metody obliczeniowej.

## Znaczenie w `piper-mat`

Jest jednym z celów modelu `pl_PL-mateusz-medium`, ale nie zastępuje zrozumiałości i naturalności. Model może brzmieć podobnie, a mimo to popełniać błędy wymowy.

## Co zmienia w praktyce

Dla podobieństwa cosinusowego wartości są zwykle od `-1` do `1`; bliżej `1` oznacza większą zgodność wektorów. Praktyczne progi, na przykład `0,7` lub `0,8`, zależą od modelu pomocniczego i korpusu, więc nie są uniwersalne.

## Przykład z repozytorium

Wynik należy raportować z wersją modelu reprezentacji i nagraniami referencyjnymi zgodnie z `docs/EVALUATION.md`.

## Typowe błędy interpretacyjne

Nie jest prawdopodobieństwem, nawet jeśli ma wartość od 0 do 1. Nie mierzy samodzielnie naturalności ani poprawności tekstu.

## Powiązane artykuły i procedury

[Reprezentacja mówcy](reprezentacja-wektorowa-mowcy.md), [MOS i CMOS](mos-i-cmos.md), [ocena](../EVALUATION.md).
