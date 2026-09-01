# Karta modelu `pl_PL-mateusz-medium`

Karta modelu (model card) dokumentuje pochodzenie, konfigurację, jakość, ograniczenia i warunki użycia konkretnego wydania modelu. Nie jest materiałem promocyjnym. Powinna umożliwiać ocenę, co rzeczywiście zmierzono i jak odtworzyć wynik.

Pola `TODO` należy uzupełniać wyłącznie na podstawie rzeczywistych pomiarów lub jednoznacznie zidentyfikowanych artefaktów.

## Informacje podstawowe

- nazwa: `pl_PL-mateusz-medium`,
- język: polski (`pl_PL`),
- architektura: Piper / VITS,
- wariant jakości: `medium`,
- liczba mówców: 1,
- częstotliwość próbkowania (sample rate): 22 050 Hz,
- format dystrybucyjny: ONNX + JSON,
- stan: w trakcie trenowania i oceny.

## Przeznaczenie

Model jest przeznaczony do syntezy polskiej mowy jednym, konkretnym głosem. Docelowe zastosowania obejmują lokalną syntezę TTS, usługi automatyzacji oraz integrację z cyfrowym awatarem.

Model nie powinien być uznawany za gotowy do wydania wyłącznie dlatego, że generuje zrozumiałą mowę. Kryteria gotowości opisano w `docs/MODEL.md`.

## Zbiór danych

Kanoniczny opis danych znajduje się w `dataset/DATASET_CARD.md`.

- liczba wypowiedzi: TODO,
- łączny czas nagrań: TODO,
- wersja zbioru danych: TODO,
- identyfikator zatwierdzenia danych: TODO,
- zbiór treningowy: TODO,
- zbiór walidacyjny: TODO,
- zbiór testowy: TODO.

Zbiór testowy musi pozostać oddzielony od procesu trenowania i wyboru modelu.

## Trenowanie

### Powtarzalność

Dla eksperymentu, z którego pochodzi publikowany model, należy podać:

- identyfikator zatwierdzenia Git kodu: TODO,
- konfigurację: `configs/pl_PL-mateusz-medium.json`,
- bazowy punkt kontrolny: TODO,
- SHA-256 bazowego punktu kontrolnego: TODO,
- wynikowy punkt kontrolny: TODO,
- ziarno losowania (seed): TODO,
- rozmiar partii (batch size): TODO,
- liczba epok (epochs): TODO,
- liczba kroków optymalizacji: TODO,
- czas trenowania: TODO.

### Środowisko

- system operacyjny: TODO,
- Python: TODO,
- PyTorch: TODO,
- PyTorch Lightning: TODO,
- CUDA: TODO,
- GPU: TODO,
- pamięć GPU: TODO.

Podanie samego modelu karty graficznej bez wersji środowiska programowego nie wystarcza do pełnego opisania eksperymentu.

## Ocena jakości

### Zrozumiałość

Współczynnik błędów słów (Word Error Rate, WER) mierzy udział błędów rozpoznania na poziomie słów. Współczynnik błędów znaków (Character Error Rate, CER) wykonuje analogiczne porównanie na poziomie znaków. Niższa wartość obu metryk oznacza mniejszą liczbę błędów względem tekstu referencyjnego.

- WER: TODO,
- CER: TODO,
- użyty system automatycznego rozpoznawania mowy: TODO,
- wersja systemu rozpoznawania: TODO,
- liczba wypowiedzi testowych: TODO.

### Jakość percepcyjna

Średnia ocena opinii słuchaczy (Mean Opinion Score, MOS) opisuje subiektywną ocenę próbek przez uczestników badania. Wynik bez informacji o skali, liczbie osób i procedurze nie powinien być interpretowany jako pełna metryka jakości.

- MOS: TODO,
- zastosowana skala: TODO,
- liczba oceniających: TODO,
- liczba próbek na osobę: TODO,
- procedura prezentacji: TODO.

