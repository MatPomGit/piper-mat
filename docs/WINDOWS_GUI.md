# Kreator trenowania dla Windows 11

Kreator Windows prowadzi przez przygotowanie środowiska i trenowanie `pl_PL-mateusz-medium` bez konieczności ręcznego wykonywania wszystkich poleceń Git, PowerShell, Pythona i PyTorch.

Interfejs upraszcza proces, ale nie zmienia jego podstawowych etapów. Pod spodem nadal istnieją repozytorium Git, środowisko Pythona, zależności, zbiór danych, punkt kontrolny i proces trenowania.

## Najkrótsza ścieżka

1. Otwórz katalog `piper-mat`.
2. Uruchom `START_PIPER_MAT_GUI.bat`.
3. Wykonuj kroki kreatora w podanej kolejności.
4. Po komunikacie o poprawnym zakończeniu przejdź do następnego etapu.
5. Jeżeli pojawi się błąd, najpierw użyj funkcji **Napraw bezpiecznie**.
6. Jeżeli problem pozostaje, sprawdź pole **Szczegóły techniczne**.

## Diagnostyka a naprawa

Diagnostyka sprawdza stan systemu, ale nie powinna samodzielnie wykonywać ryzykownych zmian. Naprawa automatyczna jest ograniczona do operacji, które można wykonać bez utraty danych użytkownika.

Przycisk **Napraw bezpiecznie** uruchamia `tools/windows_doctor.py`.

Narzędzie może między innymi:

- skonfigurować obsługę długich ścieżek dla lokalnego repozytorium Git,
- ponownie zainicjalizować Git LFS,
- ponowić `git lfs pull`,
- wykryć uszkodzone `.venv`,
- zachować stare środowisko przed utworzeniem nowego,
- zaktualizować `pip`, `setuptools` i `wheel`,
- ponownie zainstalować wymagane zależności.

Automatyczna naprawa nie powinna:

- usuwać nagrań,
- usuwać punktów kontrolnych,
- usuwać wyników trenowania,
- odrzucać lokalnych zmian Git,
- zastępować nieznanego punktu kontrolnego bez weryfikacji.

## Kontrola systemu

Funkcja **Sprawdź system** kontroluje co najmniej:

- wersję Windows,
- wersję Pythona,
- Git,
- Git LFS,
- wolne miejsce na dysku,
- poprawność repozytorium,
- stan `.venv`,
- wymagane biblioteki Pythona,
- działanie PyTorch,
- dostępność CUDA,
- rozszerzenie `monotonic_align`,
- bazowy punkt kontrolny,
- obecność rzeczywistych plików WAV zamiast wskaźników Git LFS.

Wynik diagnostyki może mieć poziom informacyjny, ostrzegawczy albo błędu. Błąd dotyczący wymaganego elementu powinien blokować rozpoczęcie trenowania.

## Odporność na typowe problemy Windows

Kreator powinien obsługiwać typowe problemy bez niszczenia istniejącego środowiska:

- operacje sieciowe mogą być ponawiane po błędach przejściowych,
- aktualizacja repozytorium powinna unikać automatycznego przepisywania lokalnej historii,
- niepusty katalog, który nie jest oczekiwanym repozytorium, nie powinien być automatycznie usuwany,
- uszkodzone `.venv` powinno zostać zachowane pod jednoznaczną nazwą kopii,
- trenowanie nie powinno rozpoczynać się po wykryciu błędu blokującego,
- awaria nowej sesji nie powinna niszczyć ostatniego poprawnego punktu wznowienia.

## Starter

`START_PIPER_MAT_GUI.bat` uruchamia `tools/start_windows_gui.ps1`.

Starter sprawdza podstawowe wymagania przed uruchomieniem graficznego interfejsu użytkownika (graphical user interface, GUI), między innymi:

- obsługiwaną wersję Pythona,
- Git for Windows,
- Git LFS.

Jeżeli dostępny jest `winget`, kreator może pomóc w instalacji brakujących narzędzi systemowych. Po instalacji komponentu zmieniającego `PATH` najbezpieczniej zamknąć i ponownie uruchomić starter.

## Etapy kreatora

### 1. Wybór katalogu projektu

Wybierz katalog na lokalnym dysku SSD z wystarczającą ilością wolnego miejsca. Należy unikać nośników wymiennych i katalogów synchronizowanych wyłącznie na żądanie.

### 2. Pobranie lub aktualizacja repozytorium

Kreator pobiera `piper-mat` albo aktualizuje istniejące repozytorium.

Przed aktualizacją nie powinien automatycznie usuwać lokalnych zmian użytkownika. Konflikt wymagający decyzji użytkownika należy zgłosić zamiast ukrywać.

