# Punkt kontrolny

## Definicja

Punkt kontrolny (checkpoint) jest zapisem stanu modelu utworzonym podczas trenowania.

## Znaczenie w `piper-mat`

W `piper-mat` zweryfikowany punkt bazowy rozpoczyna dostrajanie, a punkty sesyjne pozwalają wybierać kandydatów i bezpiecznie wznawiać pracę.

## Użycie w procesie

Przed użyciem artefakt należy zweryfikować względem manifestu. Do wznowienia wybiera się punkt końcowy poprzedniej sesji, natomiast do eksportu ONNX punkt wybrany na podstawie walidacji i odsłuchu.

## Parametry, jednostki i formaty

Pliki mają rozszerzenie `.ckpt`. Identyfikuje je ścieżka, epoka, krok, rozmiar i suma SHA-256. Pełny punkt może zawierać parametry modelu, optymalizator, harmonogram i liczniki.

## Praktyczne wartości i ich skutki

| Przykład | Zastosowanie |
| --- | --- |
| `checkpoints/base.ckpt` | Zweryfikowany punkt bazowy używany do rozpoczęcia dostrajania. |
| `output/training_state/session_01/last.ckpt` | Pełny stan końca pierwszej sesji, właściwy do wznowienia. |
| Punkt o najlepszym `val_mel` | Kandydat do odsłuchu i porównania przed eksportem ONNX. |

Aktywny punkt bazowy opisany w projekcie ma 845 898 328 bajtów. Plik mający tylko kilkaset bajtów może być wskaźnikiem Git LFS, a nie właściwym modelem.

## Przykład z repozytorium

```bash
python scripts/verify_checkpoint.py checkpoints/base.ckpt
```

## Typowe błędy interpretacyjne

- Traktowanie dowolnego `.ckpt` jako zgodnego z każdą konfiguracją.
- Mylenie inicjalizacji nowego eksperymentu ze wznowieniem pełnego stanu.
- Wybór pliku wyłącznie na podstawie nazwy lub ostatniej epoki.

## Powiązane artykuły i procedury

- [Dostrajanie](dostrajanie.md)
- [Wznowienie trenowania](wznowienie-trenowania.md)
- [Zarządzanie punktami](../CHECKPOINTS.md)
- [Trenowanie etapowe](../STAGED_TRAINING.md)
