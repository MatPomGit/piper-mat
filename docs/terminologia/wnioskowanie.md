# Wnioskowanie

## Definicja

Wnioskowanie (inference) jest wykonywaniem wytrenowanego modelu w celu wygenerowania wyniku, w tym przypadku dźwięku mowy.

## Znaczenie w `piper-mat`

W `piper-mat` obejmuje fonemizację tekstu i syntezę przez model `pl_PL-mateusz-medium`. Nie aktualizuje parametrów modelu i jest główną operacją podczas wdrożenia.

## Użycie w procesie

Po eksporcie model uruchamia się przez interfejs CLI, Python, HTTP albo usługę Wyoming Piper. Wydajność mierzy się na określonym sprzęcie i reprezentatywnym tekście.

## Parametry, jednostki i formaty

Wejście jest tekstem, a wyjście próbkami dźwięku, zwykle zapisanymi jako WAV. Istotne są częstotliwość próbkowania, parametry syntezy, czas obliczeń, opóźnienie i RTF.

## Praktyczne wartości i ich skutki

| Przykład | Co można zaobserwować |
| --- | --- |
| Zdanie dające 2 s dźwięku | Przy RTF `0,5` samo obliczenie trwa około 1 s. |
| Zdanie dające 10 s dźwięku | Przy RTF `0,2` samo obliczenie trwa około 2 s. |
| `length_scale=1.2` | Jeśli interfejs i model używają tego parametru, mowa jest zwykle wolniejsza niż przy `1.0`; parametr pozostaje opisany przy interfejsie. |

Całkowity czas odpowiedzi może być dłuższy od czasu modelu, ponieważ obejmuje również wczytanie plików, fonemizację, buforowanie i zapis WAV.

## Przykład z repozytorium

```bash
piper \
  --model output/pl_PL-mateusz-medium.onnx \
  --output-file test.wav \
  -- "To jest test polskiego głosu."
```

## Typowe błędy interpretacyjne

- Utożsamianie wnioskowania z trenowaniem albo oceną jakości.
- Pomiar czasu obejmujący inne etapy bez opisania zakresu.
- Łączenie modelu `.onnx` z konfiguracją `.onnx.json` z innego wydania.

## Powiązane artykuły i procedury

- [ONNX](onnx.md)
- [Współczynnik czasu rzeczywistego](wspolczynnik-czasu-rzeczywistego.md)
- [Wdrożenie](../DEPLOYMENT.md)
- [Interfejs CLI](../CLI.md)
