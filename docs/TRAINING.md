# Trenowanie modelu głosu

Ten rozdział opisuje kanoniczny proces [trenowania (training)](terminologia/trenowanie.md) `pl_PL-mateusz-medium`. Projekt wykorzystuje [dostrajanie (fine-tuning)](terminologia/dostrajanie.md) zgodnego modelu bazowego zamiast trenowania od losowo zainicjalizowanych parametrów.

Zaawansowane tryby Pipera, które nie są potrzebne w bieżącym eksperymencie, nie są tutaj opisywane. Ogranicza to ryzyko przypadkowego zmieszania kilku różnych metod przygotowania danych.

## Przygotowanie środowiska

Linux:

```bash
git clone https://github.com/MatPomGit/piper-mat.git
cd piper-mat
git lfs pull
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[train]'
```

Windows:

```powershell
git clone https://github.com/MatPomGit/piper-mat.git
cd piper-mat
git lfs pull
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[train]"
```

Dla Windows preferowany jest [kreator Windows 11](WINDOWS_GUI.md), ponieważ dodatkowo sprawdza narzędzia systemowe, CUDA, Git LFS, dane i punkt kontrolny.

## `monotonic_align`

`monotonic_align` realizuje monotoniczne dopasowanie (monotonic alignment) pomiędzy reprezentacją tekstu i przebiegiem czasowym mowy. Jest wymagane podczas trenowania modelu.

W systemie zgodnym z powłoką POSIX:

```bash
./build_monotonic_align.sh
```

W razie potrzeby rozszerzenia projektu można zbudować również w bieżącym drzewie:

```bash
python setup.py build_ext --inplace
```

## Zbiór danych

Zbiór danych (dataset) składa się z plików WAV i dokładnych transkrypcji. Kanoniczne zasady walidacji znajdują się w [DATASET.md](DATASET.md) oraz `dataset/DATASET_CARD.md`.

Przykład `metadata.csv`:

```text
000001.wav|Dzień dobry, to jest pierwsza wypowiedź treningowa.
000002.wav|Model powinien poprawnie odtwarzać polską wymowę.
```

Tekst musi odpowiadać rzeczywiście wypowiedzianej treści. Nie należy poprawiać transkrypcji do formy, której nie ma w nagraniu.

Przed trenowaniem należy wykonać:

```bash
python scripts/validate_dataset.py \
  --metadata dataset/metadata.csv \
  --audio-dir dataset/wavs
```

## Najważniejsze parametry

### `model.sample_rate`

[Częstotliwość próbkowania (sample rate)](terminologia/czestotliwosc-probkowania.md) określa liczbę próbek sygnału na sekundę. Dla bieżącego modelu przyjęto:

```text
22050 Hz
```

Wartość musi być zgodna z konfiguracją modelu bazowego i przygotowaniem danych. Nie należy zmieniać jej w trakcie tego samego eksperymentu.

### `data.batch_size`

Rozmiar partii (batch size) określa liczbę przykładów przetwarzanych w jednej partii trenowania. Typowe wartości do sprawdzenia to `8`, `16` i `32`.

Większa wartość zwiększa zapotrzebowanie na pamięć GPU. Mniejsza ogranicza zużycie pamięci, ale zmienia charakterystykę optymalizacji i może zmniejszyć wykorzystanie GPU.

Wartość należy dobrać przed właściwą serią eksperymentów i zapisać w konfiguracji.

### `ckpt_path`

`ckpt_path` wskazuje [punkt kontrolny (checkpoint)](terminologia/punkt-kontrolny.md), z którego odtwarzany jest stan modelu. W pierwszej sesji dostrajania jest to zweryfikowany model bazowy. Przy wznowieniu trenowania używany jest punkt kontrolny poprzedniej sesji.

Szczegóły znajdują się w [CHECKPOINTS.md](CHECKPOINTS.md).

### `data.espeak_voice`

