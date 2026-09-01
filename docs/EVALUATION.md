# Ocena jakości głosu

Ocena (evaluation) modelu `pl_PL-mateusz-medium` powinna rozdzielać zrozumiałość, podobieństwo głosu mówcy (speaker similarity), jakość percepcyjną i wydajność. Wyniki należy zapisywać wraz z identyfikatorem modelu, sumami kontrolnymi SHA-256 artefaktów oraz środowiskiem wykonawczym.

## Zamrożony zbiór testowy

Zbiór testowy (test set) jest częścią danych przeznaczoną do końcowej oceny modelu. Nie powinien być używany do strojenia parametrów ani do wyboru punktu kontrolnego.

Do porównań między kolejnymi wersjami należy używać wyłącznie wersjonowanego podziału testowego wygenerowanego przez:

```bash
python scripts/create_splits.py --output dataset/splits.json
```

Plik zawiera ziarno losowania (seed) oraz sumę kontrolną SHA-256 pliku `metadata.csv`. Jeżeli metadane się zmienią, podział należy świadomie wygenerować ponownie i odnotować zmianę w eksperymencie.

Dodatkowy zestaw `tests/polish_sentences.txt` służy do regresji polskiej normalizacji, fonemizacji i syntezy dla konstrukcji trudnych językowo.

## Zrozumiałość: WER i CER

Współczynnik błędów słów (Word Error Rate, WER) oraz współczynnik błędów znaków (Character Error Rate, CER) opisują zgodność rozpoznanej wypowiedzi syntetycznej z tekstem wzorcowym. Niższa wartość oznacza mniejszą liczbę błędów.

Po syntezie zamrożonych zdań należy wykonać transkrypcję niezależnym systemem automatycznego rozpoznawania mowy (Automatic Speech Recognition, ASR). Dane wejściowe mają format JSONL:

```json
{"reference":"tekst wzorcowy","hypothesis":"tekst rozpoznany"}
```

Metryki można policzyć bez dodatkowych zależności:

```bash
python scripts/evaluate_transcripts.py results/transcripts.jsonl \
  --output evaluations/pl_PL-mateusz-medium.json
```

Należy zapisać nazwę i wersję modelu ASR. WER i CER nie są samodzielną miarą naturalności głosu.

## Podobieństwo głosu

Do porównania podobieństwa należy użyć stałego modelu reprezentacji wektorowej mówcy (speaker embedding) i raportować średnie podobieństwo cosinusowe wypowiedzi syntetycznych do referencyjnych nagrań mówcy. W dokumentacji wyniku trzeba podać dokładną nazwę i wersję modelu reprezentacji oraz sposób agregacji.

## Ocena percepcyjna: MOS i CMOS

Średnia ocena opinii słuchaczy (Mean Opinion Score, MOS) służy do ilościowej oceny jakości odbieranej przez człowieka. Porównawcza średnia ocena opinii słuchaczy (Comparative Mean Opinion Score, CMOS) jest przeznaczona do bezpośredniego porównania dwóch wariantów.

Dla oceny percepcyjnej zalecany jest ślepy odsłuch ze stałym zestawem zdań. Należy raportować co najmniej liczbę oceniających, skalę, procedurę randomizacji, średnią, odchylenie standardowe i przedział ufności.

## Wydajność

Każde wydanie powinno być mierzone przynajmniej na:

- CPU x86-64,
- Raspberry Pi 5,
- opcjonalnie GPU używanym podczas rozwoju.

Raportowane wartości:

- współczynnik czasu rzeczywistego (Real-Time Factor, RTF),
- czas do uzyskania pierwszego fragmentu dźwięku, jeżeli używane jest przesyłanie strumieniowe,
- całkowity czas syntezy,
- maksymalne użycie pamięci RAM (peak RAM usage),
- obciążenie CPU,
- rozmiar modelu ONNX.

Dla RTF należy używać definicji:

`RTF = czas obliczeń / czas wygenerowanego dźwięku`

Wartość poniżej 1 oznacza syntezę szybszą niż czas rzeczywisty.

## Podstawowy test poprawności ONNX

Podstawowy test poprawności (smoke test) sprawdza, czy wyeksportowany model można uruchomić i czy generuje on poprawny technicznie sygnał dźwiękowy.

Po każdym eksporcie należy uruchomić:

```bash
python scripts/smoke_test_voice.py \
  --model output/pl_PL-mateusz-medium.onnx
```

Test sprawdza obecność pary ONNX/JSON, poprawność konfiguracji, możliwość wykonania Pipera oraz powstanie niepustego pliku WAV o zgodnej częstotliwości próbkowania (sample rate).

## Minimalny rekord eksperymentu

Wynik opublikowanego eksperymentu powinien zawierać:

- wersję lub identyfikator zatwierdzenia Piper,
- bazowy punkt kontrolny (checkpoint) i jego SHA-256,
- ziarno losowania,
- parametry trenowania,
- wersje Python, PyTorch, Lightning, CUDA i eSpeak NG,
- SHA-256 metadanych zbioru danych oraz pliku podziału,
- WER i CER,
- podobieństwo głosu,
- MOS/CMOS, jeżeli przeprowadzono badanie,
- pomiary wydajności sprzętowej,
- SHA-256 finalnego ONNX i JSON.
