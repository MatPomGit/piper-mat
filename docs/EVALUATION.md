# Ewaluacja głosu

Ewaluacja `pl_PL-mateusz-medium` powinna rozdzielać zrozumiałość, podobieństwo mówcy, jakość percepcyjną i wydajność. Wyniki należy zapisywać wraz z identyfikatorem modelu, SHA-256 artefaktów oraz środowiskiem wykonawczym.

## Zamrożony zbiór testowy

Do porównań między kolejnymi wersjami należy używać wyłącznie wersjonowanego podziału testowego wygenerowanego przez:

```bash
python scripts/create_splits.py --output dataset/splits.json
```

Plik zawiera ziarno losowania oraz SHA-256 `metadata.csv`. Jeżeli metadane się zmienią, podział należy świadomie wygenerować ponownie i odnotować zmianę w eksperymencie.

Dodatkowy zestaw `tests/polish_sentences.txt` służy do regresji polskiej normalizacji, fonemizacji i syntezy dla konstrukcji trudnych językowo.

## WER i CER

Po syntezie zamrożonych zdań należy wykonać transkrypcję niezależnym systemem ASR. Dane wejściowe mają format JSONL:

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

Do porównania podobieństwa należy użyć stałego modelu osadzeń mówcy i raportować średnie podobieństwo cosinusowe syntetycznych wypowiedzi do referencyjnych nagrań mówcy. W dokumentacji wyniku trzeba podać dokładną nazwę i wersję modelu osadzeń oraz sposób agregacji.

## MOS i CMOS

Dla oceny percepcyjnej zalecany jest ślepy odsłuch ze stałym zestawem zdań. Należy raportować co najmniej liczbę oceniających, skalę, procedurę randomizacji, średnią, odchylenie standardowe i przedział ufności. CMOS jest właściwy do bezpośredniego porównania dwóch wersji modelu.

## Wydajność

Każde wydanie powinno być mierzone przynajmniej na:

- CPU x86-64,
- Raspberry Pi 5,
- opcjonalnie GPU używanym podczas rozwoju.

Raportowane wartości:

- współczynnik czasu rzeczywistego (RTF),
- czas do uzyskania pierwszego fragmentu dźwięku, jeśli używane jest przesyłanie strumieniowe,
- całkowity czas syntezy,
- szczytowe użycie pamięci RAM,
- obciążenie CPU,
- rozmiar modelu ONNX.

Dla RTF należy używać definicji:

`RTF = czas obliczeń / czas wygenerowanego dźwięku`

Wartość poniżej 1 oznacza syntezę szybszą niż czas rzeczywisty.

## Test poprawności ONNX

Po każdym eksporcie należy uruchomić:

```bash
python scripts/smoke_test_voice.py \
  --model output/pl_PL-mateusz-medium.onnx
```

Test sprawdza obecność pary ONNX/JSON, poprawność konfiguracji, możliwość wykonania Pipera oraz powstanie niepustego pliku WAV o zgodnej częstotliwości próbkowania.

## Minimalny rekord eksperymentu

Wynik opublikowanego eksperymentu powinien zawierać:

- wersję lub identyfikator zatwierdzenia Piper,
- bazowy punkt kontrolny i jego SHA-256,
- ziarno losowania,
- parametry treningu,
- wersje Python, PyTorch, Lightning, CUDA i eSpeak NG,
- SHA-256 metadanych zbioru danych oraz pliku podziału,
- WER i CER,
- podobieństwo głosu,
- MOS/CMOS, jeśli przeprowadzono badanie,
- pomiary wydajności sprzętowej,
- SHA-256 finalnego ONNX i JSON.
