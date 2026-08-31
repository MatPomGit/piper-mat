# Karta modelu: pl_PL-mateusz-medium

## Model

- nazwa: `pl_PL-mateusz-medium`
- język: polski (`pl_PL`)
- architektura: Piper / VITS
- jakość: średnia
- liczba mówców: 1
- częstotliwość próbkowania: 22050 Hz
- format dystrybucyjny: ONNX + JSON

## Stan

Model jest w trakcie treningu. Pola `TODO` należy uzupełnić po zakończeniu konkretnego, identyfikowalnego eksperymentu. Nie należy wpisywać przewidywanych parametrów jako wyników pomiarów.

## Dane treningowe

Źródło: `dataset/DATASET_CARD.md`.

- liczba wypowiedzi: TODO
- czas nagrań: TODO
- wersja zbioru danych / identyfikator zatwierdzenia: TODO
- podział na zbiory treningowy, walidacyjny i testowy: TODO

## Trening

- wersja / identyfikator zatwierdzenia Piper: TODO
- bazowy punkt kontrolny: TODO
- suma kontrolna bazowego punktu kontrolnego: TODO
- ziarno losowania: TODO
- rozmiar partii: TODO
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
- podobieństwo głosu: TODO
- użyty model osadzeń mówcy: TODO

### Wydajność

Raportować co najmniej dla CPU x86-64 oraz Raspberry Pi 5, a opcjonalnie dla GPU:

- współczynnik czasu rzeczywistego (RTF): TODO
- opóźnienie uzyskania pierwszego fragmentu dźwięku: TODO
- szczytowe użycie pamięci RAM: TODO
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
- adresy URL i e-mail,
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

TODO. Licencja modelu musi zostać ustalona i opisana niezależnie od licencji kodu Piper oraz zgodnie z prawami do zbioru danych i głosu.