Jeżeli użyto porównawczej średniej oceny opinii słuchaczy (Comparative Mean Opinion Score, CMOS):

- model referencyjny: TODO,
- CMOS: TODO.

### Podobieństwo głosu

- automatyczna miara podobieństwa głosu mówcy (speaker similarity): TODO,
- model tworzący reprezentację wektorową mówcy (speaker embedding): TODO,
- wersja modelu oceniającego: TODO,
- procedura porównania: TODO,
- ocena odsłuchowa podobieństwa: TODO.

Automatyczne podobieństwo reprezentacji wektorowych nie jest równoważne pełnej percepcyjnej ocenie tożsamości głosu.

## Wydajność

Współczynnik czasu rzeczywistego (Real-Time Factor, RTF) jest ilorazem czasu obliczeń i czasu trwania wygenerowanego dźwięku. `RTF < 1` oznacza syntezę szybszą niż czas rzeczywisty.

Pomiary należy raportować oddzielnie dla konkretnych platform.

### CPU x86-64

- procesor: TODO,
- RTF: TODO,
- opóźnienie pierwszego fragmentu: TODO,
- maksymalne użycie pamięci RAM: TODO.

### Raspberry Pi 5

- system operacyjny: TODO,
- RTF: TODO,
- opóźnienie pierwszego fragmentu: TODO,
- maksymalne użycie pamięci RAM: TODO.

### GPU, opcjonalnie

- GPU: TODO,
- środowisko ONNX Runtime / CUDA: TODO,
- RTF: TODO,
- opóźnienie pierwszego fragmentu: TODO.

### Artefakt

- rozmiar `pl_PL-mateusz-medium.onnx`: TODO,
- SHA-256 ONNX: TODO,
- SHA-256 JSON: TODO.

## Testy regresyjne języka polskiego

Przed wydaniem model powinien zostać sprawdzony na stałym korpusie obejmującym między innymi:

- `ą`, `ć`, `ę`, `ł`, `ń`, `ó`, `ś`, `ź`, `ż`,
- liczby całkowite i dziesiętne,
- daty i godziny,
- liczebniki porządkowe,
- skróty i tytuły naukowe,
- jednostki SI,
- nazwy własne,
- adresy URL i adresy poczty elektronicznej,
- zdania krótkie i długie,
- interpunkcję wpływającą na rytm i intonację.

Wyniki regresji: TODO.

## Integracja z animacją twarzy

Model może zostać wykorzystany w systemie awatara razem z dopasowaniami fonemów do dźwięku (phoneme alignments). Dane czasowe nie stanowią jednak gotowego systemu synchronizacji ust.

Docelowy proces obejmuje:

```text
tekst → TTS → fonemy i czas → wizemy → koartykulacja → animacja twarzy
```

Szczegóły znajdują się w `docs/ALIGNMENTS.md`.

## Znane ograniczenia

Na obecnym etapie należy zakładać możliwość występowania błędów w szczególności dla:

- nieznanych nazw własnych,
- zapożyczeń,
- skrótów,
- tekstu wielojęzycznego,
- nietypowej interpunkcji,
- ciągów znaków przeznaczonych przede wszystkim do odczytu maszynowego.

Lista powinna zostać zaktualizowana na podstawie rzeczywistych wyników testów, a nie wyłącznie przewidywań.

## Artefakty wydania

Każde publiczne wydanie powinno zawierać co najmniej:

```text
pl_PL-mateusz-medium.onnx
pl_PL-mateusz-medium.onnx.json
MODEL_CARD.md
checksums.txt
samples/
```

Próbki powinny być reprezentatywne. Nie należy wybierać wyłącznie zdań, dla których model osiąga wyjątkowo dobry rezultat.

## Licencja i prawa

Licencja modelu: TODO.

Licencję modelu należy ustalić niezależnie od licencji kodu Piper. Musi ona być zgodna z prawami do zbioru danych oraz prawem do wykorzystania i publikacji głosu wykorzystanego do trenowania.
