# Plan rozwoju `piper-mat`

Plan rozwoju (roadmap) określa kolejność prac prowadzących od przygotowania danych do stabilnego wydania `pl_PL-mateusz-medium`. Nie jest listą pomysłów. Każde zadanie powinno mieć mierzalny rezultat i prowadzić do artefaktu, wyniku oceny albo decyzji projektowej.

Priorytety oznaczają:

- **P0**: zadania blokujące uzyskanie poprawnego modelu,
- **P1**: zadania wymagane przed stabilnym wydaniem,
- **P2**: zadania zwiększające jakość procesu, automatyzacji lub publikacji,
- **P3**: rozwój integracji po ustabilizowaniu modelu.

## Zrealizowana infrastruktura

Repozytorium posiada już podstawy powtarzalnego procesu:

- [x] wersjonowaną konfigurację `pl_PL-mateusz-medium`,
- [x] wielosesyjne trenowanie i wznowienie pełnego stanu Lightning,
- [x] archiwizację punktów kontrolnych,
- [x] raporty z kolejnych sesji trenowania,
- [x] skrypty `train.sh` i `train.ps1`,
- [x] diagnostykę gotowości środowiska,
- [x] walidację `metadata.csv` i plików WAV,
- [x] analizę czasu nagrań, RMS, wartości szczytowej, przesterowania i ciszy,
- [x] deterministyczny podział na zbiory treningowy, walidacyjny i testowy,
- [x] korpus regresyjny języka polskiego,
- [x] test fonemizacji eSpeak NG,
- [x] obliczanie WER i CER,
- [x] podstawowy test poprawności ONNX i JSON,
- [x] karty zbioru danych i modelu,
- [x] protokół oceny jakości,
- [x] manifest bazowych punktów kontrolnych,
- [x] weryfikację SHA-256 punktów kontrolnych,
- [x] rejestrowanie środowiska eksperymentu,
- [x] pomiar RTF,
- [x] kontrolę gotowości kandydata do wydania,
- [x] generator paczki wydania,
- [x] dokumentację wdrożenia,
- [x] witrynę dokumentacji MkDocs,
- [x] ciągłą integrację podstawowych kontroli projektu,
- [x] standard terminologiczny i redakcyjny dokumentacji,
- [x] zasady PEP 8, PEP 257 i KISS dla rozwijanego kodu.

## P0. Zamrożenie zbioru danych

Celem etapu jest utworzenie jednej jednoznacznie zidentyfikowanej wersji danych wejściowych do właściwego eksperymentu treningowego.

- [ ] Wykonać `git lfs pull` na komputerze treningowym.
- [ ] Uruchomić `python scripts/check_training_ready.py`.
- [ ] Uruchomić pełną walidację dźwięku przez `scripts/validate_dataset.py` bez pomijania analizy WAV.
- [ ] Przejrzeć wszystkie ostrzeżenia dotyczące przesterowania, ciszy, poziomu sygnału i długości segmentów.
- [ ] Usunąć albo poprawić segmenty niespełniające przyjętych kryteriów jakości.
- [ ] Zweryfikować transkrypcje względem nagrań.
- [ ] Wyznaczyć końcowe statystyki zbioru.
- [ ] Wygenerować `dataset/splits.json` na finalnych metadanych.
- [ ] Sprawdzić brak przecieku danych pomiędzy podziałami.
- [ ] Zamrozić podział i zapisać SHA-256 metadanych.
- [ ] Uzupełnić `dataset/DATASET_CARD.md` rzeczywistymi danymi.

**Rezultat:** wersjonowany zbiór danych i zamrożony podział gotowy do właściwego trenowania.

## P0. Właściwe trenowanie modelu

Celem jest wykonanie kontrolowanego eksperymentu, którego pochodzenie można później odtworzyć.

- [ ] Zweryfikować bazowy punkt kontrolny przez SHA-256.
- [ ] Zapisać wersję kodu i konfigurację eksperymentu.
- [ ] Zweryfikować praktycznie domyślny plan sesji na docelowym GPU.
- [ ] Ustalić ostateczny rozmiar partii na podstawie dostępnej pamięci GPU i stabilności trenowania.
- [ ] Uruchomić pierwszą pełną sesję.
- [ ] Przejrzeć raport i wykresy po sesji.
- [ ] Kontynuować kolejne sesje przez mechanizm wznowienia trenowania.
- [ ] Nie zmieniać wielu hiperparametrów jednocześnie bez utworzenia nowego, opisanego eksperymentu.
- [ ] Zachować `last.ckpt` oraz punkty kontrolne wybrane według kryteriów walidacyjnych.
- [ ] Zapisać środowisko wykonawcze przez `scripts/record_environment.py`.

