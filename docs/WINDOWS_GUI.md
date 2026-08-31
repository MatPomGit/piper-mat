# Kreator treningu dla Windows 11

To jest najprostsza metoda przygotowania i trenowania głosu `pl_PL-mateusz-medium` na Windows 11. Nie trzeba znać Git, Pythona, PowerShell ani PyTorch.

## Najkrótsza instrukcja

1. Otwórz folder projektu `piper-mat`.
2. Kliknij dwa razy plik `START_PIPER_MAT_GUI.bat`.
3. Pojawi się okno kreatora.
4. Zacznij od kroku 1 i wykonuj kolejne kroki po kolei.
5. Jeżeli krok zakończy się zielonym komunikatem, przejdź dalej.
6. Jeżeli pojawi się czerwony komunikat, nie zgaduj. Przeczytaj komunikat i dolne pole „Szczegóły techniczne”.

Można zaznaczyć opcję **„Po sukcesie przejdź automatycznie do następnego kroku”**. Program nadal nie uruchomi wielogodzinnego treningu bez dodatkowego potwierdzenia.

## Co robią kolejne kroki

### 1. Wybierz miejsce na projekt

Wskaż zwykły folder na lokalnym dysku, np. `Dokumenty`. Program będzie pracował w katalogu `piper-mat`.

Nie wybieraj:

- pendrive'a,
- katalogu tymczasowego,
- folderu OneDrive synchronizowanego w trybie „tylko online”,
- dysku z bardzo małą ilością wolnego miejsca.

### 2. Pobierz albo zaktualizuj repozytorium

Program pobiera kod z GitHub. Jeżeli repozytorium już istnieje, wykona bezpieczne `git pull --ff-only`.

W uproszczeniu: **ten krok zapewnia, że masz najnowszą wersję programu**.

### 3. Pobierz duże pliki treningowe

Git przechowuje duże pliki przez Git LFS. Dotyczy to m.in. nagrań i punktów kontrolnych.

W uproszczeniu: **kod już masz, ale teraz pobierane są ciężkie pliki potrzebne do uczenia modelu**.

### 4. Utwórz prywatne środowisko Pythona

Powstaje katalog `.venv`.

W uproszczeniu: **program tworzy własne pudełko z Pythonem, żeby nie mieszać bibliotek z innymi projektami**.

### 5. Zainstaluj biblioteki do treningu

Instalowane są m.in. PyTorch, Lightning, TensorBoard, librosa i Cython.

Ten etap może trochę potrwać i pobrać dużo danych.

### 6. Zbuduj brakujący moduł treningowy

Kreator kompiluje `monotonic_align` natywnie dla Windows.

Jeżeli Windows zgłosi brak kompilatora C++, należy zainstalować **Visual Studio 2022 Build Tools** i wybrać składnik **Desktop development with C++**. Następnie wystarczy ponownie kliknąć przycisk tego kroku.

### 7. Sprawdź nagrania

Walidator sprawdza metadane i WAV. Nie zmienia plików.

Szuka m.in.:

- brakujących nagrań,
- złej częstotliwości próbkowania,
- zbyt dużej ciszy,
- przesterowania,
- podejrzanych poziomów sygnału.

### 8. Sprawdź, czy komputer jest gotowy

To najważniejsza kontrola przed treningiem.

Program sprawdza:

- czy duże pliki rzeczywiście pobrano z Git LFS,
- czy działają wszystkie biblioteki,
- czy działa `monotonic_align`,
- czy punkt kontrolny można odczytać na Windows,
- czy jest wystarczająco dużo miejsca na dysku,
- czy plan treningu jest poprawny.

Jeżeli pojawi się **Wynik: GOTOWE**, można trenować.

### 9. Sprawdź plan treningu

Model jest trenowany w kilku sesjach. Domyślnie są to cztery podejścia.

Po każdej sesji zapisuje się stan. Możesz wtedy wyłączyć komputer i wrócić innego dnia.

### 10. Uruchom następną sesję treningu

Przed startem pojawi się dodatkowe pytanie z potwierdzeniem.

Kreator jeszcze raz uruchamia kontrolę gotowości. Dopiero po jej poprawnym zakończeniu rozpoczyna trening.

Po zakończeniu sesji automatycznie powstają:

- punkt wznowienia `last.ckpt`,
- najlepszy punkt według `val_mel`, jeśli jest dostępny,
- najlepszy punkt według `val_mos`, jeśli jest dostępny,
- raport Markdown,
- podsumowanie JSON,
- wykresy SVG.

Po komunikacie o poprawnym zakończeniu sesji można bezpiecznie wyłączyć komputer.

### 11. Otwórz raport

Kreator znajduje raport z ostatniej zakończonej sesji i otwiera go domyślnym programem Windows.

W tym samym katalogu znajdują się wykresy. Służą do porównywania kolejnych sesji i sprawdzania, czy model nadal się poprawia.

## Następny dzień treningu

Nie wykonuj wszystkiego od początku.

1. Włącz komputer.
2. Otwórz `piper-mat`.
3. Uruchom `START_PIPER_MAT_GUI.bat`.
4. Przejdź do kroku 9 i sprawdź stan.
5. Przejdź do kroku 10 i uruchom następną sesję.

Kreator użyje ostatniego zapisanego `last.ckpt` i wznowi pełny stan Lightning.

## Gdy czegoś brakuje przed uruchomieniem GUI

Starter sprawdza Python i Git.

Jeżeli ich brakuje, a system ma `winget`, może zaproponować automatyczną instalację:

- Python 3.11,
- Git for Windows.

Po instalacji należy ponownie uruchomić `START_PIPER_MAT_GUI.bat`.

## Gdzie są szczegóły techniczne

GUI jest tylko prostą nakładką. Pod spodem nadal używane są istniejące, wersjonowane narzędzia projektu:

- `scripts/validate_dataset.py`,
- `scripts/check_training_ready.py`,
- `scripts/train_sessions.py`,
- `scripts/report_training_session.py`.

Dzięki temu użytkownik zaawansowany może wykonać dokładnie te same operacje z terminala, a użytkownik początkujący może przejść cały proces klikając kolejne przyciski.