Parametr wybiera głos eSpeak NG używany do [fonemizacji (phonemization)](terminologia/fonemizacja.md). Dla polskiego zbioru projektu używana jest wartość:

```text
pl
```

Zmiana fonemizatora może zmienić reprezentację wejściową tekstu i dlatego nie powinna być wykonywana przypadkowo w środku eksperymentu.

## Kanoniczne uruchamianie

Ręczne polecenie niskiego poziomu może wyglądać następująco:

```bash
python -m piper.train fit \
  --data.voice_name "pl_PL-mateusz-medium" \
  --data.csv_path dataset/metadata.csv \
  --data.audio_dir dataset/wavs \
  --model.sample_rate 22050 \
  --data.espeak_voice "pl" \
  --data.cache_dir cache \
  --data.config_path output/pl_PL-mateusz-medium.onnx.json \
  --data.batch_size 16 \
  --ckpt_path checkpoints/base.ckpt
```

Pełną listę argumentów należy sprawdzać względem bieżącej implementacji:

```bash
python -m piper.train fit --help
```

W codziennej pracy nad `pl_PL-mateusz-medium` preferowane są jednak `train.ps1`, `train.sh` albo kreator Windows, ponieważ implementują kontrolowany proces sesji i wznowień opisany w [STAGED_TRAINING.md](STAGED_TRAINING.md).

## Wznowienie a nowy eksperyment

[Wznowienie trenowania (resume training)](terminologia/wznowienie-trenowania.md) kontynuuje wcześniejszy przebieg wraz z zapisanym stanem optymalizatora i harmonogramu. Jest czymś innym niż rozpoczęcie nowego eksperymentu z wagami modelu bazowego.

Jeżeli zmiana konfiguracji wpływa na znaczenie eksperymentu, należy rozważyć rozpoczęcie nowego przebiegu zamiast ukrywania zmiany we wznowionej sesji.

## Zaawansowane tryby danych

Piper obsługuje również bezpośrednie fonemy i wcześniej wygenerowane identyfikatory fonemów. Nie są one częścią podstawowego procesu `pl_PL-mateusz-medium`.

Jeżeli przyszły eksperyment będzie ich wymagał, należy utworzyć osobną konfigurację i dokumentację. W aktualnej implementacji tryb danych z identyfikatorami fonemów jest określany przez `--data.dataset_type phoneme_ids`, nie przez historyczne lub błędne warianty nazwy argumentu.

## Eksport [ONNX](terminologia/onnx.md)

Po zakończeniu trenowania należy najpierw wybrać punkt kontrolny na podstawie walidacji i odsłuchu. Dopiero wybrany kandydat jest eksportowany:

```bash
python -m piper.train.export_onnx \
  --checkpoint /path/to/checkpoint.ckpt \
  --output-file output/pl_PL-mateusz-medium.onnx
```

Finalna para:

```text
pl_PL-mateusz-medium.onnx
pl_PL-mateusz-medium.onnx.json
```

musi następnie przejść test techniczny i ocenę opisaną w [EVALUATION.md](EVALUATION.md).

## Pamięć GPU

Zapotrzebowanie na pamięć zależy między innymi od rozmiaru partii, długości segmentów i konfiguracji modelu. Przy błędzie braku pamięci GPU pierwszym parametrem do weryfikacji jest zwykle `data.batch_size`.

Nie należy zmieniać wielu parametrów jednocześnie tylko po to, aby trenowanie się uruchomiło. Każda istotna zmiana powinna być zapisana w konfiguracji eksperymentu.

## Reprodukowalność

Każdy istotny eksperyment powinien pozostawić:

- identyfikowalną wersję zbioru danych,
- zamrożony podział danych,
- konfigurację,
- bazowy punkt kontrolny i jego SHA-256,
- ziarno losowania,
- wersję kodu,
- zapis środowiska,
- wynikowe punkty kontrolne,
- raporty sesji.

Aktualna kolejność prac i kryteria zakończenia są utrzymywane w [ROADMAP.md](ROADMAP.md).
