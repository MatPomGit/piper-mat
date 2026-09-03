# Współczynnik uczenia

## Definicja

Współczynnik uczenia (learning rate) skaluje wielkość zmian parametrów modelu wykonywanych przez optymalizator.

## Znaczenie w `piper-mat`

Za duża wartość może powodować niestabilność, a za mała bardzo wolny postęp. Przy dostrajaniu często stosuje się mniejszą wartość niż przy trenowaniu od początku, aby nie zniszczyć użytecznych parametrów bazowych.

## Co zmienia w praktyce

Typowe rzędy wielkości do eksperymentów to `0.001`, `0.0001` i `0.00001`, ale właściwa wartość zależy od optymalizatora i konfiguracji. Harmonogram może ją stopniowo zmniejszać. Nie są to uniwersalne ustawienia projektu.

## Przykład z repozytorium

Przebieg wartości `learning_rate` może znaleźć się w raportach `output/training_reports/session_01/`.

## Typowe błędy interpretacyjne

Nie jest prędkością wykonywania programu. Dziesięciokrotnie większa wartość nie oznacza dziesięciokrotnie szybszego uczenia.

## Powiązane artykuły i procedury

[Funkcja straty](funkcja-straty.md), [dostrajanie](dostrajanie.md), [raporty sesji](../STAGED_TRAINING.md#raport-po-kazdej-sesji).
