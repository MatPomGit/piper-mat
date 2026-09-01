# Zbiór danych

Zbiór danych (dataset) to uporządkowany zestaw nagrań i odpowiadających im metadanych używanych do trenowania, walidacji i testowania modelu głosu. Jakość zbioru danych bezpośrednio wpływa na zrozumiałość, naturalność oraz stabilność syntezy.

Kanoniczna karta zbioru danych znajduje się w `dataset/DATASET_CARD.md`. Nie jest kopiowana do dokumentacji, aby uniknąć dwóch rozbieżnych źródeł prawdy.

## Procedura przed trenowaniem

1. Uruchom walidację metadanych i plików WAV.
2. Wygeneruj deterministyczny podział zbioru danych (data split) na część treningową, walidacyjną i testową.
3. Zapisz ziarno losowania (seed) i sumę kontrolną SHA-256 pliku `metadata.csv`.
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

Plik `dataset/splits.json` powinien zostać zamrożony przed serią eksperymentów porównawczych. Dzięki temu wszystkie wersje modelu są oceniane na tych samych danych, co ogranicza wpływ losowego podziału na wynik porównania.

Obowiązujące nazewnictwo pojęć związanych ze zbiorem danych znajduje się w [słowniku terminologii](TERMINOLOGIA.md).
