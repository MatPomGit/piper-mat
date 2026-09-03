# Interfejs wiersza poleceń

## Definicja

Interfejs wiersza poleceń (command-line interface, CLI) pozwala sterować programem za pomocą poleceń tekstowych i opcji.

## Znaczenie w `piper-mat`

W `piper-mat` CLI służy do trenowania, walidacji, eksportu i syntezy. Łatwo zapisać je w skrypcie i powtórzyć bez ręcznego klikania.

## Co zmienia w praktyce

Opcje mają ustaloną pisownię, na przykład `--output-file`, `--checkpoint` i `--data.batch_size`. Kod zakończenia `0` zwykle oznacza sukces, a wartość różna od zera błąd. `--help` pokazuje bieżące argumenty.

## Przykład z repozytorium

`piper --model pl_PL-mateusz-medium.onnx --output-file test.wav -- "Dzień dobry."` zapisuje syntezę do `test.wav`.

## Typowe błędy interpretacyjne

CLI nie jest nazwą konkretnej powłoki. Nie wolno dowolnie zamieniać łączników na podkreślenia w publicznych opcjach.

## Powiązane artykuły i procedury

[Wnioskowanie](wnioskowanie.md), [dokumentacja CLI](../CLI.md), [trenowanie](../TRAINING.md).
