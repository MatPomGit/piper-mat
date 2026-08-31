# Ewaluacja głosu

Ewaluacja `pl_PL-mateusz-medium` powinna rozdzielać zrozumiałość, podobieństwo mówcy, jakość percepcyjną i wydajność. Wyniki należy zapisywać wraz z identyfikatorem modelu, SHA-256 artefaktów oraz środowiskiem wykonawczym.

## Zamrożony zbiór testowy

Do porównań między kolejnymi wersjami należy używać wyłącznie wersjonowanego splitu testowego wygenerowanego przez:

```bash
python scripts/create_splits.py --output dataset/splits.json
```

Plik zawiera seed oraz SHA-256 `metadata.csv`. Jeżeli zmieni się metadata, split należy świadomie wygenerować ponownie i odnotować zmianę w eksperymencie.

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

Należy zapisać nazwę i wersję modelu ASR. WER/CER nie są samodzielną miarą naturalności głosu.

## Speaker similarity

Do porównania podobieństwa należy użyć stałego modelu speaker-embedding i raportować średnią cosinusową zgodność syntetycznych wypowiedzi z referencyjnymi nagraniami mówcy. W dokumentacji wyniku trzeba podać dokładną nazwę i wersję modelu embeddingowego oraz sposób agregacji.

## MOS i CMOS

Dla oceny percepcyjnej zalecany jest ślepy odsłuch ze stałym zestawem zdań. Należy raportować co najmniej liczbę oceniających, skalę, procedurę randomizacji, średnią, odchylenie standardowe i przedział ufności. CMOS jest właściwy do bezpośredniego porównania dwóch wersji modelu.

## Wydajność

Każde wydanie powinno być mierzone przynajmniej na:

- CPU x86-64,
- Raspberry Pi 5,
- opcjonalnie GPU używanym podczas rozwoju.

Raportowane wartości:

- real-time factor (RTF),
- czas do uzyskania pierwszego audio, jeśli używany jest streaming,
- całkowity czas syntezy,
- peak RAM,
- obciążenie CPU,
- rozmiar modelu ONNX.

Dla RTF należy używać definicji:

`RTF = czas obliczeń / czas wygenerowanego audio`

Wartość poniżej 1 oznacza syntezę szybszą niż czas rzeczywisty.

## Smoke test ONNX

Po każdym eksporcie należy uruchomić:

```bash
python scripts/smoke_test_voice.py \
  --model output/pl_PL-mateusz-medium.onnx
```

Test sprawdza obecność pary ONNX/JSON, poprawność konfiguracji, możliwość wykonania Pipera oraz powstanie niepustego WAV o zgodnym sample rate.

## Minimalny rekord eksperymentu

Wynik opublikowanego eksperymentu powinien zawierać:

- wersję/commit Piper,
- checkpoint bazowy i jego SHA-256,
- seed,
- parametry treningu,
- wersje Python, PyTorch, Lightning, CUDA i eSpeak NG,
- SHA-256 dataset metadata oraz pliku splitów,
- WER i CER,
- speaker similarity,
- MOS/CMOS, jeśli przeprowadzono badanie,
- benchmarki sprzętowe,
- SHA-256 finalnego ONNX i JSON.
