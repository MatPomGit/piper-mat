# Dopasowania fonemów do dźwięku

Dopasowanie fonemów do dźwięku (phoneme alignment) określa, jaki fragment czasowy wygenerowanego sygnału odpowiada poszczególnym fonemom lub ich identyfikatorom. Informacja ta jest szczególnie użyteczna przy synchronizacji mowy z ruchem ust (lip-sync), ponieważ pozwala wyznaczać momenty zmian fonemów i na ich podstawie sterować wizemami (visemes).

W projekcie `piper-mat` funkcja ta ma znaczenie również dla późniejszej integracji głosu `pl_PL-mateusz-medium` z animowanym awatarem.

Obowiązujące odpowiedniki terminów technicznych znajdują się w [słowniku terminologii](TERMINOLOGIA.md).

## Zasada działania

Piper może udostępnić liczbę próbek dźwięku przypadających na każdy identyfikator fonemu użyty podczas syntezy. Znając częstotliwość próbkowania, liczbę próbek można przeliczyć na czas.

Przykładowo przy częstotliwości próbkowania 22 050 Hz fragment długości 2 205 próbek trwa:

```text
2205 / 22050 = 0,1 s
```

Dopasowanie nie jest gotową animacją ust. Stanowi informację czasową, którą dalszy etap systemu może przekształcić na fonemy, wizemy i animację twarzy. Przy naturalnym ruchu ust należy dodatkowo uwzględnić koartykulację, czyli wpływ sąsiednich głosek na sposób realizacji bieżącej artykulacji.

## Przygotowanie modelu

Aby model ONNX udostępniał dopasowania, można zmodyfikować jego graf obliczeniowy poleceniem:

```bash
python -m piper.patch_voice_with_alignment /path/to/model.onnx
```

Operacja wymaga pakietu `onnx`, którego nie należy mylić z `onnxruntime`. `onnx` służy tutaj do modyfikowania struktury modelu, natomiast `onnxruntime` jest środowiskiem wykonawczym używanym do wnioskowania (inference).

Po przygotowaniu model powinien nadal działać w instalacjach Pipera, które nie korzystają z informacji o dopasowaniach.

## Modyfikowanie modelu podczas wczytywania

Alternatywnie model można przygotować w pamięci podczas wczytywania:

```python
voice = PiperVoice.load(
    "/path/to/model.onnx",
    include_alignments=True,
)
```

Wymaga to pakietu `onnx`, który można zainstalować wraz z odpowiednim zestawem zależności:

```bash
pip install "piper-tts[alignment]"
```

Oryginalny plik ONNX pozostaje wtedy niezmieniony. Jeżeli model został wcześniej przygotowany albo pakiet `onnx` nie jest dostępny, głos może zostać wczytany bez danych o dopasowaniach.

## Interfejs Python

Klasa `AudioChunk` udostępnia pola związane z dopasowaniami:

- `phonemes`: fonemy użyte do wygenerowania fragmentu dźwięku,
- `phoneme_ids`: identyfikatory fonemów (phoneme IDs),
- `phoneme_id_samples`: liczby próbek przypisane poszczególnym identyfikatorom,
- `phoneme_alignments`: dopasowania fonemów do liczby próbek.

Pola zależne od dopasowań mogą być niedostępne, jeżeli model ich nie obsługuje lub funkcję wyłączono przez `include_alignments=False`.

Kod korzystający z tej funkcji powinien sprawdzać dostępność danych zamiast zakładać, że każde wywołanie syntezy je zwróci.

## Interfejs C++

Struktura `piper_audio_chunk` udostępnia między innymi:

- `phonemes`: tablicę punktów kodowych o długości `num_phonemes`,
- `phoneme_ids`: tablicę identyfikatorów o długości `num_phoneme_ids`,
- `alignments`: tablicę liczb próbek o długości `num_alignments`.

Tablica `alignments` może być pusta, jeżeli model nie obsługuje dopasowań. Dane wejściowe użyte podczas syntezy pozostają dostępne niezależnie od tego.

## Identyfikatory specjalne

Sekwencja `phoneme_ids` może zawierać identyfikatory specjalne. Typowy układ ma postać:

```text
[1, 0, id1, 0, id2, 0, ..., 2]
```

gdzie:

- `0` oznacza dopełnienie (padding),
- `1` oznacza początek sekwencji (beginning of sequence, BOS),
- `2` oznacza koniec sekwencji (end of sequence, EOS).

Nie należy utożsamiać jednego znaku tekstowego, jednego fonemu i jednego identyfikatora fonemu. Są to różne poziomy reprezentacji, a pojedynczy fonem może odpowiadać więcej niż jednemu identyfikatorowi.

## Odczytywanie czasu fonemów

Tablica `alignments` przechowuje liczbę próbek dźwięku przypadających na kolejne identyfikatory fonemów. Czas można obliczyć ze wzoru:

```text
czas [s] = liczba próbek / częstotliwość próbkowania [Hz]
```

Dla częstotliwości 22 050 Hz:

```text
441 próbek  ≈ 0,020 s
1102 próbek ≈ 0,050 s
2205 próbek = 0,100 s
```

Wartości te są przykładami przeliczenia, a nie zalecanymi czasami trwania fonemów.

## Integracja z wizemami

Wizem (viseme) jest wizualnym odpowiednikiem realizacji głoski lub grupy podobnie wyglądających głosek. Kilka fonemów może prowadzić do tego samego wizemu, ponieważ różnice akustyczne nie zawsze są widoczne na twarzy.

Docelowy przepływ danych może mieć postać:

```text
tekst
  ↓
Piper TTS
  ↓
fonemy i dopasowania czasowe
  ↓
mapowanie fonem → wizem
  ↓
koartykulacja i wygładzanie przejść
  ↓
sterowanie kształtami morfującymi lub riggiem twarzy
```

Nie należy przełączać wizemów skokowo dokładnie na granicach fonemów. Naturalna artykulacja wymaga nakładania się ruchów, wyprzedzania części gestów artykulacyjnych oraz płynnego zanikania poprzedniej pozycji. Parametry koartykulacji powinny być później dobierane eksperymentalnie dla konkretnego systemu animacji.

## Walidacja

Po przygotowaniu modelu z obsługą dopasowań należy sprawdzić co najmniej:

1. czy synteza bez dopasowań nadal działa,
2. czy liczba zwracanych dopasowań jest zgodna z identyfikatorami fonemów,
3. czy suma długości dopasowań odpowiada długości analizowanego fragmentu dźwięku,
4. czy przeliczone znaczniki czasu są monotoniczne,
5. czy dane są wystarczająco stabilne do sterowania systemem lip-sync.

Dopiero po takiej walidacji należy traktować dopasowania jako wiarygodne źródło czasu dla animacji awatara.
