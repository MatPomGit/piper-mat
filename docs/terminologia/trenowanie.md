# Trenowanie

## Definicja

Trenowanie (training) jest procesem aktualizowania parametrów modelu na podstawie przykładów i funkcji straty.

## Znaczenie w `piper-mat`

W `piper-mat` proces buduje polski model głosu w kontrolowanych sesjach. Projekt wykorzystuje dostrajanie modelu bazowego i zapisuje konfigurację, metryki oraz punkty kontrolne.

## Użycie w procesie

Po walidacji danych uruchamia się `train.sh`, `train.ps1` albo niskopoziomowe polecenie Pipera. Walidacja w trakcie procesu pomaga oceniać postęp, a po zakończeniu wybiera się punkt do eksportu.

## Parametry, jednostki i formaty

Najważniejsze wielkości to epoka, krok, rozmiar partii `data.batch_size`, współczynnik uczenia, wartości funkcji straty i liczba epok `trainer.max_epochs`. Konfiguracje projektu są w JSON.

## Praktyczne wartości i ich skutki

| Wartość | Co zmienia |
| --- | --- |
| `data.batch_size=8` | Zwykle zużywa mniej pamięci GPU, ale daje więcej kroków na epokę niż wartość `16`. |
| 250 epok w sesji | Model 250 razy przechodzi przez część treningową przed zakończeniem tej sesji. |
| 4 sesje po 250 epok | Daje łącznie 1 000 dodatkowych epok, z czterema miejscami bezpiecznego zatrzymania. |

Dla 1 600 przykładów partia `16` daje w przybliżeniu 100 kroków na epokę, a partia `8` około 200. Rzeczywista liczba może zależeć od sposobu grupowania danych.

## Przykład z repozytorium

```bash
./train.sh --dry-run
./train.sh
```

## Typowe błędy interpretacyjne

- Utożsamianie spadku funkcji straty z gwarancją dobrej jakości odsłuchowej.
- Zmiana wielu parametrów bez utworzenia nowej konfiguracji eksperymentu.
- Nazywanie wnioskowania trenowaniem, mimo że nie aktualizuje parametrów.

## Powiązane artykuły i procedury

- [Dostrajanie](dostrajanie.md)
- [Wznowienie trenowania](wznowienie-trenowania.md)
- [Podstawy trenowania](../TRAINING.md)
- [Trenowanie etapowe](../STAGED_TRAINING.md)
