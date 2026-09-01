# Budowanie projektu ze źródeł

Budowanie projektu ze źródeł (building from source) jest potrzebne podczas rozwijania Pipera, modyfikowania rozszerzeń natywnych i przygotowywania pakietów. Do samego używania gotowego modelu głosu nie trzeba wykonywać pełnego procesu kompilacji.

## System budowania

Aktualne repozytorium wykorzystuje `setuptools` jako backend budowania oraz `scikit-build` do integracji z CMake. Źródłem prawdy są `pyproject.toml` i `setup.py`.

Nie należy opisywać tego projektu jako korzystającego z `scikit-build-core`, dopóki konfiguracja repozytorium rzeczywiście nie zostanie na niego przeniesiona.

Podstawowe składniki to:

- `setuptools`,
- `scikit-build`,
- CMake,
- Ninja,
- kompilator C/C++ właściwy dla platformy,
- Python.

CMake jest generatorem systemu budowania (build-system generator). Ninja jest narzędziem wykonującym zadania budowania. `scikit-build` łączy proces CMake z pakietem Pythona.

## Linux

W Debianie i Ubuntu przydatny jest zestaw:

```bash
sudo apt-get update
sudo apt-get install \
  build-essential \
  cmake \
  ninja-build
```

Następnie:

```bash
git clone https://github.com/MatPomGit/piper-mat.git
cd piper-mat
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## Windows

W Windows należy przygotować zgodne narzędzia kompilacyjne C/C++. Dla użytkownika wykonującego trenowanie preferowanym punktem wejścia jest [kreator Windows 11](WINDOWS_GUI.md), ponieważ zawiera diagnostykę środowiska.

Ręczne środowisko Pythona:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Instalacja edytowalna

Instalacja edytowalna (editable install) pozwala korzystać bezpośrednio z bieżącego drzewa źródeł:

```bash
python -m pip install -e '.[dev]'
```

Dla środowiska przeznaczonego do trenowania używana jest grupa `train`:

```bash
python -m pip install -e '.[train]'
```

Dostępne grupy zależności są zdefiniowane w `setup.py`. Obecnie obejmują między innymi `train`, `dev`, `http`, `alignment`, `zh` i `ja`.

## Rozszerzenia natywne

Repozytorium nadal zawiera `setup.py`, dlatego polecenie:

```bash
python setup.py build_ext --inplace
```

jest w tym projekcie rzeczywistym mechanizmem budowania rozszerzeń w bieżącym drzewie źródeł, a nie tylko historycznym przykładem.

Dla procesu trenowania należy również zbudować `monotonic_align` zgodnie z instrukcją w [TRAINING.md](TRAINING.md).

## Kontrola po zbudowaniu

Najprostsza kontrola uruchomienia:

```bash
python -m piper --help
```

Następnie należy wykonać testy odpowiadające zmienianemu komponentowi. Poprawny import modułu nie potwierdza jeszcze poprawności syntezy ani trenowania.

## Budowanie pakietu

Zależność `build` jest częścią grupy deweloperskiej. Pakiet można utworzyć poleceniem:

```bash
python -m build
```

Proces może utworzyć dystrybucję źródłową oraz pakiet wheel.

Wheel jest formatem dystrybucyjnym Pythona. Jeżeli pakiet zawiera kod natywny, jego zgodność zależy między innymi od platformy, architektury i interfejsu binarnego aplikacji (Application Binary Interface, ABI).

## eSpeak NG

Piper wykorzystuje eSpeak NG do fonemizacji tekstu. Natywna integracja pozwala uzyskać informacje potrzebne przez syntezę, w tym zachować znaczenie interpunkcji wpływającej na przebieg wypowiedzi.

Nie należy modyfikować tej warstwy w projekcie głosu bez konkretnej potrzeby, ponieważ zmiana fonemizacji może wpłynąć na zgodność danych treningowych, testów regresyjnych i modelu.

## Nazewnictwo

PEP 8 dotyczy identyfikatorów Pythona. Przykłady:

```text
voice_loader.py
sample_rate
load_voice()
VoiceModel
DEFAULT_SAMPLE_RATE
```

Opcje CLI należy zapisywać dokładnie tak, jak definiuje je rzeczywisty interfejs. `kebab-case` w opcji CLI nie oznacza, że taka sama konwencja jest poprawna dla zmiennej Pythona.

## Kontrola jakości zmian

Po zmianie kodu należy uruchomić kontrole adekwatne do zakresu modyfikacji, na przykład:

- testy jednostkowe,
- testy integracyjne,
- kontrolę formatowania,
- analizę statyczną,
- budowanie pakietu,
- test uruchomienia,
- test syntezy, jeżeli zmiana dotyczy ścieżki wykonawczej.

Nie należy wykonywać niezwiązanych refaktoryzacji przy okazji naprawy procesu budowania.

## Zasada aktualności

`pyproject.toml`, `setup.py`, skrypty budowania i dokumentacja muszą opisywać ten sam proces. Jeżeli konfiguracja zostanie przeniesiona na inny backend, dokumentację należy zmienić w tym samym zakresie prac.
