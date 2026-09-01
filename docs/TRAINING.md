# Trenowanie modelu głosu

Ten rozdział opisuje podstawowy proces trenowania (training) i dostrajania (fine-tuning) głosu w projekcie `piper-mat`. Dla głosu `pl_PL-mateusz-medium` preferowane jest dostrajanie istniejącego modelu bazowego zamiast rozpoczynania trenowania od losowo zainicjalizowanych parametrów.

Obowiązujące polskie odpowiedniki terminów technicznych znajdują się w [słowniku terminologii](TERMINOLOGIA.md).

## 1. Przygotowanie środowiska

Kod odpowiedzialny za trenowanie znajduje się w `src/piper/train`. Proces można uruchomić za pomocą modułu `piper.train`.

Projekt wykorzystuje PyTorch oraz PyTorch Lightning. Przed rozpoczęciem trenowania należy utworzyć odizolowane środowisko Pythona i zainstalować zależności projektu.

### Linux

```bash
git clone https://github.com/MatPomGit/piper-mat.git
cd piper-mat
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e '.[train]'
```

W systemach opartych na Debianie lub Ubuntu mogą być również potrzebne pakiety `build-essential`, `cmake` i `ninja-build`.

### Windows

```powershell
git clone https://github.com/MatPomGit/piper-mat.git
cd piper-mat
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[train]"
```

Szczegółowy proces przygotowania środowiska w Windows opisano również w [kreatorze dla Windows 11](WINDOWS_GUI.md).

## 2. Rozszerzenie `monotonic_align`

`monotonic_align` realizuje monotoniczne dopasowanie (monotonic alignment) pomiędzy reprezentacją tekstu a sekwencją czasową mowy. W praktyce mechanizm pomaga modelowi nauczyć się, które fragmenty sygnału dźwiękowego odpowiadają kolejnym elementom wypowiedzi.

Rozszerzenie należy zbudować zgodnie z procedurą właściwą dla używanego systemu. W środowisku zgodnym z powłoką POSIX można użyć:

```bash
./build_monotonic_align.sh
```

Jeżeli wymagane jest zbudowanie rozszerzeń bezpośrednio w drzewie źródłowym:

```bash
python setup.py build_ext --inplace
```

## 3. Zbiór danych

Zbiór danych (dataset) składa się z nagrań oraz metadanych łączących każdy plik dźwiękowy z jego transkrypcją. Szczegółowe zasady przygotowania danych projektu opisano w [rozdziale o zbiorze danych](DATASET.md).

Podstawowy plik `metadata.csv` używa separatora `|`:

```text
000001.wav|Dzień dobry, to jest pierwsza wypowiedź treningowa.
000002.wav|Model powinien poprawnie odtwarzać polską wymowę.
```

Pierwsza kolumna wskazuje plik dźwiękowy, a druga zawiera jego dokładną transkrypcję. Nagranie i tekst muszą odpowiadać sobie możliwie dokładnie. Błędy transkrypcji bezpośrednio pogarszają dane uczące model.

## 4. Najważniejsze parametry

Przed uruchomieniem trenowania warto rozumieć znaczenie podstawowych parametrów. Nazwy argumentów programu pozostają niezmienione, ponieważ stanowią część interfejsu programu.

### `model.sample_rate`

Częstotliwość próbkowania (sample rate) określa liczbę próbek sygnału dźwiękowego przypadających na sekundę. Wartość `22050` oznacza 22 050 próbek na sekundę.

Dla modelu bazowego i modelu dostrajanego częstotliwość próbkowania musi być zgodna z przyjętą konfiguracją. W projekcie głosu `pl_PL-mateusz-medium` typową wartością jest:

```text
22050 Hz
```

Nie należy zmieniać jej wyłącznie w celu uzyskania większej liczby próbek, ponieważ wpływa ona na architekturę i zgodność modelu.

### `data.batch_size`

Rozmiar partii (batch size) określa liczbę przykładów przetwarzanych przed wykonaniem pojedynczej aktualizacji parametrów modelu.

Większa wartość zwykle zwiększa zapotrzebowanie na pamięć GPU, ale może poprawić wykorzystanie procesora graficznego. Mniejsza wartość ogranicza zużycie pamięci kosztem innej charakterystyki trenowania i często dłuższego czasu wykonania epoki.

Przykładowe wartości to `8`, `16` i `32`. Dobór zależy od długości nagrań, konfiguracji modelu i dostępnej pamięci GPU. Nie należy traktować największej wartości mieszczącej się w pamięci jako automatycznie najlepszej.

### `ckpt_path`

`ckpt_path` wskazuje punkt kontrolny (checkpoint), z którego zostaną odtworzone parametry modelu. Użycie zgodnego modelu bazowego pozwala rozpocząć dostrajanie od już wyuczonej reprezentacji mowy.

W projekcie `piper-mat` bazowe punkty kontrolne opisano w [osobnym rozdziale](CHECKPOINTS.md).

### `data.espeak_voice`

Parametr wybiera konfigurację językową eSpeak NG używaną podczas fonemizacji (phonemization), czyli zamiany tekstu na reprezentację fonetyczną. Dla języka polskiego należy używać konfiguracji zgodnej z językiem danych, np. `pl`.

## 5. Uruchomienie trenowania

Przykładowe polecenie dla głosu projektu:

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

Ścieżki należy dostosować do rzeczywistego układu lokalnego zbioru danych. Nie należy umieszczać dużych, roboczych danych dźwiękowych ani sekretów w repozytorium tylko po to, aby odpowiadały przykładowemu poleceniu.

