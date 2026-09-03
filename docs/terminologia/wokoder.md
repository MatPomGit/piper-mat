# Wokoder

## Definicja

Wokoder (vocoder) przekształca akustyczną reprezentację mowy na próbki sygnału dźwiękowego.

## Znaczenie w `piper-mat`

W systemach TTS odpowiada za końcowe brzmienie fali. Architektura VITS używana przez Piper łączy generowanie mowy z resztą modelu, więc użytkownik nie uruchamia osobnego polecenia wokodera.

## Co zmienia w praktyce

Na wynik wpływają częstotliwość próbkowania, zakres amplitudy i konfiguracja modelu. Dla projektu wyjście ma 22 050 próbek na sekundę; 5 sekund dźwięku to około 110 250 próbek na kanał.

## Przykład z repozytorium

Eksport z `python -m piper.train.export_onnx` przygotowuje kompletny model wykonawczy używany przez Pipera.

## Typowe błędy interpretacyjne

Wokoder nie jest fonemizatorem: pierwszy tworzy dźwięk, drugi zamienia tekst na fonemy. Nie jest też formatem WAV.

## Powiązane artykuły i procedury

[Fonemizacja](fonemizacja.md), [model głosu](model-glosu.md), [ONNX](onnx.md).
