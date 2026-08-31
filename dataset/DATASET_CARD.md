# Dataset Card: pl_PL-mateusz

## Przeznaczenie

Dataset służy do trenowania i dostrajania jednego polskiego głosu dla Piper TTS. Metadane znajdują się w `metadata.csv`, a nagrania w `wavs/`.

## Stan

Dataset jest w trakcie przygotowania i walidacji. Poniższe pola oznaczone `TODO` należy uzupełnić wyłącznie na podstawie faktycznych pomiarów i udokumentowanego procesu przygotowania danych.

## Dane podstawowe

- język: `pl_PL`
- liczba mówców: 1
- mówca: Mateusz
- docelowa częstotliwość próbkowania: 22050 Hz
- docelowy format: mono WAV
- liczba wypowiedzi: TODO
- łączny czas: TODO
- mediana długości segmentu: TODO

## Pochodzenie nagrań

- źródła nagrań: TODO
- sprzęt rejestrujący: TODO
- środowisko akustyczne: TODO
- pierwotna częstotliwość próbkowania: TODO
- sposób uzyskania transkrypcji: TODO

## Przygotowanie danych

Udokumentuj:

1. ekstrakcję i konwersję audio,
2. segmentację wypowiedzi,
3. normalizację poziomu sygnału,
4. redukcję lub brak redukcji szumu,
5. sposób usuwania ciszy,
6. korektę transkrypcji,
7. metodę wykrywania i usuwania błędnych segmentów.

Podstawową kontrolę techniczną wykonuje:

```bash
python scripts/validate_dataset.py --metadata dataset/metadata.csv --audio-dir dataset/wavs
```

## Kontrola jakości

Przed treningiem należy raportować co najmniej:

- brakujące i nadmiarowe pliki względem `metadata.csv`,
- duplikaty,
- puste transkrypcje,
- rozkład długości segmentów,
- liczbę plików o niezgodnym sample rate,
- liczbę plików stereo,
- clipping i poziomy RMS/peak,
- udział ciszy,
- pokrycie znaków i fonemów języka polskiego.

Ostatnie cztery pozycje wymagają rozszerzenia obecnego walidatora o analizę sygnałową i fonemizację.

## Podział danych

Docelowo należy utworzyć trwały, wersjonowany podział `train/validation/test`, aby kolejne wersje modelu były porównywane na tym samym zbiorze testowym.

- train: TODO
- validation: TODO
- test: TODO
- seed podziału: TODO

## Prywatność i prawa do głosu

Nagrania przedstawiają głos jednej osoby. Przed publicznym udostępnieniem datasetu należy jednoznacznie udokumentować zgodę właściciela głosu na publikację i zakres dozwolonego wykorzystania nagrań.

## Licencja

TODO. Licencja datasetu musi zostać określona niezależnie od GPL-3.0-or-later obejmującej kod Piper.
