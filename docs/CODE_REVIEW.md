# Raport z przeglądu kodu

## Podsumowanie

Przegląd kodu (code review) wykonano 30 września 2026 roku dla rewizji
`4fe5b96`. Objął on kod w `src/piper`, narzędzia w `scripts` i `tools`, testy,
konfigurację pakietu, potok GitHub Actions oraz dokumentację związaną z
uruchamianiem i trenowaniem.

Ocena ogólna: projekt ma czytelną strukturę, liczne testy jednostkowe i dobre
kontrole integralności danych projektu, ale przed udostępnianiem serwera HTTP w
sieci należy usunąć dwa istotne problemy bezpieczeństwa. Należy też włączyć
pełny zestaw testów i kontroli jakości do GitHub Actions. W obecnym stanie sam
zielony wynik tego potoku nie potwierdza, że testy jednostkowe przechodzą ani że
kod spełnia ustawione reguły formatowania.

Zidentyfikowano:

- 1 problem o znaczeniu wysokim,
- 2 problemy o znaczeniu średnim,
- 2 problemy o znaczeniu niskim.

## Metoda i ograniczenia

W ramach przeglądu:

1. przeanalizowano kod źródłowy, testy, konfigurację pakietu i potok GitHub
   Actions;
2. wyszukano miejsca uruchamiające procesy, wczytujące punkty kontrolne,
   pobierające dane z sieci i przechwytujące szerokie klasy wyjątków;
3. uruchomiono kompilację plików Pythona i projektową kontrolę integralności;
4. podjęto próbę uruchomienia pełnych testów oraz kontroli jakości.

Pełnych testów nie udało się wykonać w dostarczonym środowisku. Projekt nie był
zainstalowany, a opcjonalna zależność `werkzeug` nie była dostępna. Po dodaniu
`src` do ścieżki importu zbieranie testów zatrzymało się wyłącznie na braku tej
zależności. Kontrola `black` uruchomiona przez `python script/lint` wykazała trzy
pliki wymagające formatowania i przerwała dalsze kontrole. Ograniczenia te nie
zmieniają opisanych niżej ustaleń, które wynikają bezpośrednio z przepływu
sterowania w kodzie.

## Ustalenia

### CR-01: pole `voice` pozwala wyjść poza skonfigurowane katalogi modeli

**Znaczenie: wysokie**

Punkt końcowy `/synthesize` pobiera `voice` bez ograniczenia jego składni, po
czym dla każdego katalogu tworzy ścieżkę przez
`Path(data_dir) / f"{model_id}.onnx"`. Wartość bezwzględna albo zawierająca
`..` może wskazać plik poza `data_dir`. Jeżeli plik istnieje, serwer przekazuje
go do `PiperVoice.load`, które odczytuje również sąsiednią konfigurację JSON i
tworzy sesję ONNX Runtime.

Skutek zależy od zawartości systemu plików. Niezaufany klient może co najmniej
sondować istnienie modeli poza dozwolonym katalogiem, wymuszać kosztowne
wczytywanie kolejnych modeli i trwale pozostawiać je w `loaded_voices`. Jeżeli
na hoście znajdują się inne modele ONNX z konfiguracjami, może też wymusić ich
uruchomienie. Problem jest szczególnie istotny, ponieważ serwer domyślnie
nasłuchuje na `0.0.0.0`.

**Zalecenie:** dopuścić jedynie identyfikator zgodny ze ściśle określonym
wzorcem, odrzucić ścieżki bezwzględne i separatory katalogów, a po rozwiązaniu
ścieżki sprawdzić przez `Path.resolve()` oraz `Path.is_relative_to()`, czy plik
pozostaje wewnątrz danego `data_dir`. Dodać testy dla `../`, ścieżki
bezwzględnej oraz poprawnego identyfikatora. Rozważyć też ograniczoną pamięć
podręczną modeli.

### CR-02: publicznie dostępne operacje nie mają ograniczeń zasobów

**Znaczenie: średnie**

Serwer domyślnie wiąże się ze wszystkimi interfejsami IPv4. Nie ma
uwierzytelniania, limitu rozmiaru żądania ani długości tekstu, limitu czasu
syntezy, ograniczenia liczby równoległych żądań ani ograniczenia liczby modeli
w pamięci. Dodatkowo `/download` pozwala każdemu klientowi inicjować pobieranie
dużych plików i nadpisywanie lokalnych modeli, a `/all-voices` wykonuje nowe
żądanie zewnętrzne przy każdym wywołaniu.

Dokumentacja prawidłowo ostrzega, że wbudowany serwer nie jest kompletną bramą
produkcyjną, jednak bezpieczny adres `127.0.0.1` jest opisany jako właściwa
wartość domyślna, podczas gdy kod używa `0.0.0.0`. Błąd konfiguracji może więc
nieświadomie wystawić kosztowne operacje na sieć lokalną lub publiczną.

