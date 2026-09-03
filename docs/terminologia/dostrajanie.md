# Dostrajanie

## Definicja

Dostrajanie (fine-tuning) jest trenowaniem modelu rozpoczynanym od wcześniej wyuczonych parametrów modelu bazowego.

## Znaczenie w `piper-mat`

W `piper-mat` pozwala wykorzystać reprezentacje mowy z modelu `en_US-lessac-medium` jako punkt startowy modelu polskiego głosu, zamiast inicjalizować parametry losowo.

## Użycie w procesie

Najpierw weryfikuje się zgodność i sumę bazowego punktu kontrolnego. Następnie uruchamia nowy eksperyment z danymi projektu. Dalsze sesje tego samego przebiegu są już wznowieniem trenowania.

## Parametry, jednostki i formaty

Kluczowe są architektura, konfiguracja modelu, częstotliwość próbkowania, mapowanie wejścia oraz ścieżka `ckpt_path`. Artefakt bazowy ma format `.ckpt` i identyfikator SHA-256.

## Praktyczne wartości i ich skutki

| Sytuacja | Praktyczna decyzja |
| --- | --- |
| Zgodna architektura i 22 050 Hz | Punkt bazowy może być kandydatem do dostrajania po sprawdzeniu manifestu. |
| Inna liczba mówców lub mapowanie fonemów | Potrzebna jest dodatkowa kontrola zgodności, samo rozszerzenie `.ckpt` nie wystarcza. |
| Zmiana danych lub celu eksperymentu | Należy rozpocząć opisany nowy przebieg zamiast przedstawiać go jako zwykłe wznowienie. |

Mniejszy współczynnik uczenia, na przykład `0.0001` zamiast `0.001`, zwykle wprowadza ostrożniejsze zmiany parametrów, ale jego właściwą wartość trzeba potwierdzić eksperymentalnie.

## Przykład z repozytorium

```bash
python scripts/download_checkpoint.py base.ckpt
python scripts/verify_checkpoint.py checkpoints/base.ckpt
```

## Typowe błędy interpretacyjne

- Zakładanie, że model bazowy musi mówić głosem tej samej osoby.
- Użycie technicznie niezgodnego punktu tylko dlatego, że ma właściwe rozszerzenie.
- Nazywanie każdej kontynuacji z `.ckpt` dostrajaniem.

## Powiązane artykuły i procedury

- [Punkt kontrolny](punkt-kontrolny.md)
- [Wznowienie trenowania](wznowienie-trenowania.md)
- [Podstawy trenowania](../TRAINING.md)
- [Punkty kontrolne](../CHECKPOINTS.md)
