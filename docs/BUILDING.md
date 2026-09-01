# Budowanie projektu ze źródeł

Budowanie projektu ze źródeł (building from source) jest potrzebne przede wszystkim podczas rozwijania samego Pipera, modyfikowania rozszerzeń natywnych lub przygotowywania pakietów dystrybucyjnych. Do zwykłego korzystania z gotowego modelu głosu nie trzeba wykonywać pełnego procesu kompilacji.

Ten rozdział opisuje środowisko programistyczne repozytorium `piper-mat`.

## 1. Narzędzia

Projekt wykorzystuje między innymi:

- CMake do konfiguracji budowania części natywnych,
- Ninja jako szybki system wykonywania zadań budowania,
- scikit-build-core do integracji procesu budowania z pakietem Pythona,
- kompilator języka C/C++ właściwy dla platformy,
- Python i narzędzia pakietowe.

### CMake

CMake jest generatorem systemu budowania (build-system generator). Nie jest samym kompilatorem. Na podstawie plików konfiguracyjnych przygotowuje instrukcje dla właściwego narzędzia budowania.

### Ninja

Ninja jest narzędziem budowania (build tool), które wykonuje zależności i polecenia wygenerowane przez system konfiguracji. Jest często używane z CMake ze względu na prostotę i szybkość.

### scikit-build-core

`scikit-build-core` łączy mechanizmy budowania CMake z ekosystemem pakietów Pythona. Dzięki temu rozszerzenia natywne mogą być budowane w procesie tworzenia lub instalowania pakietu.

## 2. Zależności systemowe w Debianie i Ubuntu

Przykładowy zestaw:

```bash
sudo apt-get update
sudo apt-get install \
  build-essential \
  cmake \
  ninja-build
```

`build-essential` dostarcza podstawowe narzędzia kompilacyjne. Dokładne zależności mogą różnić się pomiędzy systemami i wersjami projektu.

## 3. Pobranie repozytorium

```bash
git clone https://github.com/MatPomGit/piper-mat.git
cd piper-mat
```

Dokumentacja `piper-mat` nie powinna kierować użytkownika do klonowania projektu źródłowego zamiast tego repozytorium, chyba że dany rozdział wyraźnie opisuje porównanie lub synchronizację z projektem źródłowym.

## 4. Środowisko wirtualne

Środowisko wirtualne (virtual environment) izoluje zależności Pythona projektu od globalnej instalacji interpretera.

Linux i macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Nie należy instalować zależności deweloperskich globalnie, jeżeli nie ma ku temu konkretnej potrzeby.

## 5. Instalacja edytowalna

Instalacja edytowalna (editable install) pozwala uruchamiać pakiet bez tworzenia nowej kopii kodu po każdej zmianie źródeł.

Dla środowiska deweloperskiego:

```bash
python -m pip install -e ".[dev]"
```

Jeżeli potrzebny jest zestaw zależności związany z trenowaniem, należy użyć odpowiedniej grupy zdefiniowanej przez bieżącą konfigurację projektu. Dostępność grup należy sprawdzać w pliku `pyproject.toml`.

## 6. Budowanie rozszerzeń natywnych

Jeżeli rozwijana część projektu wymaga ręcznego zbudowania rozszerzenia w bieżącym drzewie źródeł, można użyć mechanizmu właściwego dla aktualnej konfiguracji projektu.

Starszy proces może wykorzystywać:

```bash
python setup.py build_ext --inplace
```

Polecenie `setup.py` należy traktować jako mechanizm zgodności ze starszym sposobem budowania, a nie automatycznie jako preferowany interfejs dla nowego kodu. Jeżeli `pyproject.toml` i backend budowania obsługują wymagany proces, należy preferować współczesny mechanizm pakietowy.

## 7. Uruchomienie po zbudowaniu

Podstawowa kontrola:

```bash
python -m piper --help
```

