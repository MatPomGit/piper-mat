# Funkcja straty

## Definicja

Funkcja straty (loss function) wyraża liczbowo, jak bardzo wynik modelu różni się od celu używanego podczas trenowania.

## Znaczenie w `piper-mat`

Optymalizator zmienia parametry tak, aby zmniejszać wartość funkcji straty. Model mowy może raportować kilka składników, na przykład związanych z mel-spektrogramem, czasem trwania lub generatorem.

## Co zmienia w praktyce

Wartości `2.0`, `1.0` i `0.5` mają znaczenie tylko dla tej samej definicji i konfiguracji. Liczy się przebieg w czasie oraz wynik walidacyjny, nie sama skala. `NaN` wskazuje błąd numeryczny.

## Przykład z repozytorium

Raporty w `output/training_reports/session_01/REPORT.md` zestawiają dostępne metryki zawierające między innymi `loss` i `mel`.

## Typowe błędy interpretacyjne

Niższa strata treningowa nie gwarantuje naturalniejszego głosu. Nie wolno porównywać liczb z różnych funkcji jak tej samej miary.

## Powiązane artykuły i procedury

[Współczynnik uczenia](wspolczynnik-uczenia.md), [trenowanie](trenowanie.md), [ocena](ocena.md).
