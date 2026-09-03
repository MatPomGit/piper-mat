# Ocena

## Definicja

Ocena (evaluation) jest uporządkowanym sprawdzaniem jakości i wydajności modelu na danych niewykorzystywanych do aktualizacji jego parametrów.

## Znaczenie w `piper-mat`

W `piper-mat` łączy odsłuch, WER, CER, MOS, CMOS, podobieństwo głosu, testy techniczne i RTF. Wyniki decydują, czy model nadaje się do wydania.

## Co zmienia w praktyce

Warto porównywać co najmniej dwa modele na tym samym korpusie. WER i CER podaje się jako ułamek lub procent, MOS często w skali 1 do 5, a RTF jako iloraz bez jednostki.

## Przykład z repozytorium

`python scripts/evaluate_transcripts.py results/transcripts.jsonl --output evaluations/pl_PL-mateusz-medium.json` oblicza metryki transkrypcji.

## Typowe błędy interpretacyjne

Ocena nie jest tym samym co walidacja w trakcie trenowania. Jedna metryka nie opisuje wszystkich cech głosu.

## Powiązane artykuły i procedury

[WER i CER](wer-i-cer.md), [MOS i CMOS](mos-i-cmos.md), [procedura oceny](../EVALUATION.md).