### 3. Pobranie dużych artefaktów

Git LFS pobiera duże pliki przechowywane poza zwykłymi obiektami Git. Przerwaną operację można ponowić.

Po zakończeniu należy sprawdzić, czy wymagane pliki nie są jedynie wskaźnikami Git LFS.

### 4. Przygotowanie `.venv`

Środowisko wirtualne (virtual environment) izoluje zależności Pythona projektu od globalnej instalacji.

Jeżeli istniejące środowisko jest uszkodzone, kreator powinien zachować je jako kopię i dopiero potem utworzyć nowe.

### 5. Instalacja bibliotek

Instalowane są zależności wymagane przez projekt i proces trenowania.

Wersje zależności mają znaczenie dla powtarzalności. Po przygotowaniu działającego środowiska jego stan powinien być możliwy do zapisania w raporcie eksperymentu.

### 6. Budowanie `monotonic_align`

`monotonic_align` jest rozszerzeniem używanym podczas trenowania do wyznaczania monotonicznego dopasowania pomiędzy reprezentacją tekstową i przebiegiem czasowym mowy.

Krok wymaga narzędzi kompilacyjnych C/C++. W Windows może być potrzebny Visual Studio Build Tools z komponentem obsługującym rozwój aplikacji C++ dla komputerów stacjonarnych.

Brak tego komponentu jest problemem środowiska budowania, a nie błędem zbioru danych ani modelu.

### 7. Walidacja nagrań

Walidator sprawdza metadane i pliki WAV bez modyfikowania nagrań.

Należy przeanalizować nie tylko błędy, ale również ostrzeżenia dotyczące jakości sygnału, długości segmentów, ciszy i przesterowania.

### 8. Pełna diagnostyka

Przed trenowaniem należy wykonać pełną kontrolę systemu. Ten etap potwierdza, że środowisko jest spójne po wszystkich wcześniejszych zmianach.

### 9. Kontrola planu trenowania

Kreator pokazuje liczbę zaplanowanych sesji, dotychczasowy postęp i punkt, od którego zostanie wznowione trenowanie.

Przed rozpoczęciem należy sprawdzić, czy wskazany punkt kontrolny odpowiada oczekiwanemu eksperymentowi.

### 10. Uruchomienie następnej sesji

Bezpośrednio przed startem wykonywana jest ponowna diagnostyka. Błąd blokujący powinien zatrzymać operację przed uruchomieniem kosztownego procesu trenowania.

Po rozpoczęciu sesji nie należy równolegle modyfikować zbioru danych, konfiguracji ani aktywnego punktu kontrolnego.

### 11. Analiza raportu

Po sesji należy otworzyć raport i wykresy. Celem nie jest tylko potwierdzenie, że proces się zakończył.

Należy sprawdzić:

- przebieg funkcji straty,
- wyniki walidacji,
- ewentualne wartości nietypowe,
- czas sesji,
- zapisane punkty kontrolne,
- komunikaty ostrzegawcze.

## Kolejny dzień pracy

Po ponownym uruchomieniu komputera nie trzeba odtwarzać całego środowiska.

1. Uruchom `START_PIPER_MAT_GUI.bat`.
2. Wykonaj **Sprawdź system**.
3. Sprawdź plan trenowania.
4. Potwierdź, że wykryty został właściwy punkt wznowienia.
5. Uruchom następną sesję.
6. Po zakończeniu przeanalizuj raport.

Kreator powinien użyć ostatniego poprawnego `last.ckpt` i wznowić pełny stan Lightning, jeżeli konfiguracja eksperymentu jest zgodna.

## Kiedy nie używać automatycznej naprawy

Nie należy wielokrotnie uruchamiać automatycznej naprawy, jeżeli problem dotyczy:

- lokalnych zmian w kodzie,
- nieznanego pochodzenia punktu kontrolnego,
- ręcznie zmodyfikowanej konfiguracji eksperymentu,
- uszkodzonych danych źródłowych,
- braku miejsca wymagającego decyzji o usunięciu danych,
- konfliktu wersji, którego rozwiązanie może zmienić wynik eksperymentu.

W takich przypadkach należy najpierw ustalić przyczynę problemu.

## Nazewnictwo techniczne

Nazwy plików i skryptów, takie jak `START_PIPER_MAT_GUI.bat`, `start_windows_gui.ps1` i `windows_doctor.py`, należy zapisywać dokładnie tak, jak występują w repozytorium.

PEP 8 ma zastosowanie do identyfikatorów i modułów Pythona. Dlatego `windows_doctor.py` używa `snake_case`. Nazwa pliku wsadowego Windows nie musi być zmieniana na `snake_case`, jeżeli pełni rolę stabilnego punktu wejścia dla użytkownika.
