# ONNX

## Definicja

ONNX (Open Neural Network Exchange) jest otwartym formatem reprezentacji grafów modeli uczenia maszynowego.

## Znaczenie w `piper-mat`

W `piper-mat` jest formatem wykonawczym finalnego modelu głosu. Eksport oddziela artefakt używany we wdrożeniu od treningowego punktu kontrolnego PyTorch Lightning.

## Użycie w procesie

Wybrany `.ckpt` eksportuje się do `.onnx`, a potem testuje razem z konfiguracją `.onnx.json`. ONNX Runtime wykonuje model, natomiast pakiet `onnx` może modyfikować jego graf, na przykład dodając wyjścia dopasowań.

## Parametry, jednostki i formaty

Model ma rozszerzenie `.onnx`, konfiguracja `.onnx.json`. Ważne są wersja artefaktu, rozmiar w bajtach, SHA-256, nazwy wejść i wyjść oraz zgodność z używanym środowiskiem wykonawczym.

## Praktyczne wartości i ich skutki

| Przykład | Znaczenie praktyczne |
| --- | --- |
| Plik `.ckpt` | Stan treningowy, który może zawierać optymalizator; nie jest finalnym modelem dla Pipera. |
| Plik `.onnx` | Model wykonawczy przekazywany do ONNX Runtime. |
| Plik `.onnx.json` | Konfiguracja wymagana obok modelu przez Pipera. |

Jeśli eksport utworzył model 80 MB, a skopiowany plik ma 0 bajtów albo kilka kilobajtów, wdrożenie należy zatrzymać i zweryfikować SHA-256. Liczby są przykładem kontroli, nie oczekiwanym rozmiarem każdego modelu.

## Przykład z repozytorium

```bash
python -m piper.train.export_onnx \
  --checkpoint checkpoints/candidate.ckpt \
  --output-file output/pl_PL-mateusz-medium.onnx
```

## Typowe błędy interpretacyjne

- Używanie nazw ONNX i ONNX Runtime zamiennie.
- Eksport ostatniego punktu bez wcześniejszego wyboru na podstawie oceny.
- Rozdzielanie modelu i konfiguracji pochodzących z tego samego wydania.

## Powiązane artykuły i procedury

- [Model głosu](model-glosu.md)
- [Wnioskowanie](wnioskowanie.md)
- [Trenowanie](../TRAINING.md#eksport-onnx)
- [Wdrożenie](../DEPLOYMENT.md)
