# piper-mat

`piper-mat` jest gałęzią rozwojową Piper ukierunkowaną na przygotowanie, trenowanie (training), walidację i publikację polskiego głosu `pl_PL-mateusz-medium`.

Repozytorium obejmuje kod Pipera, konfigurację eksperymentu, metadane zbioru danych (dataset), walidację jakości danych, narzędzia do oceny (evaluation) oraz dokumentację procesu wydawania modelu.

## Standard dokumentacji

Dokumentacja projektu jest prowadzona po polsku. Przy pierwszym użyciu charakterystycznego terminu technicznego podawana jest jego polska nazwa oraz angielski odpowiednik w nawiasie. Obowiązujące tłumaczenia i zasady redakcyjne znajdują się w [słowniku terminologii](TERMINOLOGIA.md).

Nie należy tworzyć prostych kalek z języka angielskiego, jeżeli istnieje utrwalony lub trafniejszy polski odpowiednik techniczny. Przed wprowadzeniem nowego terminu należy sprawdzić słownik. Nowe pojęcie powinno zostać najpierw zdefiniowane i dodane do `TERMINOLOGIA.md`.

Nazwy techniczne wymagane przez kod, np. `batch_size`, `--checkpoint`, `ONNX`, `PyTorch` lub `CUDA`, pozostają bez zmian. Ich znaczenie jest jednak opisywane po polsku, np. „parametr `batch_size` określa rozmiar partii (batch size)”.

## Standard kodu

Kod Python rozwijany w projekcie powinien być zgodny z [PEP 8](https://peps.python.org/pep-0008/) oraz konwencją łańcuchów dokumentacyjnych (docstrings) określoną w [PEP 257](https://peps.python.org/pep-0257/).

PEP 8 określa przede wszystkim zasady formatowania, nazewnictwa, organizacji importów i czytelności kodu. PEP 257 określa sposób dokumentowania publicznych modułów, klas, funkcji i metod za pomocą docstringów.

W projekcie obowiązują ponadto następujące zasady:

- KISS (Keep It Simple, Stupid): wybieraj najprostsze rozwiązanie poprawnie realizujące wymagania;
- czytelność kodu ma pierwszeństwo przed jego nadmiernym skracaniem;
- funkcja lub klasa powinna mieć jasno określoną odpowiedzialność;
- unikaj przedwczesnej abstrakcji i generalizacji;
- ograniczaj powtórzenia, ale nie twórz sztucznych abstrakcji wyłącznie w celu usunięcia kilku podobnych wierszy;
- stosuj jednoznaczne nazwy opisujące znaczenie danych i operacji;
- ograniczaj efekty uboczne oraz zależności globalne;
- komentarze powinny wyjaśniać przyczynę decyzji lub nietrywialny kontekst, a nie powtarzać treść kodu;
- usuwaj martwy kod zamiast pozostawiać zakomentowane stare implementacje;
- zmiana zachowania programu powinna prowadzić do dodania lub aktualizacji odpowiednich testów;
- optymalizacje powinny wynikać z rzeczywistej potrzeby lub pomiarów.

Szczegółowe instrukcje dla agentów programistycznych i osób modyfikujących repozytorium znajdują się w pliku `AGENTS.md` w katalogu głównym.

## Główne obszary

- `dataset/` — metadane i karta zbioru danych,
- `configs/` — wersjonowana konfiguracja trenowania,
- `models/` — karta finalnego modelu,
- `scripts/` — walidacja, podziały danych, ocena i testy jakości,
- `tests/` — zamrożony korpus regresyjny języka polskiego,
- `docs/` — dokumentacja procesu badawczego i wdrożeniowego.

## Aktualny cel

Najbliższym celem jest uzyskanie powtarzalnego procesu:

`walidacja → podział danych → trenowanie → eksport → podstawowy test poprawności → ocena → pakowanie`.

Aktualny stan i pozostałe zadania są opisane w [planie rozwoju](ROADMAP.md).

## Licencja

Kod pochodzący z Piper jest udostępniany zgodnie z GPL-3.0-or-later. Licencje zbioru danych oraz finalnego modelu głosu należy traktować oddzielnie i wskazać w odpowiednich kartach artefaktów.
