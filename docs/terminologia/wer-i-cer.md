# WER i CER

## Definicja

Współczynnik błędów słów (Word Error Rate, WER) i współczynnik błędów znaków (Character Error Rate, CER) mierzą różnicę między tekstem referencyjnym a transkrypcją rozpoznaną z syntetycznej mowy.

## Znaczenie w `piper-mat`

W `piper-mat` wspierają automatyczną ocenę zrozumiałości. Nie zastępują odsłuchu, ponieważ zależą również od użytego systemu rozpoznawania mowy i normalizacji tekstu.

## Użycie w procesie

Dla zamrożonego korpusu generuje się próbki, wykonuje automatyczne rozpoznawanie mowy, normalizuje tekst według jednej procedury i oblicza odległość edycyjną na poziomie słów oraz znaków.

## Parametry, jednostki i formaty

WER to `(S + D + I) / N` dla zamian, usunięć i wstawień słów. CER stosuje analogiczne operacje na znakach. Wyniki są ilorazami, często raportowanymi w procentach wraz z liczebnością korpusu.

## Praktyczne wartości i ich skutki

| Wynik | Prosta interpretacja |
| --- | --- |
| WER 0,00, czyli 0% | System rozpoznawania nie wykazał błędów słów w badanym korpusie. |
| WER 0,10, czyli 10% | Na każde 100 słów referencji przypada łącznie około 10 zamian, usunięć i wstawień. |
| CER 0,03, czyli 3% | Na każde 100 znaków przypada około 3 operacji edycyjnych. |

WER może przekroczyć 100%, gdy rozpoznanie zawiera wiele dodatkowych słów. Wynik z 10 zdań jest mniej wiarygodny niż wynik z 1 000 zdań, dlatego zawsze trzeba podać rozmiar korpusu.

## Przykład z repozytorium

```bash
python scripts/evaluate_transcripts.py results/transcripts.jsonl \
  --output evaluations/pl_PL-mateusz-medium.json
```

## Typowe błędy interpretacyjne

- Traktowanie WER i CER jako bezpośrednich miar naturalności lub podobieństwa głosu.
- Porównywanie wyników po różnej normalizacji tekstu.
- Pomijanie wersji systemu rozpoznawania i korpusu testowego.

## Powiązane artykuły i procedury

- [MOS i CMOS](mos-i-cmos.md)
- [Model głosu](model-glosu.md)
- [Procedura oceny](../EVALUATION.md)
- [Podział danych](podzial-zbioru-danych.md)
