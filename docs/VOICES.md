# Głosy i modele Piper

Głos Piper jest zestawem artefaktów pozwalających wykonywać syntezę mowy dla określonego języka, wariantu językowego i jednego lub wielu mówców. W `piper-mat` głównym artefaktem jest rozwijany [model głosu (voice model)](terminologia/model-glosu.md) `pl_PL-mateusz-medium`.

Ten dokument wyjaśnia sposób identyfikowania głosów i relację pomiędzy modelem projektu a publicznymi modelami Piper. Nie utrzymujemy tutaj ręcznej kopii pełnej listy wszystkich publicznie dostępnych głosów, ponieważ taka lista szybko się dezaktualizuje.

## Model projektu

Docelowy głos:

```text
pl_PL-mateusz-medium
```

Identyfikator składa się z trzech logicznych części:

```text
pl_PL | mateusz | medium
```

`pl_PL` określa język polski i wariant regionalny Polska. `mateusz` identyfikuje głos w obrębie projektu. `medium` oznacza wariant modelu zgodny z konwencją Piper.

Identyfikator modelu nie jest nazwą zmiennej Pythona. Nie należy zmieniać go na `pl_PL_mateusz_medium` tylko po to, aby przypominał `snake_case`.

## Wymagane pliki

Do uruchomienia głosu potrzebne są co najmniej:

```text
pl_PL-mateusz-medium.onnx
pl_PL-mateusz-medium.onnx.json
```

Plik `.onnx` przechowuje model wykonawczy. Plik `.onnx.json` zawiera konfigurację potrzebną do jego poprawnej interpretacji przez Pipera.

Oba pliki należy traktować jako nierozłączną parę wersjonowaną razem.

## Publiczne głosy Piper

Publiczne modele Piper są użyteczne jako:

- punkt odniesienia jakościowego,
- materiał do testowania zgodności oprogramowania,
- źródło bazowych punktów kontrolnych, jeżeli ich pochodzenie i zgodność zostały zweryfikowane,
- porównanie wydajności,
- przykład struktury konfiguracji.

Nie należy jednak zakładać, że każdy publiczny głos może być użyty jako baza do trenowania `pl_PL-mateusz-medium` bez sprawdzenia architektury, konfiguracji, licencji i zgodności technicznej.

## Język i wariant regionalny

Identyfikatory takie jak `pl_PL`, `en_US` i `en_GB` kodują język oraz wariant regionalny. W projekcie należy konsekwentnie używać `pl_PL` dla polskiego głosu docelowego.

Zmiana kodu języka nie jest kosmetyczną zmianą nazwy. Może wpływać na wybór fonemizatora, konfigurację głosu, normalizację tekstu i zgodność z narzędziami integracyjnymi.

## Wariant jakości

Nazwy takie jak `low`, `medium` i `high` są elementem konwencji dystrybucji modeli Piper. Nie należy interpretować ich jako bezpośredniej, uniwersalnej skali jakości percepcyjnej.

Wariant może wiązać się z różnicami architektury, rozmiarem modelu, częstotliwością próbkowania albo wymaganiami obliczeniowymi zależnie od konkretnej rodziny modeli.

Dlatego porównanie dwóch głosów powinno opierać się na rzeczywistych parametrach i pomiarach, a nie wyłącznie na etykiecie wariantu.

## Model jednomówcowy i wielomówcowy

Model jednomówcowy (single-speaker model) reprezentuje jeden głos. `pl_PL-mateusz-medium` jest projektowany jako model jednomówcowy.

Model wielomówcowy (multi-speaker model) może przechowywać wiele głosów w jednym modelu i wymaga wskazania mówcy podczas syntezy.

Nie ma potrzeby zwiększania złożoności `piper-mat` przez przejście na model wielomówcowy, jeżeli celem pozostaje wierne odwzorowanie jednego głosu.

## VITS

Piper wykorzystuje architekturę opartą na VITS. VITS jest generatywną architekturą syntezy mowy łączącą modelowanie reprezentacji tekstowej, czasu trwania i generowania sygnału mowy w jednym procesie trenowania.

W dokumentacji użytkowej nie należy sprowadzać jakości modelu do samej nazwy architektury. Wynik zależy również od danych, fonemizacji, konfiguracji, procesu trenowania i wyboru punktu kontrolnego.

## ONNX i środowisko wykonawcze

[ONNX (Open Neural Network Exchange)](terminologia/onnx.md) jest formatem reprezentacji modelu. ONNX Runtime jest środowiskiem wykonawczym służącym do wykonywania modelu ONNX.

Nie należy używać nazw `ONNX` i `ONNX Runtime` zamiennie:

- `ONNX` opisuje format modelu,
- `ONNX Runtime` opisuje oprogramowanie wykonujące model.

To rozróżnienie jest istotne w raportach wydajności i dokumentacji wdrożenia.

## Licencje

Licencję każdego modelu należy sprawdzać niezależnie. Licencja kodu Piper nie nadaje automatycznie takich samych praw do wszystkich modeli głosów, punktów kontrolnych ani zbiorów danych.

Dla `pl_PL-mateusz-medium` należy osobno ustalić:

- prawa do nagrań źródłowych,
- warunki wykorzystania głosu,
- licencję zbioru danych,
- licencję finalnego modelu,
- warunki publikacji próbek.

Karta modelu jest kanonicznym miejscem dokumentowania tych informacji dla konkretnego wydania.

## Wybór modelu do porównań

Jeżeli `pl_PL-mateusz-medium` jest porównywany z innym głosem, należy zapisać:

- pełny identyfikator modelu referencyjnego,
- wersję lub rewizję źródła,
- SHA-256 pobranego artefaktu, jeżeli jest używany w eksperymencie,
- częstotliwość próbkowania,
- platformę wykonawczą,
- parametry syntezy,
- licencję.

Dzięki temu wynik porównania można później odtworzyć.

## Powiązane dokumenty

Szczegółowy opis `pl_PL-mateusz-medium` znajduje się w `models/pl_PL-mateusz-medium/MODEL_CARD.md`. Kryteria gotowości modelu opisano w [MODEL.md](MODEL.md), a proces wydawania w [RELEASES.md](RELEASES.md).
