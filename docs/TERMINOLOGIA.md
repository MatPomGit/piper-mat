# Terminologia projektu

Ten dokument jest normą redakcyjną dokumentacji projektu `piper-mat`. Dokumentację użytkową należy pisać po polsku, z wykorzystaniem poprawnej polskiej terminologii technicznej. Należy unikać dosłownych kalek językowych z angielskiego.

Przy pierwszym użyciu charakterystycznego pojęcia technicznego zaleca się podanie polskiej nazwy, a następnie angielskiego odpowiednika w nawiasie, np. **częstotliwość próbkowania (sample rate)**. W dalszej części tego samego dokumentu można używać samej nazwy polskiej, o ile nie prowadzi to do niejednoznaczności.

Nazwy parametrów programu, identyfikatorów, klas, funkcji, bibliotek, formatów i plików pozostają bez tłumaczenia i należy zapisywać je jako kod, np. `batch_size`, `--checkpoint`, `PyTorch`, `ONNX`.

## Słownik obowiązujących odpowiedników

| Termin angielski | Zalecany termin polski | Uwagi |
| --- | --- | --- |
| alignment | dopasowanie | W kontekście TTS oznacza powiązanie reprezentacji tekstowej lub fonemicznej z przebiegiem czasowym sygnału mowy. |
| batch | partia | Grupa próbek przetwarzanych w jednym kroku optymalizacji. |
| batch size | rozmiar partii | Liczba próbek w jednej partii. Nazwa parametru `batch_size` pozostaje bez zmian. |
| cache | pamięć podręczna | Nie używać kalki „cache” w zwykłym tekście. |
| checkpoint | punkt kontrolny | Zapis stanu modelu i, zależnie od mechanizmu treningu, również optymalizatora oraz harmonogramu uczenia. |
| clipping | przesterowanie | W odniesieniu do sygnału dźwiękowego. |
| checksum | suma kontrolna | Np. SHA-256. |
| command-line interface | interfejs wiersza poleceń | Skrót CLI można pozostawić po pierwszym rozwinięciu. |
| data loader | mechanizm wczytywania danych | W odniesieniu do klasy `DataLoader` pozostawić nazwę klasy bez tłumaczenia. |
| dataset | zbiór danych | Nie używać „dataset” w zwykłym tekście. |
| epoch | epoka | Jedno pełne przejście przez zbiór treningowy. |
| evaluation | ocena | W zależności od kontekstu dopuszczalne: „ewaluacja”, zwłaszcza w opisie eksperymentu. |
| fine-tuning | dostrajanie | Preferowane zamiast „fine-tuning” i „dostrojenie modelu”. |
| inference | wnioskowanie | Generowanie wyniku przez wytrenowany model. |
| learning rate | współczynnik uczenia | Nie używać kalki „tempo uczenia”. |
| loss | funkcja straty | Jeżeli omawiana jest jej wartość: „wartość funkcji straty”. |
| metadata | metadane | W liczbie mnogiej. |
| model warm start | inicjalizacja z parametrów modelu bazowego | W krótszym kontekście: „wstępna inicjalizacja”. |
| monitoring | monitorowanie | Preferowane w opisie procesu. |
| peak RAM usage | maksymalne użycie pamięci RAM | Zamiast „peak RAM”. |
| phonemization | fonemizacja | Zamiana tekstu na reprezentację fonemiczną. |
| real-time factor | współczynnik czasu rzeczywistego | Skrót RTF można stosować po pierwszym rozwinięciu. |
| release | wydanie | Dotyczy wydań programu lub modelu. |
| resume training | wznowienie trenowania | Nie używać „resume treningu”. |
| sample | próbka | W audio może oznaczać próbkę sygnału albo element zbioru danych, dlatego trzeba doprecyzować kontekst. |
| sample rate | częstotliwość próbkowania | Podawać w hercach, np. 22 050 Hz. |
| speaker embedding | reprezentacja wektorowa mówcy | Termin bardziej precyzyjny niż dosłowne „osadzenie mówcy”. |
| speaker similarity | podobieństwo głosu mówcy | W kontekście porównania głosu referencyjnego i syntetycznego. |
| split | podział zbioru danych | Np. podział na część treningową, walidacyjną i testową. |
| smoke test | podstawowy test poprawności | Nie używać kalki „test dymny”. |
| training | trenowanie | Dopuszczalne także „uczenie modelu”, gdy opis jest ogólny. |
| training set | zbiór treningowy | Część danych używana do aktualizacji parametrów modelu. |
| validation set | zbiór walidacyjny | Część danych używana do doboru modelu i kontroli przebiegu trenowania. |
| test set | zbiór testowy | Część danych przeznaczona do końcowej oceny. |
| upstream | projekt źródłowy | W kontekście repozytorium, z którego pochodzi rozwijany kod. |
| validation | walidacja | Kontrola na wydzielonym zbiorze danych lub kontrola poprawności artefaktu. |
| vocoder | wokoder | Utrwalony termin specjalistyczny. |
| voice model | model głosu | Model syntezy konkretnego głosu. |
| warm start | wstępna inicjalizacja | Gdy trzeba doprecyzować: „inicjalizacja z wcześniej wytrenowanych parametrów”. |

