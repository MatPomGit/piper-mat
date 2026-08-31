# 🏋️ Trenowanie

Kod do trenowania nowych głosów znajduje się w `src/piper/train` i można go uruchomić za pomocą `python3 -m piper.train fit`.
Wykorzystuje on [PyTorch Lightning][lighting] oraz `LightningCLI`.

Należy zainstalować następujące pakiety systemowe (`apt-get`):

* `build-essential`
* `cmake`
* `ninja-build`

Następnie sklonuj repozytorium i zainstaluj zależności do trenowania:

``` sh
git clone https://github.com/OHF-voice/piper1-gpl.git
cd piper1-gpl
python3 -m venv .venv
source .venv/Scripts/activate # windows
source .venv/bin/activate #linux
python3 -m pip install -e '.[train]'
```

a następnie zbuduj rozszerzenie Cython:

``` sh
./build_monotonic_align.sh
```

W przypadku uruchamiania z repozytorium należy wykonać kompilację deweloperską:

``` sh
python3 setup.py build_ext --inplace
```

Do trenowania potrzebny jest plik CSV z separatorem `|` w następującym formacie:

``` csv
utt1.wav|Text for utterance 1.
utt2.wav|Text for utterance 2.
...
```

Pierwsza kolumna zawiera nazwę pliku dźwiękowego (w dowolnym formacie obsługiwanym przez [librosa][]), który musi znajdować się w `--data.audio_dir` (zobacz niżej).

