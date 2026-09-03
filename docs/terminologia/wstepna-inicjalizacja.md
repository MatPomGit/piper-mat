# Wstępna inicjalizacja

## Definicja

Wstępna inicjalizacja (warm start), dokładniej inicjalizacja z parametrów modelu bazowego (model warm start), rozpoczyna nowy eksperyment od wcześniej wyuczonych parametrów.

## Znaczenie w `piper-mat`

Pozwala szybciej uzyskać użyteczny model niż rozpoczęcie trenowania od losowych parametrów. W `piper-mat` bazą jest zweryfikowany punkt kontrolny, ale nowy eksperyment ma własne dane i cel.

## Co zmienia w praktyce

Należy sprawdzić architekturę, częstotliwość próbkowania i mapowanie wejścia. W praktyce plik może mieć około 846 MB, jak opisany `base.ckpt`, i musi zgadzać się z SHA-256 w manifeście.

## Przykład z repozytorium

`python scripts/download_checkpoint.py base.ckpt` pobiera aktywny model bazowy.

## Typowe błędy interpretacyjne

Nie jest wznowieniem przerwanej sesji, bo nie musi odtwarzać optymalizatora i liczników. Nie oznacza też rozgrzewania sprzętu.

## Powiązane artykuły i procedury

[Dostrajanie](dostrajanie.md), [wznowienie trenowania](wznowienie-trenowania.md), [punkty kontrolne](../CHECKPOINTS.md).
