# Model głosu

Model głosu (voice model) jest wytrenowanym modelem syntezy mowy wraz z konfiguracją potrzebną do poprawnego wnioskowania (inference). W `piper-mat` docelowym modelem jest `pl_PL-mateusz-medium`.

Kanoniczna karta modelu znajduje się w `models/pl_PL-mateusz-medium/MODEL_CARD.md`. Ten rozdział opisuje natomiast kryteria techniczne, które muszą zostać spełnione przed uznaniem modelu za gotowy do wydania.

Terminologię metryk i procesu opisano w [słowniku](TERMINOLOGIA.md).

## Artefakty modelu

Podstawowy komplet składa się z:

```text
pl_PL-mateusz-medium.onnx
pl_PL-mateusz-medium.onnx.json
```

ONNX przechowuje graf obliczeniowy i parametry modelu. Plik JSON zawiera konfigurację wymaganą przez Pipera, między innymi informacje potrzebne do poprawnej interpretacji wejścia i wyjścia modelu.

Pliki te należy traktować jako jedną wersjonowaną całość. Nie wolno mieszać modelu ONNX z konfiguracją pochodzącą z innego eksperymentu lub wydania.

## Kryteria gotowości

Model może zostać oznaczony jako kandydat do wydania dopiero wtedy, gdy spełnia wszystkie wymagane kryteria.

### 1. Poprawność techniczna

Model powinien:

- poprawnie wczytywać się w obsługiwanej wersji Pipera,
- generować poprawny plik dźwiękowy,
- przechodzić podstawowy test poprawności (smoke test),
- posiadać zgodną konfigurację JSON,
- nie generować wartości nienumerycznych ani oczywiście uszkodzonego sygnału dla korpusu regresyjnego.

Podstawowy test poprawności potwierdza jedynie, że najważniejsza ścieżka działania funkcjonuje. Nie jest testem jakości głosu.

### 2. Zrozumiałość

Należy wyznaczyć co najmniej:

- współczynnik błędów słów (Word Error Rate, WER),
- współczynnik błędów znaków (Character Error Rate, CER).

Metryki należy obliczać na zamrożonym zbiorze testowym, który nie był wykorzystywany do trenowania ani doboru punktu kontrolnego.

### 3. Jakość percepcyjna

Automatyczne metryki nie zastępują odsłuchu. Model powinien przejść co najmniej podstawową ocenę odsłuchową, np. z wykorzystaniem średniej oceny opinii słuchaczy (Mean Opinion Score, MOS) albo porównawczej średniej oceny opinii słuchaczy (Comparative Mean Opinion Score, CMOS).

Należy zachować teksty testowe, sposób prezentacji próbek, skalę ocen i liczbę oceniających.

### 4. Podobieństwo głosu

Dla modelu odtwarzającego głos konkretnej osoby należy ocenić podobieństwo głosu mówcy (speaker similarity). Automatyczna miara oparta na reprezentacji wektorowej mówcy (speaker embedding) powinna być uzupełniona oceną odsłuchową, jeśli model ma być publikowany jako cyfrowe odwzorowanie konkretnego głosu.

### 5. Wydajność

Należy zmierzyć co najmniej:

- współczynnik czasu rzeczywistego (Real-Time Factor, RTF),
- opóźnienie do uzyskania pierwszego fragmentu dźwięku,
- całkowity czas syntezy,
- maksymalne użycie pamięci RAM,
- rozmiar modelu ONNX.

RTF porównuje czas obliczeń z długością wygenerowanego dźwięku. Przykładowo `RTF = 0,25` oznacza, że wygenerowanie 4 sekund mowy zajmuje około 1 sekundy. `RTF < 1` oznacza syntezę szybszą niż czas rzeczywisty.

Pomiary należy zawsze łączyć z opisem sprzętu, środowiska wykonawczego i parametrów syntezy.

### 6. Język polski

Korpus regresyjny powinien obejmować co najmniej:

- polskie znaki diakrytyczne,
- liczby całkowite i dziesiętne,
- daty i godziny,
- skróty,
- tytuły naukowe,
- jednostki SI,
- nazwy własne,
- adresy URL i adresy poczty elektronicznej,
- krótkie i długie zdania,
- znaki interpunkcyjne wpływające na prozodię.

Wynik pozytywny nie oznacza, że wszystkie te przypadki muszą brzmieć idealnie. Znane ograniczenia muszą jednak zostać udokumentowane i nie mogą być ukrywane przez dobór wyłącznie łatwych przykładów.

## Identyfikowalność eksperymentu

Każdy model kandydujący do wydania musi dać się powiązać z konkretnym eksperymentem. Należy zapisać co najmniej:

- wersję kodu lub identyfikator zatwierdzenia Git,
- wersję zbioru danych,
- podział danych,
- bazowy punkt kontrolny i jego SHA-256,
- konfigurację trenowania,
- ziarno losowania (seed),
- wybrany wynikowy punkt kontrolny,
- środowisko programowe i sprzętowe.

Bez tych informacji wynik może być interesujący odsłuchowo, ale nie jest wystarczająco powtarzalnym wynikiem eksperymentalnym.

## Integralność wydania

Każdy publikowany artefakt powinien mieć sumę kontrolną SHA-256. Paczka wydania powinna zawierać co najmniej model, konfigurację, kartę modelu, sumy kontrolne i reprezentatywne próbki.

Do momentu wykonania rzeczywistych pomiarów pola wynikowe w `MODEL_CARD.md` powinny pozostawać oznaczone jako `TODO`. Nie należy zastępować brakujących danych wartościami szacunkowymi.
