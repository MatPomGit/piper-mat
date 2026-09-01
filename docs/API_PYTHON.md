# Interfejs programistyczny Python

Interfejs programistyczny aplikacji (application programming interface, API) dla języka Python pozwala wczytać model Pipera bezpośrednio w procesie aplikacji. W przeciwieństwie do wielokrotnego uruchamiania interfejsu wiersza poleceń model może pozostać w pamięci i obsługiwać kolejne żądania syntezy.

Nazwy klas, metod, parametrów i pól pozostają niezmienione, ponieważ stanowią część API. Ich znaczenie opisujemy po polsku zgodnie ze [słownikiem terminologii](TERMINOLOGIA.md).

## Instalacja

Dla opublikowanej wersji Pipera:

```bash
pip install piper-tts
```

Podczas rozwoju `piper-mat` należy używać środowiska projektu i instalacji edytowalnej opisanej w [instrukcji trenowania](TRAINING.md).

## Wczytanie modelu

Dla głosu projektu:

```python
from piper import PiperVoice

voice = PiperVoice.load("/path/to/pl_PL-mateusz-medium.onnx")
```

Wczytanie modelu jest operacją relatywnie kosztowną. W aplikacji obsługującej wiele wypowiedzi obiekt `PiperVoice` powinien być tworzony raz i ponownie wykorzystywany, o ile architektura aplikacji na to pozwala.

## Synteza do pliku WAV

Przykład zapisu mowy do pliku WAV:

```python
import wave

from piper import PiperVoice

MODEL_PATH = "/path/to/pl_PL-mateusz-medium.onnx"
OUTPUT_PATH = "test.wav"
TEXT = "Witaj. To jest przykład syntezy polskiego głosu."

voice = PiperVoice.load(MODEL_PATH)

with wave.open(OUTPUT_PATH, "wb") as wav_file:
    voice.synthesize_wav(TEXT, wav_file)
```

Kontekst `with` zapewnia zamknięcie pliku także wtedy, gdy podczas zapisu wystąpi wyjątek.

## Konfiguracja syntezy

`SynthesisConfig` pozwala modyfikować wybrane właściwości generowanej mowy. Parametry te nie zmieniają wytrenowanych wag modelu. Sterują sposobem wykorzystania modelu podczas wnioskowania (inference).

```python
from piper.config import SynthesisConfig

syn_config = SynthesisConfig(
    volume=1.0,
    length_scale=1.0,
    noise_scale=0.667,
    noise_w_scale=0.8,
    normalize_audio=True,
)
```

Przed użyciem wartości w produkcji należy sprawdzić wartości domyślne i zakresy obsługiwane przez aktualną wersję kodu.

### `volume`

`volume` jest mnożnikiem poziomu sygnału. Wartość `1.0` zachowuje nominalny poziom, `0.5` zmniejsza amplitudę, a wartość większa od `1.0` ją zwiększa.

Zbyt duża wartość może prowadzić do przesterowania (clipping). Parametr ten nie powinien służyć do kompensowania błędów nagłośnienia lub niewłaściwego poziomu danych treningowych.

### `length_scale`

Skala długości (length scale) wpływa na czas trwania generowanej wypowiedzi. Wartość około `1.0` odpowiada nominalnemu tempu modelu. Większa wartość wydłuża wypowiedź, a mniejsza ją skraca.

Przykładowo `2.0` może prowadzić do znacznie wolniejszej mowy, natomiast `0.8` do szybszej. Skrajne wartości mogą pogorszyć naturalność, dlatego parametr należy dobierać odsłuchowo i pomiarowo.

### `noise_scale`

Skala szumu (noise scale) steruje zmiennością generowania związaną z reprezentacją latentną modelu. Zwiększenie wartości może zwiększyć zróżnicowanie realizacji, ale zbyt duża wartość może obniżyć stabilność i naturalność.

Nie należy interpretować tego parametru jako dodawania zwykłego szumu akustycznego do gotowego pliku WAV.

