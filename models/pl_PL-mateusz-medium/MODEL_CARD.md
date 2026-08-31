# Model Card: pl_PL-mateusz-medium

## Model

- nazwa: `pl_PL-mateusz-medium`
- język: polski (`pl_PL`)
- architektura: Piper / VITS
- jakość: medium
- liczba mówców: 1
- sample rate: 22050 Hz
- format dystrybucyjny: ONNX + JSON

## Status

Model jest w trakcie treningu. Pola `TODO` należy uzupełnić po zakończeniu konkretnego, identyfikowalnego eksperymentu. Nie należy wpisywać przewidywanych parametrów jako wyników pomiarów.

## Dane treningowe

Źródło: `dataset/DATASET_CARD.md`.

- liczba wypowiedzi: TODO
- czas nagrań: TODO
- wersja datasetu / commit: TODO
- podział train/validation/test: TODO

## Trening

- wersja/commit Piper: TODO
- checkpoint bazowy: TODO
- checksum checkpointu bazowego: TODO
- seed: TODO
- batch size: TODO
- liczba epok / kroków: TODO
- GPU: TODO
- system operacyjny: TODO
- Python: TODO
- PyTorch: TODO
- CUDA: TODO
- czas treningu: TODO

Referencyjne parametry projektu znajdują się w `configs/pl_PL-mateusz-medium.json`.

## Ewaluacja

### Zrozumiałość

- WER: TODO
- CER: TODO

### Jakość i podobieństwo głosu

- MOS lub inna ocena odsłuchowa: TODO
- liczba oceniających: TODO
- speaker similarity: TODO
- użyty model embeddingowy: TODO

### Wydajność

Raportować co najmniej dla CPU x86-64 oraz Raspberry Pi 5, a opcjonalnie dla GPU:

- real-time factor (RTF): TODO
- opóźnienie pierwszego audio: TODO
- peak RAM: TODO
- użycie CPU: TODO
- rozmiar modelu ONNX: TODO

## Testy regresyjne języka polskiego

Przed wydaniem model powinien przejść testy obejmujące:

- `ą ć ę ł ń ó ś ź ż`,
- liczby całkowite i dziesiętne,
- daty i godziny,
- liczebniki porządkowe,
- skróty i tytuły naukowe,
- jednostki SI,
- nazwy własne,
- URL i adresy e-mail,
- krótkie oraz długie wypowiedzi.

## Artefakty wydania

Każde publiczne wydanie powinno zawierać:

```text
pl_PL-mateusz-medium.onnx
pl_PL-mateusz-medium.onnx.json
MODEL_CARD.md
checksums.txt
samples/
```

## Ograniczenia

Model reprezentuje pojedynczy polski głos i może popełniać błędy fonetyczne dla nieznanych nazw własnych, zapożyczeń, skrótów oraz tekstu wielojęzycznego. Zakres ograniczeń należy rozszerzyć po ewaluacji regresyjnej.

## Licencja

TODO. Licencja modelu musi zostać ustalona i opisana niezależnie od licencji kodu Piper oraz zgodnie z prawami do datasetu i głosu.
