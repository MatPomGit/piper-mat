# Dopasowania

Do interfejsów API Pipera dla języków Python i C++ dodano eksperymentalną obsługę dopasowań dźwięku.
Udostępnia ona liczbę próbek dźwięku dla każdego **identyfikatora fonemu** użytego podczas syntezy i może służyć do [synchronizowania mowy z ruchem ust][visemes].

## Modyfikowanie głosów

Aby uzyskać dostęp do dopasowań, najpierw należy „zmodyfikować” plik modelu ONNX głosu:

``` sh
python3 -m piper.patch_voice_with_alignment /path/to/model.onnx
```

Wymaga to zainstalowania pakietu Python `onnx` (nie należy go mylić z `onnxruntime`). Po zmodyfikowaniu pakiet `onnx` nie jest już potrzebny. Zmodyfikowane modele ONNX powinny nadal poprawnie działać z istniejącymi instalacjami Pipera.

### Modyfikowanie podczas wczytywania

Alternatywnie można zmodyfikować głos w pamięci podczas jego wczytywania, bez zapisywania zmienionego modelu na dysku:

``` python
voice = PiperVoice.load("/path/to/model.onnx", include_alignments=True)
```

To również wymaga pakietu `onnx` (zainstaluj go poleceniem `pip install piper-tts[alignment]`), ale pozostawia oryginalny plik `.onnx` bez zmian. Jeśli model został już zmodyfikowany albo pakiet `onnx` jest niedostępny, głos zostanie wczytany normalnie, a dopasowania po prostu nie będą dostępne.

## API języka Python

Klasę `AudioChunk` rozszerzono o kilka nowych pól:

* `phonemes` — lista fonemów użytych do utworzenia fragmentu dźwięku
* `phoneme_ids` — lista identyfikatorów fonemów użytych do utworzenia fragmentu dźwięku
* `phoneme_id_samples` — liczba próbek dźwięku dla każdego identyfikatora fonemu
* `phoneme_alignments` — lista dopasowań fonemów do liczby próbek

Pola `phoneme_id_sample` i `phoneme_alignments` będą nieobecne, jeśli model głosu nie obsługuje dopasowań lub wyłączono je za pomocą `include_alignments=False`.

## API języka C++

Strukturę `piper_audio_chunk` rozszerzono o kilka nowych pól:

* `phonemes` — tablica punktów kodowych o długości `num_phonemes`
* `phoneme_ids` — tablica identyfikatorów o długości `num_phoneme_ids`
* `alignments` — tablica liczb próbek o długości `num_alignments`

Tablica `alignments` będzie pusta, jeśli głos nie obsługuje dopasowań, ale tablice `phonemes` i `phonemes_ids` będą zawsze obecne.

Tablica `phoneme_ids` zawiera identyfikatory użyte do syntezy dźwięku danego fragmentu. Ma postać [1, 0, id1, 0, id2, 0, ..., 2], gdzie:

* 0 = wypełnienie
* 1 = początek zdania
* 2 = koniec zdania

Ponieważ jeden fonem może utworzyć wiele identyfikatorów fonemów, tablica `phonemes` jest nieco bardziej złożona. Ma postać [p1, p1, 0, p2, p2, 0, ...], w której ten sam punkt kodowy fonemu jest powtarzany dla każdego odpowiadającego mu identyfikatora w `phoneme_ids`. Wartość 0 oddziela poszczególne fonemy, a w większości przypadków na fonem przypadają dwa punkty kodowe odpowiadające identyfikatorowi fonemu i identyfikatorowi wypełnienia.

Tablica `alignments` zawiera liczbę próbek dźwięku dla każdego identyfikatora fonemu. Przynależność próbek do fonemów można ustalić następująco:

1. Odczytaj N (powtórzonych) punktów kodowych z `phonemes`, aż zostanie napotkane 0 (lub koniec)
2. Następnych N identyfikatorów fonemów odpowiada temu fonemowi
3. Następnych N dopasowań (liczb próbek) odpowiada temu fonemowi
4. Przesuń iteratory w tablicach `phoneme_ids` i `alignments` o N
5. Powtórz

<!-- Odnośniki -->
[visemes]: https://github.com/aflorithmic/viseme-to-video
