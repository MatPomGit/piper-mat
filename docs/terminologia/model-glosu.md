# Model głosu

## Definicja

Model głosu (voice model) jest modelem syntezy mowy oraz zestawem informacji potrzebnych do odtworzenia określonego głosu.

## Znaczenie w `piper-mat`

W `piper-mat` docelowym modelem jest `pl_PL-mateusz-medium`. Do użycia wymaga zgodnej pary modelu ONNX i konfiguracji JSON, a jego pochodzenie i wyniki opisuje karta modelu.

## Użycie w procesie

Model powstaje przez dostrajanie, jest wybierany na podstawie oceny, eksportowany do ONNX, testowany i publikowany jako wersjonowane wydanie. Wdrożenie powinno zachowywać parę artefaktów.

## Parametry, jednostki i formaty

Identyfikator zawiera język, nazwę głosu i wariant. Plik `.onnx` zawiera graf i parametry, `.onnx.json` konfigurację, między innymi częstotliwość próbkowania i mapowanie fonemów.

## Praktyczne wartości i ich skutki

| Artefakt lub wartość | Rola |
| --- | --- |
| `pl_PL-mateusz-medium.onnx` | Graf i parametry używane do syntezy. |
| `pl_PL-mateusz-medium.onnx.json` | Konfiguracja, między innymi 22 050 Hz i mapowanie fonemów. |
| `pl_PL-mateusz-medium` | Identyfikator języka, głosu i wariantu; nie jest ścieżką pliku. |

Model o rozmiarze 60 MB i model o rozmiarze 100 MB mogą mieć różne wymagania, ale sam rozmiar nie przesądza o naturalności. Należy porównać je na tym samym korpusie i sprzęcie.

## Przykład z repozytorium

```text
output/pl_PL-mateusz-medium.onnx
output/pl_PL-mateusz-medium.onnx.json
```

## Typowe błędy interpretacyjne

- Utożsamianie samego pliku `.onnx` z kompletnym głosem.
- Interpretowanie etykiety `medium` jako uniwersalnego wyniku jakości.
- Zakładanie, że licencja kodu automatycznie obejmuje dane i model.

## Powiązane artykuły i procedury

- [ONNX](onnx.md)
- [Dostrajanie](dostrajanie.md)
- [Opis modelu](../MODEL.md)
- [Głosy Piper](../VOICES.md)
