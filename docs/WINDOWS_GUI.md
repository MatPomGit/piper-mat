# Kreator treningu dla Windows 11

To jest najprostsza metoda przygotowania i trenowania głosu `pl_PL-mateusz-medium` na Windows 11. Nie trzeba znać Git, Pythona, PowerShell ani PyTorch.

## Najkrótsza instrukcja

1. Otwórz folder `piper-mat`.
2. Kliknij dwa razy `START_PIPER_MAT_GUI.bat`.
3. Wykonuj kroki od 1 do 11.
4. Zielony komunikat oznacza, że można przejść dalej.
5. Przy czerwonym komunikacie najpierw kliknij **Napraw bezpiecznie**.
6. Jeżeli problem pozostanie, przeczytaj dolne pole **Szczegóły techniczne**.

## Co kreator potrafi naprawić sam

Przycisk **Napraw bezpiecznie** uruchamia narzędzie `tools/windows_doctor.py`. Naprawa nie usuwa nagrań, punktów kontrolnych ani wyników treningu.

Program może m.in.:

- włączyć obsługę długich ścieżek w lokalnym repozytorium Git,
- ponownie zainicjalizować Git LFS,
- ponowić `git lfs pull`,
- wykryć uszkodzone `.venv`, zachować je jako kopię i utworzyć nowe,
- zaktualizować `pip`, `setuptools` i `wheel`,
- ponownie zainstalować zależności treningowe.

Niektórych rzeczy kreator celowo nie naprawia bez pytania, np. nie usuwa lokalnych zmian Git i nie podmienia checkpointów.

## Co jest sprawdzane przez „Sprawdź system”

Diagnostyka kontroluje:

- Windows i wersję Pythona,
- Git i Git LFS,
- ilość wolnego miejsca na dysku,
- poprawność repozytorium,
- stan `.venv`,
- obecność Pipera, Lightning, TensorBoard i librosa,
- działanie PyTorch,
- dostępność CUDA,
- `monotonic_align`,
- bazowy checkpoint,
- obecność prawdziwych WAV zamiast wskaźników Git LFS.

Wynik może być `OK`, `WARNING` albo `ERROR`. Ostrzeżenie nie zawsze blokuje pracę, ale błąd przed treningiem powinien zostać usunięty.

## Odporność na typowe problemy Windows

Kreator wykonuje dodatkowe zabezpieczenia:

- `git clone`, `git fetch`, `git lfs pull` i instalacja bibliotek są ponawiane po chwilowym błędzie sieci,
- aktualizacja repozytorium używa `pull --ff-only`, więc nie nadpisuje lokalnej historii,
- istniejący niepusty folder, który nie jest repozytorium, nie zostanie automatycznie skasowany,
- uszkodzone `.venv` dostaje nazwę `.venv_broken_DATA_GODZINA`, zamiast być kasowane bez śladu,
- trening nie ruszy, jeśli diagnostyka wykryje błąd,
- przy błędzie treningu poprzedni punkt wznowienia pozostaje bezpieczny.

## Starter uruchamiany dwuklikiem

`START_PIPER_MAT_GUI.bat` uruchamia `tools/start_windows_gui.ps1`.

Starter sprawdza przed pokazaniem GUI:

- Python 3.11 lub nowszy,
- Git for Windows,
- Git LFS.

Jeżeli dostępny jest `winget`, może zaproponować automatyczną instalację brakującego Pythona, Git albo Git LFS. Po instalacji systemowego narzędzia najbezpieczniej ponownie uruchomić starter.

## Kroki kreatora

### 1. Wybierz miejsce na projekt

Wskaż zwykły folder na lokalnym SSD. Unikaj pendrive'a, katalogu tymczasowego i plików OneDrive dostępnych tylko online.

### 2. Pobierz albo zaktualizuj projekt

Program pobiera repozytorium z GitHub albo wykonuje bezpieczną aktualizację istniejącego repozytorium.

### 3. Pobierz duże pliki

Git LFS pobiera nagrania WAV i duże checkpointy. Przerwane pobieranie można uruchomić ponownie.

### 4. Przygotuj `.venv`

Powstaje osobne środowisko Pythona. Jeżeli stare środowisko jest uszkodzone, zostaje zachowane jako kopia.

### 5. Zainstaluj biblioteki

Instalowane są składniki treningu. Przy chwilowych błędach połączenia instalacja jest ponawiana.

### 6. Zbuduj `monotonic_align`

Ten krok wymaga narzędzi C++. Jeśli ich brakuje, zainstaluj **Visual Studio 2022 Build Tools** z komponentem **Desktop development with C++**, uruchom ponownie Windows i powtórz krok.

### 7. Sprawdź nagrania

Walidator sprawdza WAV i metadane bez zmieniania plików.

### 8. Sprawdź cały komputer

Uruchamia pełną diagnostykę. To obowiązkowa kontrola przed treningiem.

### 9. Sprawdź plan treningu

Pokazuje liczbę zaplanowanych sesji i ostatni zapisany postęp.

### 10. Uruchom następną sesję

Przed startem pełna diagnostyka jest wykonywana ponownie. Jeżeli wykryje błąd, trening nie zostanie rozpoczęty.

### 11. Otwórz raport

Otwiera raport i wykresy z ostatniej ukończonej sesji.

## Następny dzień treningu

Po ponownym włączeniu komputera nie trzeba wykonywać wszystkiego od początku:

1. uruchom `START_PIPER_MAT_GUI.bat`,
2. kliknij **Sprawdź system**,
3. jeśli wynik jest poprawny, przejdź do kroku 9,
4. sprawdź plan,
5. uruchom następną sesję w kroku 10.

Kreator użyje ostatniego zapisanego `last.ckpt` i wznowi pełny stan Lightning.
