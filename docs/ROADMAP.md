# Plan rozwoju piper-mat

Repozytorium ma już podstawową strukturę powtarzalnego projektu głosu `pl_PL-mateusz-medium`. Poniżej rozdzielono elementy wdrożone od prac wymagających rzeczywistych danych pomiarowych lub finalnego modelu.

## Zrealizowane

- [x] uporządkowanie repozytorium jako gałęzi rozwojowej Piper do treningu własnego głosu,
- [x] usunięcie konfliktującej deklaracji licencji MIT dla kodu pochodzącego z Piper GPL,
- [x] wersjonowana konfiguracja eksperymentu,
- [x] kanoniczna konfiguracja JSON rzeczywiście sterująca `train.sh`,
- [x] walidator `metadata.csv` i parametrów WAV,
- [x] analiza PCM16: czas nagrań, RMS, wartość szczytowa, przesterowanie, udział ciszy i pliki nieujęte w metadanych,
- [x] deterministyczny generator podziału na zbiory treningowy, walidacyjny i testowy ze stałym ziarnem losowania i SHA-256 metadanych,
- [x] zamrożony korpus zdań regresyjnych dla języka polskiego,
- [x] test poprawności polskiej fonemizacji przez eSpeak NG,
- [x] kalkulator WER/CER,
- [x] test poprawności finalnej pary ONNX/JSON przez rzeczywistą syntezę Piper,
- [x] `DATASET_CARD.md` i `MODEL_CARD.md`,
- [x] dokument protokołu ewaluacji,
- [x] manifest znanych punktów kontrolnych z SHA-256 i rozmiarem,
- [x] walidator punktu kontrolnego obsługujący plik rzeczywisty i wskaźnik Git LFS,
- [x] automatyczny rekord środowiska eksperymentu z wersjami oprogramowania i SHA-256 wejść,
- [x] powtarzalny benchmark RTF modelu Piper,
- [x] automatyczna kontrola minimalnej gotowości kandydata do wydania,
- [x] katalog i zasady wersjonowania wyników w `evaluations/`,
- [x] generator paczki wydania z `checksums.txt` i `release-manifest.json`,
- [x] instrukcja wdrożenia modelu do Piper, Wyoming Piper i Home Assistant,
- [x] poprawiona struktura MkDocs z `docs_dir: docs`,
- [x] ciągła integracja sprawdzająca strukturę, metadane, reprodukowalność podziału, punkt kontrolny, kanoniczne polecenie treningowe, rekord środowiska, polską fonemizację, ewaluator i MkDocs,
- [x] aktualizacja GitHub Actions do wersji opartych na Node 24,
- [x] ujednolicenie materiałów użytkowych i dokumentacji w języku polskim.

## P0. Zbiór danych i trening

1. Uruchomić pełny `scripts/validate_dataset.py` bez `--skip-audio` na finalnym zbiorze i przeanalizować wszystkie ostrzeżenia dotyczące przesterowania, ciszy, poziomu RMS i długości segmentów.
2. Uruchomić `scripts/create_splits.py` na finalnej wersji metadanych i **zatwierdzić `dataset/splits.json` w repozytorium dopiero po zamrożeniu zbioru danych**.
3. Uzupełnić `DATASET_CARD.md` o faktyczny czas nagrań, liczbę segmentów, sprzęt, sposób wstępnego przetwarzania, metodę transkrypcji i licencję danych.
4. Uzupełnić `checkpoints/manifest.json` o zweryfikowane źródło aktywnego punktu kontrolnego. SHA-256 i rozmiar aktualnych obiektów są już zapisane.
5. Ustalić finalne ziarno losowania oraz ewentualny limit epok w `configs/pl_PL-mateusz-medium.json`.
6. Po każdym eksporcie uruchamiać `scripts/smoke_test_voice.py` na finalnym `pl_PL-mateusz-medium.onnx`.

## P1. Ewaluacja jakości

1. Wygenerować mowę dla zamrożonego zbioru testowego i `tests/polish_sentences.txt`.
2. Uruchomić niezależny ASR i policzyć WER/CER przez `scripts/evaluate_transcripts.py`.
3. Dodać miarę podobieństwa głosu z ustalonym modelem osadzeń mówcy.
4. Przeprowadzić ślepy odsłuch MOS lub CMOS zgodnie z `docs/EVALUATION.md`.
5. Uruchomić `scripts/benchmark_voice.py` na x86-64 oraz Raspberry Pi 5 i zapisać wyniki w `evaluations/`.
6. Dla każdego eksperymentu zapisać środowisko przez `scripts/record_environment.py`.

## P1. Polska fonemizacja

Ciągła integracja sprawdza obecnie, czy wszystkie zdania z korpusu regresyjnego są poprawnie fonemizowane przez polski głos eSpeak NG. Kolejny etap to przypięcie konkretnej wersji eSpeak NG i zapisanie oczekiwanych sekwencji fonemów dla wybranych zdań.

Nie należy zamrażać oczekiwanych fonemów przed przypięciem wersji eSpeak NG, ponieważ aktualizacja projektu źródłowego może celowo zmieniać wymowę.

## P1. Artefakty i reprodukowalność

1. Po ustaleniu pierwotnego źródła punktu kontrolnego dodać bezpieczne pobieranie z adresu URL wskazanego w `checkpoints/manifest.json`.
2. Usunąć niepotrzebne warianty punktów kontrolnych i duże modele bazowe z głównego drzewa po zapewnieniu stabilnego źródła pobierania.
3. Publikować finalne modele jako wydania GitHub lub w serwisie Hugging Face zamiast jako zwykłe zatwierdzenia.
4. Rozważyć podpisywanie manifestów wydania po ustabilizowaniu procesu publikacji.

## P2. Publikacja modelu

1. Uzupełnić `MODEL_CARD.md` rzeczywistymi parametrami i wynikami.
2. Ustalić osobno licencję zbioru danych i finalnego modelu głosu.
3. Opublikować stały zestaw próbek porównawczych.
4. Uruchamiać `scripts/check_release_readiness.py` i `scripts/package_release.py` dla każdego kandydata do wydania.
5. Publikować dopiero kandydatów, którzy przechodzą test poprawności, ewaluację i kontrolę gotowości.

## Kryterium wydania v1.0

Wydanie `pl_PL-mateusz-medium` można oznaczyć jako stabilne, gdy:

- zbiór danych przechodzi pełną walidację sygnału,
- `dataset/splits.json` jest zamrożony i zgodny z SHA-256 metadanych,
- trening można odtworzyć z wersjonowanej konfiguracji i wskazanego punktu kontrolnego,
- finalny ONNX przechodzi test poprawności,
- dostępne są WER/CER, podobieństwo głosu i pomiary wydajności na Raspberry Pi 5 oraz x86-64,
- `DATASET_CARD.md` i `MODEL_CARD.md` nie zawierają niewypełnionych danych krytycznych,
- licencje zbioru danych oraz modelu są jednoznaczne,
- `scripts/check_release_readiness.py` kończy się powodzeniem,
- opublikowana paczka zawiera sumy kontrolne i próbki dźwięku.