### `noise_w_scale`

Skala szumu długości (noise width scale) wpływa na zmienność przewidywanych czasów trwania elementów wypowiedzi. Może przez to zmieniać rytm i sposób realizacji mowy.

Przy eksperymentach należy zmieniać ten parametr niezależnie od `noise_scale`, aby można było określić, która zmiana odpowiada za obserwowany efekt.

### `normalize_audio`

Normalizacja dźwięku (audio normalization) dostosowuje poziom sygnału wyjściowego zgodnie z mechanizmem zaimplementowanym w Piperze. Ustawienie `False` pozwala otrzymać sygnał bez tej normalizacji.

Wyłączenie normalizacji jest przydatne między innymi podczas pomiarów, gdy dodatkowa obróbka amplitudy utrudniałaby porównanie wyników.

## Użycie konfiguracji

```python
voice.synthesize_wav(
    "To jest wypowiedź z własną konfiguracją syntezy.",
    wav_file,
    syn_config=syn_config,
)
```

Przy porównywaniu modeli należy zachowywać tę samą konfigurację syntezy. W przeciwnym razie różnica odsłuchowa może wynikać z parametrów wnioskowania, a nie z jakości samych modeli.

## CUDA

Jeżeli środowisko zawiera zgodny pakiet `onnxruntime-gpu`, model można wczytać z obsługą CUDA:

```python
voice = PiperVoice.load(
    "/path/to/pl_PL-mateusz-medium.onnx",
    use_cuda=True,
)
```

Samo włączenie CUDA nie gwarantuje mniejszego całkowitego opóźnienia dla każdej długości tekstu. Wydajność należy oceniać na docelowym sprzęcie, np. za pomocą współczynnika czasu rzeczywistego (Real-Time Factor, RTF).

## Synteza strumieniowa

Synteza strumieniowa (streaming synthesis) umożliwia odbieranie kolejnych fragmentów dźwięku bez oczekiwania na zapis całej wypowiedzi do pliku.

```python
for chunk in voice.synthesize("Przykładowa wypowiedź strumieniowa."):
    set_audio_format(
        chunk.sample_rate,
        chunk.sample_width,
        chunk.sample_channels,
    )
    write_raw_data(chunk.audio_int16_bytes)
```

`chunk` jest fragmentem dźwięku (audio chunk). Jego pola opisują między innymi częstotliwość próbkowania, szerokość próbki, liczbę kanałów oraz dane PCM.

Synteza strumieniowa jest szczególnie istotna w aplikacjach interaktywnych, ponieważ pozwala rozpocząć odtwarzanie przed zakończeniem generowania całej wypowiedzi.

## Dopasowania fonemów

Jeżeli model został przygotowany do zwracania dopasowań fonemów do dźwięku (phoneme alignments), można je wykorzystać do synchronizacji mowy z animacją twarzy. Mechanizm opisano szczegółowo w [rozdziale o dopasowaniach](ALIGNMENTS.md).

Dla projektu awatara dane te mogą stanowić wejście do dalszego procesu:

```text
fonemy → znaczniki czasu → wizemy → koartykulacja → animacja twarzy
```

## Zasady implementacyjne

Kod wykorzystujący API powinien być zgodny z PEP 8, a docstringi z PEP 257. Należy również stosować zasadę KISS i unikać niepotrzebnych warstw abstrakcji.

W szczególności:

- model należy wczytywać w jednym, jednoznacznie określonym miejscu,
- konfigurację syntezy warto przekazywać jawnie,
- obsługa błędów powinna rozróżniać problemy modelu, konfiguracji i warstwy wejścia/wyjścia,
- nie należy ukrywać kosztownych operacji w pozornie prostych właściwościach lub konstruktorach pomocniczych,
- funkcje powinny mieć pojedynczą, czytelną odpowiedzialność,
- zmiany zachowania powinny mieć testy.

Pełne zasady pracy z kodem i dokumentacją repozytorium znajdują się w `AGENTS.md`.