## Metryki i skróty

Przy pierwszym użyciu metryki należy podać jej polską nazwę oraz oryginalną nazwę angielską i skrót.

| Skrót | Zalecany zapis przy pierwszym użyciu |
| --- | --- |
| WER | współczynnik błędów słów (Word Error Rate, WER) |
| CER | współczynnik błędów znaków (Character Error Rate, CER) |
| MOS | średnia ocena opinii słuchaczy (Mean Opinion Score, MOS) |
| CMOS | porównawcza średnia ocena opinii słuchaczy (Comparative Mean Opinion Score, CMOS) |
| RTF | współczynnik czasu rzeczywistego (Real-Time Factor, RTF) |

## Nazwy pozostawiane w języku oryginalnym

Nie tłumaczy się nazw własnych, nazw bibliotek, formatów, standardów i identyfikatorów technicznych, m.in.:

- `Piper`, `eSpeak NG`, `PyTorch`, `PyTorch Lightning`, `CUDA`, `Cython`, `TensorBoard`,
- `ONNX`, `JSON`, `CSV`, `WAV`, `UTF-8`, `Git`, `Git LFS`, GitHub,
- nazw plików, katalogów, klas, funkcji i zmiennych,
- opcji wiersza poleceń, np. `--checkpoint`, `--sample-rate`, `--data.batch_size`,
- nazw pól konfiguracji, np. `epochs_per_session`, `val_mel`, `val_mos`.

Jeżeli taki identyfikator pojawia się w zdaniu opisowym, należy wyjaśnić jego znaczenie po polsku. Przykład: „parametr `batch_size` określa **rozmiar partii (batch size)**”.

## Konwencje nazewnicze kodu

W kodzie Pythona obowiązuje nazewnictwo zgodne z PEP 8.

- funkcje, metody, zmienne i parametry: `snake_case`, np. `load_voice_model`, `sample_rate`;
- klasy i wyjątki: `CapWords` / `PascalCase`, np. `VoiceModel`, `DatasetValidationError`;
- stałe modułu: `UPPER_CASE_WITH_UNDERSCORES`, np. `DEFAULT_SAMPLE_RATE`;
- moduły Pythona: małe litery, w razie potrzeby z podkreśleniami, np. `voice_export.py`;
- pakiety Pythona: krótkie nazwy zapisane małymi literami, z podkreśleniami tylko wtedy, gdy poprawiają czytelność i są rzeczywiście potrzebne;
- elementy przeznaczone do użytku wewnętrznego mogą mieć pojedyncze podkreślenie z przodu, np. `_load_metadata`.

`kebab-case`, np. `sample-rate`, nie jest konwencją identyfikatorów Pythona i nie wolno go stosować w nazwach funkcji, zmiennych, klas ani modułów importowanych w Pythonie.

`kebab-case` jest natomiast właściwy dla wielu opcji interfejsu wiersza poleceń, np. `--sample-rate`, `--output-file` lub `--data-dir`, jeżeli dokładnie tak definiuje je istniejący interfejs programu.

PEP 8 nie nakazuje stosowania `snake_case` ani `kebab-case` dla wszystkich plików repozytorium. Pliki niebędące modułami Pythona powinny zachowywać konwencję odpowiednią dla danego typu artefaktu, np. `README.md`, `AGENTS.md`, `MODEL_CARD.md`.

## Zasady redakcyjne

1. Najpierw używaj poprawnego terminu polskiego, a angielski odpowiednik podawaj w nawiasie przy pierwszym istotnym wystąpieniu.
2. Nie tłumacz nazw zmiennych ani opcji programu. Wyjaśniaj ich znaczenie po polsku.
3. Nie twórz kalk językowych, jeżeli w polskiej literaturze technicznej istnieje utrwalony odpowiednik.
4. Jeżeli pojęcie może mieć kilka znaczeń, doprecyzuj je w kontekście uczenia maszynowego, przetwarzania mowy lub inżynierii oprogramowania.
5. Nowe terminy wprowadzane do dokumentacji należy najpierw dopisać do tego słownika, a następnie konsekwentnie stosować w pozostałych plikach.
6. W dokumentach dydaktycznych nowe pojęcie powinno zostać krótko wyjaśnione przed opisem parametrów i procedur, które się do niego odnoszą.
7. Nie używaj pauzy em (em dash, `—`). Dobierz poprawny polski znak interpunkcyjny do funkcji składniowej zdania.
8. Zachowuj wielkość liter wymaganą przez kod, API, standard lub nazwę własną. Nie normalizuj samodzielnie zapisów takich jak `ONNX`, `CUDA`, `PiperVoice` czy `Git LFS`.