Pozostałe kolumny zależą od [ustawień trenowania](#ustawienia). Domyślnie druga kolumna zawiera tekst przekazywany do [espeak-ng][] w celu fonemizacji (podobnie jak w `espeak-ng --ipa=3`).

Uruchom skrypt trenujący:

``` sh
python3 -m piper.train fit \
  --data.voice_name "<name of voice>" \
  --data.csv_path /path/to/metadata.csv \
  --data.audio_dir /path/to/audio/ \
  --model.sample_rate 22050 \
  --data.espeak_voice "<espeak voice name>" \
  --data.cache_dir /path/to/cache/dir/ \
  --data.config_path /path/to/write/config.json \
  --data.batch_size 32 \
  --ckpt_path /path/to/finetune.ckpt  # optional but highly recommended
```

gdzie:

* `data.voice_name` to nazwa głosu (może być dowolna)
* `data.csv_path` to ścieżka do pliku CSV z nazwami plików dźwiękowych i tekstem
* `data.audio_dir` to katalog zawierający pliki dźwiękowe (zwykle `.wav`)
* `model.sample_rate` to częstotliwość próbkowania dźwięku w hercach (zwykle 22050)
* `data.espeak_voice` to głos/język espeak-ng, na przykład `en-us` (zobacz `espeak-ng --voices`)
* `data.cache_dir` to katalog, w którym buforowane są artefakty trenowania (fonemy, przycięty dźwięk itd.)
* `data.config_path` to ścieżka zapisu pliku konfiguracji JSON głosu
* `data.batch_size` to rozmiar partii podczas trenowania
* `ckpt_path` to ścieżka do istniejącego [punktu kontrolnego Pipera][piper-checkpoints]

Zaleca się użycie `--ckpt_path`, ponieważ znacznie przyspiesza trenowanie, nawet jeśli punkt kontrolny pochodzi z innego języka. Bez [dostosowania innych ustawień][audio-config] obsługiwane są tylko punkty kontrolne jakości `medium`.

Uruchom `python3 -m piper.train fit --help`, aby poznać wiele innych opcji.

## Ustawienia

Niektóre ustawienia trenowania zmieniają format danych wejściowych.

### Wielu mówców

Jeśli zbiór danych zawiera więcej niż jednego mówcę, format wejściowego pliku CSV zmienia się na:

``` csv
utt1.wav|speaker_1|Text for utterance 1 with first speaker.
utt2.wav|speaker_2|Text for utterance 2 with second speaker.
...
```

gdzie `speaker_1` i `speaker_2` są **nazwami** mówców. Po rozpoczęciu trenowania Piper policzy unikatowe nazwy mówców i utworzy mapowanie nazw mówców na identyfikatory. Mapowanie zostanie zapisane w pliku `config.json` głosu (`--data.config_path`).

### Własne fonemy

Aby pominąć fonemizację za pomocą `espeak-ng`, ustaw `--data.phoneme_type text` i użyj formatu CSV:

``` csv
utt1.wav|phonemes_for_utt_1
utt2.wav|phonemes_for_utt_2
...
```

Ostatnia kolumna zawiera teraz punkty kodowe UTF-8, które mają być fonemami każdej wypowiedzi. W języku Python są one przekształcane w listę za pomocą:

```python
phonemes_list = list(unicodedata.normalize("NFD", phonemes_text))
```

Fonemy przechodzą zwykły proces tworzenia identyfikatorów fonemów, obejmujący dodanie identyfikatorów BOS/EOS i wstawienie PAD.

### Własne identyfikatory fonemów

Aby uzyskać pełną kontrolę nad fonemizacją, użyj `--data.data_type phoneme_ids` oraz formatu CSV:

``` csv
utt1.wav|Text for utterance 1.|0 1 2 3 4 5
utt2.wav|Text for utterance 2.|5 4 3 2 1 0
...
```

Model zostanie wytrenowany dokładnie z podanymi identyfikatorami fonemów. Należy ustawić `--data.num_symbols <N>` na liczbę posiadanych identyfikatorów fonemów, chyba że ma zostać użyta wartość domyślna 256.

Ustawienie `--data.phonemes_path <FILE>` skopiuje mapę fonemów i identyfikatorów do pliku konfiguracji głosu (`--data.config_path`). Plik ten jest obiektem JSON mapującym fonemy na identyfikatory:

```json
{
  "phoneme_1": 0,
  "phoneme_2": 1,
  ...
}
```

### Wstępna inicjalizacja wokodera

Podczas trenowania nowego modelu od podstaw można znacznie przyspieszyć ten proces za pomocą `--model.vocoder_warmstart_ckpt <CHECKPOINT>`. Spowoduje to skopiowanie parametrów modelu wokodera, ale nie warstwy osadzania fonemów.

W przeciwieństwie do `--ckpt_path` użycie `--model.vocoder_warmstart_ckpt` pozwala trenować model z inną liczbą fonemów bez rozpoczynania całkowicie od podstaw.

## Eksportowanie

Po zakończeniu trenowania wyeksportuj model do formatu ONNX za pomocą:

``` sh
python3 -m piper.train.export_onnx \
  --checkpoint /path/to/checkpoint.ckpt \
  --output-file /path/to/model.onnx
```

Aby zapewnić zgodność z innymi głosami Pipera, zmień nazwę `model.onnx` na `<language>-<name>-medium.onnx` (np. `en_US-lessac-medium.onnx`). Plikowi konfiguracji JSON zapisanemu w `--data.config_path` **podczas trenowania** nadaj tę samą nazwę z rozszerzeniem `.json`. Głos będzie więc składał się z dwóch plików:

* `en_US-lessac-medium.onnx` (ze skryptu eksportującego)
* `en_US-lessac-medium.onnx.json` (z trenowania)

## Sprzęt

Większość głosów Pipera trenowano lub dostrajano na procesorze Threadripper 1900X ze 128 GB pamięci RAM oraz kartą NVIDIA A6000 (48 GB VRAM) albo 3090 (24 GB VRAM).

Użytkownicy zgłaszali udane trenowanie nawet z 8 GB pamięci VRAM i alternatywnymi kartami GPU, takimi jak RX 7600.

<!-- Odnośniki -->
[espeak-ng]: https://github.com/espeak-ng/espeak-ng
[lighting]: https://lightning.ai/docs/pytorch/stable/
[librosa]: https://librosa.org/doc/latest/index.html
[piper-checkpoints]: https://huggingface.co/datasets/rhasspy/piper-checkpoints
[audio-config]: https://github.com/rhasspy/piper/blob/9b1c6397698b1da11ad6cca2b318026b628328ec/src/python/piper_train/vits/config.py#L20