**Rezultat:** komplet punktów kontrolnych i raportów z powtarzalnego eksperymentu.

## P1. Wybór modelu kandydującego do wydania

Nie należy automatycznie wybierać ostatniego punktu kontrolnego.

- [ ] Porównać `last.ckpt`, `best_val_mel.ckpt` i `best_val_mos.ckpt`.
- [ ] Wykonać odsłuch tego samego zestawu zdań dla wszystkich kandydatów.
- [ ] Sprawdzić wymowę trudnych przypadków języka polskiego.
- [ ] Wybrać punkt kontrolny na podstawie wyników walidacji i odsłuchu.
- [ ] Zapisać kryterium wyboru.
- [ ] Wyeksportować wybrany model do ONNX.
- [ ] Uruchomić `scripts/smoke_test_voice.py` na wyeksportowanej parze ONNX i JSON.

**Rezultat:** jednoznacznie zidentyfikowany kandydat do pełnej oceny.

## P1. Ocena zrozumiałości

- [ ] Wygenerować mowę dla zamrożonego zbioru testowego.
- [ ] Wygenerować mowę dla `tests/polish_sentences.txt`.
- [ ] Wybrać i przypiąć wersję niezależnego systemu automatycznego rozpoznawania mowy.
- [ ] Obliczyć współczynnik błędów słów (Word Error Rate, WER).
- [ ] Obliczyć współczynnik błędów znaków (Character Error Rate, CER).
- [ ] Zapisać surowe transkrypcje systemu rozpoznawania.
- [ ] Przeanalizować najczęstsze klasy błędów zamiast ograniczać się do pojedynczej wartości liczbowej.

**Rezultat:** powtarzalny raport zrozumiałości modelu.

## P1. Ocena podobieństwa głosu

- [ ] Wybrać model tworzący reprezentację wektorową mówcy (speaker embedding).
- [ ] Przypiąć jego konkretną wersję.
- [ ] Zdefiniować zestaw nagrań referencyjnych prawdziwego głosu.
- [ ] Zdefiniować odpowiadający zestaw wypowiedzi syntetycznych.
- [ ] Obliczyć automatyczną miarę podobieństwa.
- [ ] Uzupełnić wynik oceną odsłuchową.

**Rezultat:** udokumentowana ocena podobieństwa głosu syntetycznego do głosu referencyjnego.

## P1. Ocena percepcyjna

- [ ] Przygotować reprezentatywny zestaw próbek.
- [ ] Ustalić procedurę średniej oceny opinii słuchaczy (Mean Opinion Score, MOS) albo porównawczej średniej oceny opinii słuchaczy (Comparative Mean Opinion Score, CMOS).
- [ ] Ustalić skalę ocen.
- [ ] Zapewnić ślepy sposób prezentacji próbek tam, gdzie jest wymagany.
- [ ] Zebrać wyniki.
- [ ] Obliczyć statystyki opisowe i udokumentować liczbę oceniających.
- [ ] Zachować formularz lub procedurę badania razem z wynikami.

**Rezultat:** audytowalna ocena percepcyjna jakości i naturalności głosu.

## P1. Ocena wydajności

- [ ] Uruchomić `scripts/benchmark_voice.py` na platformie x86-64.
- [ ] Wykonać pomiar na Raspberry Pi 5.
- [ ] Zapisać współczynnik czasu rzeczywistego (Real-Time Factor, RTF).
- [ ] Zapisać czas do uzyskania pierwszego fragmentu dźwięku, jeżeli interfejs umożliwia taki pomiar.
- [ ] Zapisać maksymalne użycie pamięci RAM.
- [ ] Zapisać wersję środowiska wykonawczego.
- [ ] Powtórzyć pomiary wystarczającą liczbę razy, aby pojedynczy przypadek nie decydował o wyniku.

**Rezultat:** porównywalny profil wydajności modelu na platformach docelowych.

## P1. Polska fonemizacja

- [ ] Przypiąć konkretną wersję eSpeak NG dla testów regresyjnych.
- [ ] Wybrać reprezentatywne zdania testowe.
- [ ] Zapisać oczekiwane sekwencje fonemów dopiero po przypięciu wersji eSpeak NG.
- [ ] Dodać testy przypadków problematycznych: liczby, skróty, jednostki, nazwy własne i znaki diakrytyczne.
- [ ] Dokumentować świadome zmiany oczekiwanej wymowy po aktualizacji fonemizatora.

**Rezultat:** stabilny zestaw regresyjny polskiej fonemizacji.

## P1. Gotowość wydania

