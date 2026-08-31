# Karta zbioru danych: pl_PL-mateusz

## Przeznaczenie

Zbiór danych służy do trenowania i dostrajania jednego polskiego głosu dla Piper TTS. Metadane znajdują się w `metadata.csv`, a nagrania w `wavs/`.

## Stan

Zbiór danych jest w trakcie przygotowania i walidacji. Poniższe pola oznaczone `TODO` należy uzupełnić wyłącznie na podstawie faktycznych pomiarów i udokumentowanego procesu przygotowania danych.

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

Należy udokumentować:

1. ekstrakcję i konwersję dźwięku,
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
- liczbę plików o niezgodnej częstotliwości próbkowania,
- liczbę plików stereo,
- przesterowanie i poziomy RMS oraz wartości szczytowe,
- udział ciszy,
- pokrycie znaków i fonemów języka polskiego.

## Podział danych

Docelowo należy utworzyć trwały, wersjonowany podział na zbiory treningowy, walidacyjny i testowy, aby kolejne wersje modelu były porównywane na tym samym zbiorze testowym.

- zbiór treningowy: TODO
- zbiór walidacyjny: TODO
- zbiór testowy: TODO
- ziarno losowania podziału: TODO

## Prywatność i prawa do głosu

Nagrania przedstawiają głos jednej osoby. Przed publicznym udostępnieniem zbioru danych należy jednoznacznie udokumentować zgodę właściciela głosu na publikację i zakres dozwolonego wykorzystania nagrań.

## Licencja

TODO. Licencja zbioru danych musi zostać określona niezależnie od GPL-3.0-or-later obejmującej kod Piper.
