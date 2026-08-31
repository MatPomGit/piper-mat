# Historia zmian

## 1.7.0

- Dodano fonemizator języka japońskiego wykorzystujący OpenJTalk (`pyopenjtalk-plus`) w nowym dodatku `ja`.
    - `--data.phoneme_type japanese` podczas treningu oraz `"phoneme_type": "japanese"` w konfiguracji głosu podczas syntezy.
    - espeak-ng nie obsługuje kanji w wymaganym zakresie, ponieważ odczytuje nazwy znaków Unicode, ani akcentu wysokościowego.
    - Etykiety pełnokontekstowe są analizowane pod kątem akcentu wysokościowego i odwzorowywane na IPA, dzięki czemu japońskie głosy pozostają zgodne z inicjalizacją opartą na IPA i espeak.
- Dodano `script/setup --ja` oraz instalację dodatku `ja` w ciągłej integracji, aby uruchamiane były testy języka japońskiego.
- `libpiper`: dodano `piper_create_options` i `piper_create_with_options()`, zachowując `piper_create()` jako funkcję opakowującą dla zgodności ABI.

## 1.6.1

- Model g2pW jest teraz uruchamiany przez `piper.g2pw_onnx` zamiast `g2pw.api`, dzięki czemu z dodatku `zh` usunięto zależności `torch` (około 750 MB po instalacji) oraz `requests`.
    - `g2pw.api` importował torch wyłącznie do budowania dopełnionych tensorów i iterowania po partiach; sam model już wcześniej działał przez onnxruntime.
    - Rozwiązanie jest również około 1,5–2 razy szybsze, ponieważ nie uruchamia procesów roboczych DataLoader przy każdym wywołaniu.
    - `g2pW` pozostaje wymagany ze względu na tablice wyszukiwania pinyin/bopomofo.

## 1.6.0

- Dodano fonemizator języka hebrajskiego wykorzystujący Nakdimon.

## 1.5.0

- Dodano wykonywalny interfejs wiersza poleceń `libpiper` w C++, przeniesiony ze starszego repozytorium Piper, wraz z zestawem testów C++.
- Naprawiono kompilowanie `libpiper` w systemie Windows (MSVC, MSYS2-GCC) oraz w ciągłej integracji Windows.
- Zaktualizowano wbudowaną wersję espeak-ng.
- Dodano domyślny identyfikator mówcy dla głosów wielomówcowych.
- Dodano obsługę grupowania samogłosek (`--data.vowel_clusters`).
- Dodano modyfikowanie dopasowań bezpośrednio w pamięci.
- Trening: dodano dyskryminator MRD (wielorozdzielczy STFT), śledzenie funkcji straty i MOS z użyciem UTMOS, poprawki przycinania ciszy oraz usprawnienia wydajności modułu wczytywania danych.
- Podczas treningu przekazywana jest własna mapa identyfikatorów fonemów.

## 1.4.2

- Naprawiono zależność `pathvalidate`.

## 1.4.1

- Dodano brakujące pakiety wheel.

## 1.4.0

- Dodano fonemizator języka chińskiego oparty na [g2pW](https://github.com/GitYCC/g2pW/).
    - Używana jest skwantyzowana wersja oryginalnego modelu utworzona za pomocą `quantize_dynamic`.
- Dodano `--data.phoneme_type pinyin` do chińskiej fonemizacji za pomocą g2pW.
- Dodano `--data.phoneme_type text` do bezpośredniego używania fonemów IPA bez espeak-ng.
- Dodano `--model.vocoder_warmstart_ckpt <CHECKPOINT>` do przywracania wyłącznie parametrów wokodera.
- Dodano `--data.dataset_type 'phoneme_ids'` do treningu z wcześniej wygenerowanymi identyfikatorami fonemów.
    - `--data.num_symbols <N>` ustawia liczbę fonemów.
    - `--data.phonemes_path "/path/to/phonemes.json"` wskazuje mapę fonemów i identyfikatorów.
- Dodano opcję `--output-dir-naming` z wartościami `timestamp` (domyślną) i `text`.

## 1.3.1

- Dodano eksperymentalną obsługę dopasowań, opisaną w `docs/ALIGNMENTS.md`.
- Surowe fonemy nie powodują już dzielenia zdań.
- Naprawiono trening głosów wielomówcowych.

## 1.3.0

- Rozwój projektu przeniesiono do organizacji OHF-Voice.
- Tymczasowo usunięto kod C++, aby skoncentrować rozwój na Pythonie.
    - Planowany jest interfejs C `libpiper` napisany w C++.
- espeak-ng jest osadzany bezpośrednio zamiast korzystania z oddzielnej biblioteki `piper-phonemize`.
- Zmieniono licencję na GPLv3.
- Używany jest stabilny ABI Pythona (3.9+), dzięki czemu wymagany jest tylko jeden pakiet wheel na platformę.
- Zmieniono interfejs Python:
    - `PiperVoice.synthesize` przyjmuje `SynthesisConfig` i generuje obiekty `AudioChunk`.
    - `PiperVoice.synthesize_raw` został usunięty.
- Dodano oddzielne narzędzie `piper.download_voices` do pobierania głosów z Hugging Face.
- Tekst może być przekazywany jako argument wiersza poleceń: `piper ... -- "Text to speak"`.
- Tekst może być wczytywany z jednego lub wielu plików za pomocą `--input-file <FILE>`.
- Jeśli nie podano argumentów zapisu do pliku, dźwięk jest odtwarzany bezpośrednio za pomocą `ffplay`.
- Dodano obsługę surowych fonemów w tekście w postaci `[[ <phonemes> ]]`.
- Głośność wyjściową można regulować za pomocą `--volume <MULTIPLIER>`; wartość domyślna wynosi 1.0.