**Zalecenie:** zmienić wartość domyślną `--host` na `127.0.0.1`, ustawić
`MAX_CONTENT_LENGTH`, ograniczyć długość `text`, wyłączyć `/download` domyślnie
i dokumentować jego jawne włączenie. Dla wdrożeń sieciowych wymagać warstwy
pośredniczącej zapewniającej uwierzytelnianie, TLS, limity czasu i liczby
żądań. Dodać test odpowiedzi `413` dla zbyt dużego żądania.

### CR-03: główny potok GitHub Actions nie uruchamia zestawu testów ani linterów

**Znaczenie: średnie**

Repozytorium zawiera 90 zebranych testów oraz skrypty `script/test` i
`script/lint`, lecz zadanie linuksowe w `.github/workflows/ci.yml` uruchamia
tylko wybrane kontrole i krótkie fragmenty Pythona. Nie instaluje dodatku
`dev`, nie wywołuje `pytest`, `black`, `isort`, `flake8`, `pylint` ani `mypy`.
Aktualny problem formatowania trzech plików nie jest więc wykrywany w GitHub
Actions. Regresje w syntezie, serwerze HTTP, pobieraniu modeli i zbiorze danych
mogą zostać połączone z gałęzią główną mimo zielonego wyniku potoku.

**Zalecenie:** dodać osobne zadanie instalujące `.[dev,http]`, a następnie
uruchamiające `python script/lint` oraz `PYTHONPATH=src python -m pytest` albo
testować z zainstalowanym pakietem. Ciężkie lub zależne od opcjonalnych modeli
testy można oznaczyć i uruchamiać osobno, ale podstawowy zestaw nie powinien
być zastępowany ręcznymi fragmentami kontrolnymi.

### CR-04: ujemne i niefinitywne `--sentence-silence` kończy CLI wyjątkiem

**Znaczenie: niskie**

Interfejs wiersza poleceń przyjmuje `--sentence-silence` jako dowolny `float`.
Następnie mnoży tę wartość przez częstotliwość próbkowania i przekazuje wynik
do `bytes`. Wartość ujemna prowadzi do `ValueError`, a `nan` i nieskończoność
do błędu konwersji na liczbę całkowitą. Błąd następuje dopiero po kosztownym
wczytaniu modelu. Serwer HTTP ma już pomocniczy analizator
`_nonnegative_finite_float`, więc zachowanie dwóch interfejsów jest niespójne.

**Zalecenie:** przenieść walidator skończonej, nieujemnej liczby do wspólnego
modułu albo dodać analogiczny typ argumentu do CLI. Dodać testy wartości `-1`,
`nan`, `inf`, `0` i poprawnej wartości dodatniej.

### CR-05: skrypty z katalogu `script` nie są wykonywalne

**Znaczenie: niskie**

Skrypty `script/test`, `script/lint` i `script/run` mają poprawne wiersze
uruchamiające Pythona, ale w indeksie Git mają tryb `100644`. Bezpośrednie
wywołanie `./script/test` lub `./script/lint` kończy się odmową dostępu. Nazwa
katalogu i obecność wiersza `#!/usr/bin/env python3` sugerują, że powinny działać
jak polecenia. Użytkownik może uruchomić je przez `python script/test`, lecz nie
jest to oczywiste i nie jest egzekwowane w potoku.

**Zalecenie:** ustawić bit wykonywania dla skryptów przeznaczonych do
bezpośredniego użycia albo konsekwentnie dokumentować wywołanie przez
`python`. Dodać prostą kontrolę trybów plików do GitHub Actions.

## Mocne strony

- Pobieranie modeli używa plików tymczasowych, waliduje dostępne sumy kontrolne
  i publikuje model wraz z konfiguracją z możliwością wycofania częściowej
  operacji.
- Walidacja identyfikatora mówcy odrzuca wartości logiczne oraz liczby spoza
  zakresu, a kod syntezy sprawdza skończoność i zakres skal.
- Projekt ma rozbudowany zestaw testów obejmujący syntezę, fonemizację,
  pobieranie modeli, serwer HTTP, dane treningowe i narzędzia pomocnicze.
- `scripts/check_project.py` zapewnia szybką i działającą kontrolę spójności
  podstawowych artefaktów projektu.
- Dokumentacja serwera HTTP jasno wskazuje potrzebę uwierzytelniania, TLS i
  ograniczania żądań przed wdrożeniem poza zaufaną siecią.

## Zalecana kolejność prac

1. Usunąć możliwość wskazania modelu poza `data_dir` i dodać testy regresji.
2. Zmienić domyślny adres serwera na `127.0.0.1` oraz dodać limity żądań i
   jawne włączanie pobierania.
3. Włączyć pełne testy oraz kontrole jakości do GitHub Actions, po czym poprawić
   zgłoszone formatowanie.
4. Ujednolicić walidację `--sentence-silence` między CLI i HTTP.
5. Uporządkować sposób uruchamiania skryptów deweloperskich.

Po realizacji punktów 1 do 3 warto przeprowadzić ponowny, dynamiczny przegląd
serwera z rzeczywistym modelem, pomiarem zachowania przy równoległych żądaniach
i kontrolą wzrostu pamięci po przełączaniu głosów.