Następnie należy wykonać testy odpowiednie dla zmienianego komponentu. Sam fakt, że moduł można zaimportować, nie potwierdza poprawności działania całego systemu.

## 8. Budowanie pakietu

Pakiet dystrybucyjny można utworzyć za pomocą:

```bash
python -m build
```

Proces może wygenerować dystrybucję źródłową oraz pakiet wheel.

### Pakiet wheel

Wheel jest binarnym lub gotowym do instalacji formatem dystrybucyjnym Pythona. Dla projektu zawierającego kod natywny zgodność pakietu zależy od platformy, ABI i sposobu zbudowania rozszerzeń.

## 9. Stabilne ABI Pythona

Interfejs binarny aplikacji (Application Binary Interface, ABI) określa sposób współpracy skompilowanych komponentów na poziomie binarnym.

Piper wykorzystuje ograniczony interfejs API Pythona (Limited C API), aby w odpowiednich przypadkach korzystać ze stabilnego ABI (Stable ABI). Pozwala to ograniczyć liczbę wariantów binarnych wymaganych dla różnych wersji Pythona.

Nie oznacza to automatycznie zgodności jednego pakietu ze wszystkimi systemami operacyjnymi i architekturami. Platforma nadal pozostaje istotnym wymiarem zgodności.

## 10. eSpeak NG

Piper wykorzystuje eSpeak NG do fonemizacji tekstu. Projekt korzysta z natywnej integracji, ponieważ potrzebuje informacji wykraczających poza prosty tekstowy wynik standardowego programu wiersza poleceń.

Jednym z istotnych elementów jest zachowanie terminatora klauzuli, np. kropki, pytajnika lub wykrzyknika. Interpunkcja może być przekazywana do modelu jako część reprezentacji wejściowej i wpływać na prozodię.

Przykładowo:

```text
To jest zdanie.
Czy to jest pytanie?
To jest wykrzyknienie!
```

mogą prowadzić do różnych realizacji intonacyjnych, jeżeli model nauczył się takich zależności z danych.

## 11. Nazewnictwo w kodzie i narzędziach

PEP 8 dotyczy kodu Pythona. W nowych modułach należy stosować między innymi:

```text
voice_loader.py
sample_rate
load_voice()
VoiceModel
DEFAULT_SAMPLE_RATE
```

Odpowiada to odpowiednio nazwie modułu w `snake_case`, zmiennej w `snake_case`, funkcji w `snake_case`, klasie w `CapWords` i stałej w `UPPER_CASE_WITH_UNDERSCORES`.

Opcje wiersza poleceń nie są identyfikatorami Pythona. Jeżeli interfejs definiuje opcję jako `--sample-rate`, należy zachować `kebab-case`. Jeżeli istniejący interfejs definiuje `--output_file`, należy zachować jego rzeczywistą nazwę do czasu świadomej zmiany API.

## 12. Kontrola jakości po zmianach

Po modyfikacji kodu należy uruchomić kontrole odpowiadające zakresowi zmiany. W zależności od komponentu mogą obejmować:

- testy jednostkowe,
- testy integracyjne,
- kontrolę formatowania i stylu,
- kontrolę statyczną,
- budowanie pakietu,
- podstawowy test uruchomienia,
- test syntezy modelu.

Nie należy wykonywać niezwiązanych refaktoryzacji wyłącznie przy okazji naprawy procesu budowania. Zasada KISS oraz mały zakres zmian ułatwiają diagnostykę i przegląd kodu.

## 13. Zgodność dokumentacji z implementacją

Polecenia w tym rozdziale powinny odpowiadać aktualnemu `pyproject.toml`, strukturze repozytorium i skryptom projektu. Jeżeli proces budowania zostanie zmieniony, dokumentację należy aktualizować razem z kodem.

Dokumentacja nie może utrwalać poleceń historycznych tylko dlatego, że działały w poprzedniej wersji projektu.
