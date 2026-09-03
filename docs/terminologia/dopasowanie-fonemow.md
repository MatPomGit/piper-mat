# Dopasowanie fonemów

## Definicja

Dopasowanie fonemów (phoneme alignment) przypisuje fonemom lub ich identyfikatorom odcinki czasowe wygenerowanego dźwięku.

## Znaczenie w `piper-mat`

W `piper-mat` umożliwia synchronizację głosu z ruchem ust awatara. Stanowi dane czasowe, a nie gotową animację ani ocenę poprawności wymowy.

## Użycie w procesie

Model ONNX można przygotować tak, aby zwracał liczbę próbek przypadającą na identyfikatory fonemów. `phoneme_alignments_to_timings` przelicza te długości na półotwarte przedziały osi czasu.

## Parametry, jednostki i formaty

Podstawową wartością jest `num_samples`. Początek i koniec zapisuje się jako indeks próbki oraz czas w sekundach. Przeliczenie wymaga częstotliwości próbkowania w Hz; format wymiany może być JSON.

## Praktyczne wartości i ich skutki

| Liczba próbek przy 22 050 Hz | Czas odcinka |
| ---: | ---: |
| 220 | około 0,010 s, czyli 10 ms |
| 1 102 lub 1 103 | około 0,050 s, czyli 50 ms |
| 2 205 | 0,100 s, czyli 100 ms |

Jeżeli poprzedni fragment kończy się na próbce 44 100, kolejny powinien rozpocząć oś czasu od 2,0 s. Pominięcie tego przesunięcia przeniosłoby jego fonemy na początek wypowiedzi.

## Przykład z repozytorium

```bash
python -m piper.patch_voice_with_alignment \
  output/pl_PL-mateusz-medium.onnx \
  --output output/pl_PL-mateusz-medium-aligned.onnx
```

## Typowe błędy interpretacyjne

- Utożsamianie dopasowania z fonemizacją lub animacją wizemów.
- Zakładanie relacji jeden znak do jednego fonemu i jednego identyfikatora.
- Pomijanie ciszy między fragmentami przy budowaniu wspólnej osi czasu.

## Powiązane artykuły i procedury

- [Fonemizacja](fonemizacja.md)
- [Częstotliwość próbkowania](czestotliwosc-probkowania.md)
- [Procedura dopasowań](../ALIGNMENTS.md)
- [Wdrożenie](../DEPLOYMENT.md)
