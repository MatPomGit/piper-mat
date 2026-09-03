# MOS i CMOS

## Definicja

Średnia ocena opinii słuchaczy (Mean Opinion Score, MOS) opisuje bezwzględne oceny próbek, a porównawcza średnia ocena opinii słuchaczy (Comparative Mean Opinion Score, CMOS) opisuje preferencję względem próbki odniesienia.

## Znaczenie w `piper-mat`

W `piper-mat` metryki te służą do percepcyjnej oceny naturalności, stabilności lub różnicy między kandydatami. Uzupełniają pomiary automatyczne WER, CER i RTF.

## Użycie w procesie

Badanie wymaga losowej kolejności próbek, spójnej instrukcji, tej samej skali oraz zapisania liczby słuchaczy. CMOS przedstawia pary A i B, natomiast MOS prosi o ocenę pojedynczej próbki.

## Parametry, jednostki i formaty

MOS często używa pięciostopniowej skali, ale raport musi podać rzeczywiście zastosowaną skalę i znaczenie punktów. Dla CMOS trzeba określić kierunek znaku, średnią, rozrzut i liczebność ocen.

## Praktyczne wartości i ich skutki

| Wartość | Przykładowa interpretacja |
| --- | --- |
| MOS 1 w skali 1 do 5 | Najniższa ocena zdefiniowana w instrukcji badania. |
| MOS 3 w skali 1 do 5 | Środek skali, nie automatycznie „wystarczająca jakość”. |
| MOS 5 w skali 1 do 5 | Najwyższa ocena w tej skali. |
| CMOS `+1,0` | Wariant wskazany jako dodatni oceniono średnio lepiej o jeden punkt, jeśli tak zdefiniowano kierunek skali. |

Średnia MOS `4,2` z 5 ocen jest znacznie mniej stabilna niż `4,2` ze 100 ocen. Raport powinien podawać liczbę słuchaczy, liczbę próbek i miarę rozrzutu.

## Przykład z repozytorium

```text
korpus: tests/polish_sentences.txt
model A: output/pl_PL-mateusz-medium.onnx
model B: wydanie referencyjne
```

## Typowe błędy interpretacyjne

- Nazywanie wartości przewidywanej przez model pomocniczy wynikiem badania słuchaczy.
- Porównywanie średnich uzyskanych z innych skal lub instrukcji.
- Raportowanie samej średniej bez liczby ocen i opisu procedury.

## Powiązane artykuły i procedury

- [WER i CER](wer-i-cer.md)
- [Współczynnik czasu rzeczywistego](wspolczynnik-czasu-rzeczywistego.md)
- [Procedura oceny](../EVALUATION.md)
- [Model głosu](../MODEL.md)
