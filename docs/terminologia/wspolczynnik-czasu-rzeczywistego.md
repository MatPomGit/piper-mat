# Współczynnik czasu rzeczywistego

## Definicja

Współczynnik czasu rzeczywistego (Real-Time Factor, RTF) jest ilorazem czasu obliczeń i czasu wygenerowanego dźwięku.

## Znaczenie w `piper-mat`

W `piper-mat` służy do porównywania wydajności wnioskowania modeli i środowisk wykonawczych. Wynik ma sens tylko razem z opisem sprzętu, oprogramowania, tekstu i sposobu pomiaru.

## Użycie w procesie

Mierzy się czas syntezy oraz długość wynikowego dźwięku, a następnie oblicza `RTF = czas obliczeń / czas dźwięku`. Wartość poniżej 1 oznacza syntezę szybszą od odtwarzania w czasie rzeczywistym.

## Parametry, jednostki i formaty

RTF jest wielkością bezwymiarową. Oba czasy muszą mieć tę samą jednostkę, zwykle sekundy. Raport powinien też podawać liczbę prób, medianę lub inną agregację i warunki rozgrzania.

## Praktyczne wartości i ich skutki

| Czas obliczeń | Długość dźwięku | RTF | Interpretacja |
| ---: | ---: | ---: | --- |
| 1 s | 10 s | 0,1 | Synteza jest około 10 razy szybsza od czasu rzeczywistego. |
| 5 s | 10 s | 0,5 | Synteza jest około 2 razy szybsza od czasu rzeczywistego. |
| 12 s | 10 s | 1,2 | Obliczenie trwa dłużej niż odtworzenie wyniku. |

RTF `0,5` nie oznacza opóźnienia 0,5 s. Dla dźwięku długości 2 s odpowiada około 1 s obliczeń, a dla 20 s około 10 s.

## Przykład z repozytorium

```text
czas obliczeń = 2 s
czas dźwięku = 10 s
RTF = 2 / 10 = 0,2
```

## Typowe błędy interpretacyjne

- Odczytywanie RTF 0,2 jako 20 sekund.
- Porównywanie wyników z różnego sprzętu bez zaznaczenia tej różnicy.
- Utożsamianie RTF z opóźnieniem do pierwszego fragmentu dźwięku.

## Powiązane artykuły i procedury

- [Wnioskowanie](wnioskowanie.md)
- [ONNX](onnx.md)
- [Ocena](../EVALUATION.md)
- [Wdrożenie](../DEPLOYMENT.md#opoznienie-koncowe)
