# Częstotliwość próbkowania

## Definicja

Częstotliwość próbkowania (sample rate) określa liczbę próbek sygnału dźwiękowego rejestrowanych lub odtwarzanych w ciągu sekundy.

## Znaczenie w `piper-mat`

W `piper-mat` jest cechą zbioru nagrań, konfiguracji modelu głosu i wygenerowanych plików WAV. Musi być zgodna na wszystkich tych etapach, ponieważ model uczony dla jednej wartości nie powinien otrzymywać danych opisanych inną wartością.

## Użycie w procesie

Przed trenowaniem skrypt walidacyjny sprawdza pliki w `dataset/wavs`. Podczas trenowania wartość przekazuje `model.sample_rate`, a po eksporcie jest zapisana w konfiguracji `.onnx.json`. Test modelu porównuje ją z nagłówkiem wygenerowanego WAV.

## Parametry, jednostki i formaty

Jednostką jest herc, Hz, czyli próbka na sekundę. Konfiguracja projektu używa `22050`, co zapisuje się jako 22 050 Hz. Zmiana liczby w nagłówku bez przeliczenia próbek nie zmienia rzeczywistej charakterystyki nagrania.

## Praktyczne wartości i ich skutki

| Wartość | Co oznacza w praktyce |
| --- | --- |
| 16 000 Hz | Pasmo wystarczające głównie dla mowy; nie odpowiada konfiguracji docelowego modelu. |
| 22 050 Hz | Wartość używana przez `pl_PL-mateusz-medium`; jedna sekunda zawiera 22 050 próbek na kanał. |
| 44 100 Hz | Dwa razy więcej próbek na sekundę niż przy 22 050 Hz, więc pliki i obliczenia mogą być większe; sama zmiana nie poprawi wytrenowanego modelu. |

Dla nagrania trwającego 10 sekund wartości te oznaczają odpowiednio 160 000, 220 500 albo 441 000 próbek na kanał.

## Przykład z repozytorium

```bash
python -m piper.train fit \
  --model.sample_rate 22050 \
  --data.csv_path dataset/metadata.csv \
  --data.audio_dir dataset/wavs
```

## Typowe błędy interpretacyjne

- Utożsamianie częstotliwości próbkowania z głębią bitową lub przepływnością.
- Zmiana `model.sample_rate` w trakcie eksperymentu bez ponownego przygotowania danych.
- Założenie, że wyższa wartość zawsze oznacza lepszy model.

## Powiązane artykuły i procedury

- [Zbiór danych](zbior-danych.md)
- [Model głosu](model-glosu.md)
- [Przygotowanie zbioru](../DATASET.md)
- [Trenowanie](../TRAINING.md)
