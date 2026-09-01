# piper-mat

`piper-mat` jest projektem rozwijającym Piper w celu przygotowania, trenowania, oceny, wydania i wdrożenia polskiego modelu głosu `pl_PL-mateusz-medium`.

Dokumentacja opisuje proces projektu głosu. Szczegóły implementacyjne odziedziczone po Piper są dokumentowane tylko wtedy, gdy są potrzebne do trenowania, uruchamiania, rozwijania lub integracji `piper-mat`.

## Cel projektu

Docelowy proces ma być powtarzalny i pozostawiać jednoznacznie identyfikowalne artefakty:

```text
nagrania i transkrypcje
  ↓
walidacja zbioru danych
  ↓
zamrożony podział danych
  ↓
trenowanie
  ↓
wybór punktu kontrolnego
  ↓
eksport ONNX
  ↓
ocena jakości i wydajności
  ↓
wydanie
  ↓
wdrożenie
```

Rozwój integracji z awatarem rozszerza ten proces o dane fonemiczne i animację twarzy:

```text
tekst → Piper TTS → dźwięk i czas fonemów → wizemy → koartykulacja → animacja twarzy
```

## Od czego zacząć

Jeżeli przygotowujesz dane, przejdź do [zbioru danych](DATASET.md).

Jeżeli środowisko jest już gotowe i chcesz trenować model, przejdź do [podstaw trenowania](TRAINING.md) albo [kreatora Windows 11](WINDOWS_GUI.md).

Jeżeli wznawiasz dłuższy eksperyment, użyj procedury [trenowania etapowego](STAGED_TRAINING.md).

Jeżeli model został już wytrenowany, przejdź kolejno do [opisu modelu](MODEL.md), [oceny jakości](EVALUATION.md), [wydawania](RELEASES.md) i [wdrożenia](DEPLOYMENT.md).

Aktualne zadania projektu znajdują się wyłącznie w [planie rozwoju](ROADMAP.md).

## Struktura dokumentacji

Dokumentacja jest podzielona według odpowiedzialności:

- **Projekt głosu** opisuje dane, model, punkty kontrolne, ocenę, wydania i wdrożenie.
- **Trenowanie** opisuje przygotowanie środowiska i prowadzenie eksperymentów.
- **Integracja** opisuje używanie modelu przez CLI, Python i HTTP oraz dane potrzebne do synchronizacji ust.
- **Rozwój oprogramowania** opisuje budowanie kodu oraz obowiązującą terminologię.

Dokumenty historyczne, które nie opisują bieżącego procesu `piper-mat`, nie są utrzymywane w głównej dokumentacji.

## Najważniejsze katalogi

```text
configs/      konfiguracje eksperymentów
dataset/      metadane, nagrania i karta zbioru danych
docs/         dokumentacja projektu
models/       karty modeli
scripts/      narzędzia procesu treningowego i oceny
tests/        testy oraz korpus regresyjny
checkpoints/  kontrolowane punkty kontrolne
```

Duże artefakty nie powinny trafiać do historii Git bez uzasadnienia. Finalne modele powinny być dystrybuowane jako wersjonowane wydania lub przez repozytorium modeli.

## Standard terminologiczny

Dokumentacja jest prowadzona po polsku. Przy pierwszym użyciu specjalistycznego pojęcia podawana jest poprawna polska nazwa oraz angielski odpowiednik w nawiasie. Obowiązujące odpowiedniki znajdują się w [słowniku terminologii](TERMINOLOGIA.md).

Nazwy wymagane przez kod lub format, np. `batch_size`, `--checkpoint`, `ONNX`, `PyTorch` i `CUDA`, zachowują oryginalny zapis.

W dokumentacji nie stosuje się pauzy em (`—`).

## Standard kodu

Kod Pythona rozwijany w projekcie powinien przestrzegać PEP 8 i PEP 257.

Najważniejsze reguły nazewnictwa:

- funkcje, metody, zmienne i parametry: `snake_case`,
- klasy i wyjątki: `CapWords`,
- stałe modułu: `UPPER_CASE_WITH_UNDERSCORES`,
- moduły Pythona: małe litery, w razie potrzeby z podkreśleniami,
- opcje CLI: zapis zgodny z rzeczywistym interfejsem, często `kebab-case`.

`kebab-case` nie jest konwencją identyfikatorów Pythona.

Szczegółowe reguły dla zmian w repozytorium znajdują się w `AGENTS.md`.

## Zasady projektowe

W kodzie i dokumentacji obowiązuje zasada KISS. Należy preferować rozwiązania proste, jawne i możliwe do zweryfikowania.

Nie należy:

- utrzymywać dwóch dokumentów opisujących ten sam proces,
- kopiować informacji, które mają jedno kanoniczne źródło,
- pozostawiać nieaktualnych instrukcji jako aktywnej dokumentacji,
- dokumentować planowanej funkcji tak, jakby była już dostępna,
- wpisywać wartości szacunkowych jako wyniki pomiarów,
- zmieniać wielu parametrów eksperymentu bez zapisania nowej konfiguracji.

## Licencje

Kod odziedziczony po Piper podlega warunkom GPL-3.0-or-later. Licencja kodu nie określa automatycznie warunków wykorzystania zbioru danych ani wytrenowanego modelu głosu. Informacje te są dokumentowane osobno w kartach danych i modelu.