- [ ] Uzupełnić `models/pl_PL-mateusz-medium/MODEL_CARD.md` rzeczywistymi wynikami.
- [ ] Ustalić licencję zbioru danych.
- [ ] Ustalić licencję modelu głosu.
- [ ] Zweryfikować prawa do publikacji głosu i artefaktów.
- [ ] Uruchomić `scripts/check_release_readiness.py`.
- [ ] Usunąć wszystkie krytyczne pola `TODO` z karty modelu.
- [ ] Przygotować reprezentatywne próbki.
- [ ] Utworzyć paczkę przez `scripts/package_release.py`.
- [ ] Zweryfikować `checksums.txt` i `release-manifest.json`.

**Rezultat:** kompletny kandydat do wydania.

## P2. Publikacja i porządkowanie artefaktów

- [ ] Opublikować finalny model jako formalne wydanie zamiast zwykłego pliku w historii Git.
- [ ] Zachować jednoznaczne numery wersji.
- [ ] Nie zastępować opublikowanego modelu innym plikiem pod tym samym numerem wersji.
- [ ] Usunąć z bieżącego drzewa niepotrzebne warianty punktów kontrolnych po potwierdzeniu, że nie są wymagane.
- [ ] Rozważyć podpisywanie manifestów wydania po ustabilizowaniu procesu publikacji.
- [ ] Zweryfikować, czy duże artefakty są przechowywane we właściwym miejscu i nie obciążają niepotrzebnie historii Git.

## P2. Utrzymanie dokumentacji

- [ ] Usunąć lub oznaczyć jako archiwalne dokumenty odziedziczone po projekcie źródłowym, które nie opisują aktualnego `piper-mat`.
- [ ] Ujednolicić przykłady dla `pl_PL-mateusz-medium`.
- [ ] Sprawdzić wszystkie polecenia CLI względem bieżącej implementacji.
- [ ] Sprawdzić zgodność przykładów Pythona z PEP 8 i PEP 257.
- [ ] Sprawdzić brak pauzy em w dokumentacji projektu.
- [ ] Sprawdzić terminologię względem `docs/TERMINOLOGIA.md`.
- [ ] Uruchamiać budowanie MkDocs jako kontrolę odnośników i struktury dokumentacji.

## P3. Integracja z awatarem 3D

Ten etap rozpoczyna się po ustabilizowaniu jakości głosu. Celem jest wykorzystanie tego samego modelu TTS jako źródła dźwięku i informacji czasowej dla animacji twarzy.

- [ ] Ustabilizować eksport dopasowań fonemów do dźwięku.
- [ ] Zdefiniować mapowanie fonemów języka polskiego na wizemy (visemes).
- [ ] Zdefiniować reprezentację danych czasowych niezależną od konkretnego silnika 3D.
- [ ] Opracować koartykulację pomiędzy sąsiednimi wizemami.
- [ ] Dodać wygładzanie przejść i minimalne czasy aktywacji wizemów.
- [ ] Zsynchronizować ruch żuchwy z animacją ust.
- [ ] Dodać warstwę mimiki niezależną od podstawowego ruchu artykulacyjnego.
- [ ] Dodać mruganie, ruch spojrzenia i subtelne ruchy głowy podczas mowy.
- [ ] Zdefiniować interfejs wyjściowy dla docelowego systemu czasu rzeczywistego.
- [ ] Zmierzyć opóźnienie całego procesu tekst → TTS → dane fonemiczne → animacja.

**Rezultat:** działający prototyp fonemicznego systemu synchronizacji ust dla awatara.

## Kryterium wydania `v1.0.0`

Wydanie `pl_PL-mateusz-medium` można oznaczyć jako stabilne, gdy:

- [ ] finalny zbiór danych przeszedł pełną walidację,
- [ ] podział danych jest zamrożony i identyfikowalny,
- [ ] trenowanie można odtworzyć z zapisanej konfiguracji i punktu kontrolnego,
- [ ] kandydat został wybrany według jawnego kryterium,
- [ ] ONNX i JSON przechodzą podstawowy test poprawności,
- [ ] dostępne są WER i CER,
- [ ] dostępna jest ocena podobieństwa głosu,
- [ ] wykonano ocenę percepcyjną,
- [ ] wykonano pomiary wydajności na platformach docelowych,
- [ ] karty danych i modelu są kompletne,
- [ ] licencje są jednoznaczne,
- [ ] kontrola gotowości wydania kończy się powodzeniem,
- [ ] paczka zawiera manifest, sumy kontrolne i próbki,
- [ ] procedura wdrożenia i wycofania wersji została sprawdzona.
