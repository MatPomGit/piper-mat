# Trening etapowy i wznawianie

Projekt obsługuje trening podzielony na kilka niezależnych sesji. Po zakończeniu każdej sesji stan modelu i optymalizatora jest zapisywany w punkcie kontrolnym Lightning, powstaje raport z metrykami i wykresami, a komputer można bezpiecznie wyłączyć. Kolejne uruchomienie automatycznie wznawia trening od końca poprzedniej sesji.

## Plan sesji

Plan znajduje się w `configs/pl_PL-mateusz-medium.json`:

```json
"sessions": {
  "epochs_per_session": [250, 250, 250, 250]
}
```

Domyślnie są to cztery podejścia po 250 dodatkowych epok. Można zmienić plan, np.:

```json
[200, 200, 200]
```

dla trzech sesji albo:

```json
[150, 150, 150, 150, 150, 150]
```

dla sześciu sesji. Wartości oznaczają **dodatkowe epoki wykonywane w danej sesji**, a nie bezwzględne numery epok. Menedżer odczytuje epokę bazowego punktu kontrolnego i sam oblicza poprawne `trainer.max_epochs`.

## Kontrola przed pierwszym treningiem

Po sklonowaniu repozytorium i pobraniu Git LFS wykonaj:

```bash
git lfs pull
python -m pip install -e '.[train]'
./build_monotonic_align.sh
python setup.py build_ext --inplace
python scripts/check_training_ready.py
```

Na Windows po instalacji zależności i zbudowaniu rozszerzenia uruchom:

```powershell
python scripts/check_training_ready.py
```

Kontrola sprawdza m.in.:

- konfigurację treningu i plan sesji,
- obecność `metadata.csv` i WAV,
- czy pliki Git LFS zostały rzeczywiście pobrane,
- bazowy punkt kontrolny,
- moduły `torch`, `lightning`, `tensorboard`, `librosa` i `piper`,
- rozszerzenie `monotonic_align`,
- podstawową ilość wolnego miejsca na dysku.

## Uruchomienie pierwszej sesji

Linux:

```bash
./train.sh
```

Windows PowerShell:

```powershell
.\train.ps1
```

Skrypt:

1. odczytuje bazowy punkt kontrolny,
2. odczytuje jego numer epoki,
3. oblicza cel pierwszej sesji,
4. uruchamia `python -m piper.train fit`,
5. po poprawnym zakończeniu znajduje `last.ckpt`,
6. archiwizuje punkt końcowy oraz najlepsze punkty według `val_mel` i `val_mos`, jeśli są dostępne,
7. generuje raport Markdown i wykresy SVG,
8. zapisuje `output/training_state/state.json`.

Po komunikacie:

```text
Sesja N zakończona. Można bezpiecznie wyłączyć komputer.
```

komputer może zostać wyłączony.

## Wznowienie w kolejnym dniu

Uruchom dokładnie to samo polecenie:

```powershell
.\train.ps1
```

albo:

```bash
./train.sh
```

Menedżer odczyta `output/training_state/state.json`, wybierze końcowy punkt kontrolny poprzedniej sesji i wznowi pełny stan Lightning. Obejmuje to model, optymalizatory, harmonogramy uczenia oraz licznik epok i kroków zapisany w punkcie kontrolnym.

Nie trzeba ręcznie podawać ścieżki do poprzedniego checkpointu.

## Sprawdzenie postępu bez uruchamiania treningu

Linux:

```bash
./train.sh --status
```

Windows:

```powershell
.\train.ps1 -Status
```

Przykładowy wynik:

```text
Ukończone sesje: 2/4
Punkt startowy: epoka 2164 (...)
Ostatni punkt kontrolny: output/training_state/session_02/last.ckpt
Następna sesja: 3, dodatkowe epoki: 250
```

## Podgląd następnej sesji

Bez uruchamiania obliczeń:

```bash
./train.sh --dry-run
```

lub:

```powershell
.\train.ps1 -DryRun
```

## Raport po każdej sesji

Raporty trafiają do:

```text
output/training_reports/session_01/
output/training_reports/session_02/
...
```

Każdy katalog zawiera:

```text
REPORT.md
summary.json
charts/
```

Generator odczytuje skalarne logi TensorBoard i tworzy wykresy SVG dla najważniejszych dostępnych metryk, w szczególności metryk zawierających nazwy `loss`, `mel`, `mos`, `disc`, `gen`, `kl`, `duration` i `learning_rate`.

Raport zawiera dla każdej wybranej metryki:

- pierwszy i ostatni krok,
- wartość początkową i końcową,
- minimum i maksimum,
- wykres przebiegu w czasie.

## Punkty kontrolne po sesji

Trwałe punkty trafiają do:

```text
output/training_state/session_01/
```

W zależności od dostępnych metryk mogą znajdować się tam:

```text
last.ckpt
best_val_mel.ckpt
best_val_mos.ckpt
```

`last.ckpt` jest punktem używanym do wznowienia kolejnej sesji. Punkty `best_*` służą do późniejszego odsłuchu i wyboru kandydata do eksportu ONNX.

Piper sam zapisuje `last.ckpt` i najlepsze modele dzięki callbackom `ModelCheckpoint`. Projekt po zakończeniu sesji archiwizuje wybrane pliki i może usunąć pozostałe tymczasowe checkpointy, aby ograniczyć zajętość dysku.

## Przerwanie awaryjne

Jeżeli trening zostanie przerwany błędem albo ręcznie przed dojściem do zaplanowanego końca sesji, `state.json` **nie jest przesuwany do kolejnej sesji**. Następne uruchomienie rozpocznie tę samą sesję od ostatniego oficjalnie zakończonego punktu kontrolnego poprzedniej sesji.

Nie należy wyłączać komputera przez odcięcie zasilania podczas zapisu checkpointu. Najbezpieczniej poczekać na zakończenie zaplanowanej sesji.

## Jednorazowy trening bez menedżera sesji

Niski poziom pozostaje dostępny:

```bash
python scripts/train_voice.py --dry-run
python scripts/train_voice.py
```

Można również jawnie podać punkt wznowienia i limit epok:

```bash
python scripts/train_voice.py \
  --checkpoint output/training_state/session_02/last.ckpt \
  --max-epochs 2915 \
  --default-root-dir output/manual-run
```

Do normalnego trenowania głosu zalecany jest jednak `train.sh` lub `train.ps1`, ponieważ menedżer sesji pilnuje stanu, raportów i archiwizacji.