Pełną listę opcji można sprawdzić poleceniem:

```bash
python -m piper.train fit --help
```

## 6. Wznowienie trenowania

Wznowienie trenowania (resume training) oznacza kontynuowanie wcześniejszego przebiegu wraz ze stanem zapisanym w punkcie kontrolnym. Nie jest tym samym co rozpoczęcie nowego eksperymentu z parametrami skopiowanymi z modelu bazowego.

Projekt udostępnia osobny proces trenowania etapowego i wznawiania. Został on opisany w [rozdziale o trenowaniu etapowym](STAGED_TRAINING.md).

## 7. Wiele głosów w jednym zbiorze

W przypadku zbioru zawierającego wielu mówców (multi-speaker dataset) metadane mogą zawierać dodatkową kolumnę identyfikującą mówcę:

```text
000001.wav|speaker_1|Pierwsza wypowiedź pierwszego mówcy.
000002.wav|speaker_2|Pierwsza wypowiedź drugiego mówcy.
```

Piper tworzy mapowanie nazw mówców na identyfikatory i zapisuje je w konfiguracji modelu. Głos `pl_PL-mateusz-medium` jest jednak projektem konkretnego mówcy, dlatego nie należy wprowadzać dodatkowych mówców do jego podstawowego zbioru treningowego.

## 8. Własne fonemy

Domyślnie tekst jest poddawany fonemizacji przez eSpeak NG. Zmiana tego mechanizmu jest funkcją zaawansowaną i wymaga zachowania spójności między danymi, konfiguracją oraz modelem.

Po ustawieniu:

```text
--data.phoneme_type text
```

ostatnia kolumna metadanych może bezpośrednio zawierać reprezentację fonemów. Tekst jest normalizowany w Pythonie między innymi za pomocą:

```python
phonemes_list = list(unicodedata.normalize("NFD", phonemes_text))
```

Nie należy wprowadzać własnego systemu fonemów bez wyraźnej potrzeby eksperymentalnej i odpowiedniej walidacji wymowy języka polskiego.

## 9. Własne identyfikatory fonemów

Tryb `--data.data_type phoneme_ids` pozwala przekazać bezpośrednio identyfikatory fonemów (phoneme IDs). Daje to pełniejszą kontrolę nad reprezentacją wejściową, ale jednocześnie przenosi odpowiedzialność za jej poprawność na przygotowanie danych.

Przykład:

```text
000001.wav|Przykładowa wypowiedź.|0 1 2 3 4 5
```

Liczba symboli musi być zgodna z konfiguracją `--data.num_symbols`. Opcja `--data.phonemes_path` może służyć do przekazania mapowania fonemów na identyfikatory.

## 10. Wstępna inicjalizacja wokodera

Wokoder (vocoder) jest częścią systemu odpowiedzialną za przekształcenie reprezentacji generowanej przez model w końcowy przebieg sygnału dźwiękowego.

Opcja:

```text
--model.vocoder_warmstart_ckpt <CHECKPOINT>
```

umożliwia wstępną inicjalizację (warm start) parametrów wokodera z istniejącego punktu kontrolnego bez kopiowania warstwy reprezentującej fonemy. Jest to przydatne przede wszystkim przy eksperymentach wymagających innej liczby symboli fonetycznych.

Dla standardowego dostrajania `pl_PL-mateusz-medium` należy preferować sprawdzony, prostszy proces z odpowiednim `--ckpt_path`, jeżeli nie ma konkretnego powodu do zmiany architektury wejścia.

## 11. Eksport do ONNX

Po zakończeniu trenowania wybrany punkt kontrolny należy wyeksportować do ONNX:

```bash
python -m piper.train.export_onnx \
  --checkpoint /path/to/checkpoint.ckpt \
  --output-file output/pl_PL-mateusz-medium.onnx
```

Docelowy głos składa się co najmniej z dwóch zgodnych plików:

```text
pl_PL-mateusz-medium.onnx
pl_PL-mateusz-medium.onnx.json
```

Sam poprawny eksport nie oznacza jeszcze, że model jest gotowy do publikacji. Należy wykonać test syntezy oraz ocenę jakości zgodnie z [procedurą oceny](EVALUATION.md).

## 12. Sprzęt i pamięć GPU

Zapotrzebowanie na pamięć GPU zależy między innymi od rozmiaru partii, długości nagrań i konfiguracji modelu. Trenowanie jest możliwe na różnych kartach graficznych, dlatego dokumentacja projektu nie powinna zakładać jednej konkretnej konfiguracji sprzętowej jako wymogu.

W przypadku błędu braku pamięci GPU należy najpierw zmniejszyć `data.batch_size`, a następnie zweryfikować długości przykładów i pozostałe ustawienia. Zmiany parametrów powinny być dokumentowane, aby eksperyment można było później odtworzyć.

## 13. Zasady prowadzenia eksperymentu

Każdy istotny przebieg trenowania powinien pozostawić informacje pozwalające go odtworzyć: użyty zbiór i jego podział, konfigurację, bazowy punkt kontrolny, ziarno losowania (seed), wersję kodu oraz wybrany wynikowy punkt kontrolny.

Nie należy zmieniać jednocześnie wielu parametrów bez uzasadnienia. Prostsze eksperymenty ułatwiają ustalenie, która zmiana rzeczywiście wpłynęła na wynik. Jest to zgodne z zasadą KISS i ogranicza ryzyko powstania konfiguracji, której zachowania nie można później wyjaśnić.
