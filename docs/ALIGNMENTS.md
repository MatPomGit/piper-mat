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

## Dwa poziomy danych czasowych

W projekcie należy rozróżniać dwa poziomy reprezentacji.

Pierwszy poziom to surowe dopasowanie zwracane przez Pipera. `PhonemeAlignment` przechowuje fonem, odpowiadające mu identyfikatory oraz liczbę próbek `num_samples`. Jest to reprezentacja bliska sposobowi działania modelu.

Drugi poziom to bezwzględna oś czasu. `PhonemeTiming` przechowuje:

- `phoneme`, czyli symbol fonemu,
- `phoneme_ids`, czyli odpowiadające mu identyfikatory modelu,
- `start_sample`, czyli pierwszą próbkę fonemu,
- `end_sample`, czyli pierwszą próbkę po zakończeniu fonemu,
- `start_seconds`, czyli początek w sekundach,
- `end_seconds`, czyli koniec w sekundach.

Przedział jest półotwarty: `start_sample` należy do fonemu, natomiast `end_sample` jest już początkiem kolejnego odcinka. Taki zapis eliminuje niejednoznaczność na granicy dwóch fonemów.

## Przygotowanie modelu

Aby model ONNX udostępniał dopasowania, można zmodyfikować jego graf obliczeniowy poleceniem:

```bash
python -m piper.patch_voice_with_alignment /path/to/model.onnx
```

Operacja wymaga pakietu `onnx`, którego nie należy mylić z `onnxruntime`. `onnx` służy tutaj do modyfikowania struktury modelu, natomiast `onnxruntime` jest środowiskiem wykonawczym używanym do wnioskowania.

Domyślnie polecenie nadpisuje wskazany model. Aby zachować plik źródłowy, należy użyć osobnej ścieżki:

```bash
python -m piper.patch_voice_with_alignment \
  /path/to/model.onnx \
  --output /path/to/model-with-alignments.onnx
```

Po przygotowaniu model powinien nadal działać w instalacjach Pipera, które nie korzystają z informacji o dopasowaniach.

## Modyfikowanie modelu podczas wczytywania

Alternatywnie model można przygotować w pamięci podczas wczytywania:

```python
from piper import PiperVoice

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

## Konwersja do osi czasu

Moduł `piper.alignment_timing` udostępnia funkcję `phoneme_alignments_to_timings`. Funkcja nie zależy od konkretnego silnika animacji i dlatego stanowi zalecany punkt integracji z Avatar 3D.

```python
from piper import phoneme_alignments_to_timings

for chunk in voice.synthesize(text, include_alignments=True):
    if chunk.phoneme_alignments is None:
        continue

    timings = phoneme_alignments_to_timings(
        chunk.phoneme_alignments,
        chunk.sample_rate,
    )

    for timing in timings:
        print(
            timing.phoneme,
            timing.start_seconds,
            timing.end_seconds,
        )
```

Dla wielu fragmentów dźwięku można użyć parametru `start_sample`, aby umieścić kolejne fragmenty na jednej osi czasu. Jest to istotne, ponieważ `PiperVoice.synthesize()` może zwrócić osobny `AudioChunk` dla każdego zdania.

Przykład dla drugiego fragmentu:

```python
second_timings = phoneme_alignments_to_timings(
    second_chunk.phoneme_alignments,
    second_chunk.sample_rate,
    start_sample=len(first_chunk.audio_float_array),
)
```

W docelowej integracji należy uwzględnić również ciszę dodawaną pomiędzy zdaniami. Offset kolejnego fragmentu musi odpowiadać rzeczywistej pozycji w końcowym strumieniu dźwięku, a nie tylko sumie długości samych fragmentów mowy.

## Format do wymiany danych

`PhonemeTiming.to_dict()` zwraca strukturę możliwą do zapisania jako JSON. Przykładowy rekord może wyglądać następująco:

```json
{
  "phoneme": "a",
  "phoneme_ids": [10, 0],
  "start_sample": 0,
  "end_sample": 2205,
  "start_seconds": 0.0,
  "end_seconds": 0.1
}
```

W plikach przeznaczonych do integracji czasu rzeczywistego zaleca się przechowywanie zarówno indeksów próbek, jak i czasu w sekundach. Indeksy próbek są dokładniejszym źródłem prawdy, natomiast sekundy są wygodniejsze dla silników animacji.

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

Czas można obliczyć ze wzoru:

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

Docelowy przepływ danych ma postać:

```text
tekst
  ↓
Piper TTS
  ↓
PhonemeAlignment
  ↓
PhonemeTiming
  ↓
mapowanie fonem → wizem
  ↓
koartykulacja i wygładzanie przejść
  ↓
sterowanie kształtami morfującymi lub riggiem twarzy
```

Mapowania fonemów na wizemy nie należy umieszczać w rdzeniu Pipera. Jest ono zależne od języka, zestawu wizemów, sposobu riggowania twarzy i docelowego silnika animacji. Piper powinien dostarczać wiarygodną warstwę fonetyczną i czasową, a Avatar 3D powinien odpowiadać za interpretację wizualną.

Nie należy przełączać wizemów skokowo dokładnie na granicach fonemów. Naturalna artykulacja wymaga nakładania się ruchów, wyprzedzania części gestów artykulacyjnych oraz płynnego zanikania poprzedniej pozycji. Parametry koartykulacji powinny być później dobierane eksperymentalnie dla konkretnego systemu animacji.

## Walidacja

Po przygotowaniu modelu z obsługą dopasowań należy sprawdzić co najmniej:

1. czy synteza bez dopasowań nadal działa,
2. czy liczba zwracanych dopasowań jest zgodna z identyfikatorami fonemów,
3. czy suma długości dopasowań odpowiada długości analizowanego fragmentu dźwięku,
4. czy przeliczone znaczniki czasu są monotoniczne,
5. czy `end_sample` jednego fonemu jest równy `start_sample` następnego,
6. czy dane są wystarczająco stabilne do sterowania systemem lip-sync.

Dopiero po takiej walidacji należy traktować dopasowania jako wiarygodne źródło czasu dla animacji awatara.
