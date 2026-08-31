# Dataset

Kanoniczna karta datasetu znajduje się w `dataset/DATASET_CARD.md`. Nie jest kopiowana do dokumentacji, aby uniknąć dwóch rozbieżnych źródeł prawdy.

## Procedura przed treningiem

1. Uruchom walidację metadanych i WAV.
2. Wygeneruj deterministyczny split train/validation/test.
3. Zapisz seed i SHA-256 pliku `metadata.csv`.
4. Uzupełnij `DATASET_CARD.md` rzeczywistymi statystykami i informacją o licencji.

```bash
python scripts/validate_dataset.py \
  --metadata dataset/metadata.csv \
  --audio-dir dataset/wavs

python scripts/create_splits.py \
  --metadata dataset/metadata.csv \
  --output dataset/splits.json \
  --seed 20260831
```

Plik `dataset/splits.json` powinien zostać zamrożony przed serią eksperymentów porównawczych.
