# Roadmap piper-mat

Repozytorium ma już podstawową strukturę powtarzalnego projektu głosu `pl_PL-mateusz-medium`. Poniżej rozdzielono elementy wdrożone od prac wymagających rzeczywistych danych pomiarowych lub finalnego modelu.

## Zrealizowane

- [x] uporządkowanie repozytorium jako forka Piper do treningu własnego głosu,
- [x] usunięcie konfliktującej deklaracji licencji MIT dla kodu pochodzącego z Piper GPL,
- [x] wersjonowana konfiguracja eksperymentu,
- [x] walidator `metadata.csv` i parametrów WAV,
- [x] analiza PCM16: czas nagrań, RMS, peak, clipping, udział ciszy i pliki nieujęte w metadata,
- [x] deterministyczny generator train/validation/test ze stałym seed i SHA-256 metadata,
- [x] zamrożony korpus zdań regresyjnych dla języka polskiego,
- [x] smoke test polskiej fonemizacji przez eSpeak NG,
- [x] kalkulator WER/CER,
- [x] smoke test finalnej pary ONNX/JSON przez rzeczywistą syntezę Piper,
- [x] `DATASET_CARD.md` i `MODEL_CARD.md`,
- [x] dokument protokołu ewaluacji,
- [x] manifest znanych checkpointów z SHA-256 i rozmiarem,
- [x] walidator checkpointu obsługujący plik rzeczywisty i wskaźnik Git LFS,
- [x] generator paczki wydania z `checksums.txt` i `release-manifest.json`,
- [x] poprawiona struktura MkDocs z `docs_dir: docs`,
- [x] CI sprawdzające strukturę, metadata, reprodukowalność splitu, checkpoint, polską fonemizację, evaluator i MkDocs,
- [x] aktualizacja GitHub Actions do wersji opartych na Node 24.

## P0. Dataset i trening

1. Uruchomić pełny `scripts/validate_dataset.py` bez `--skip-audio` na finalnym zbiorze i przeanalizować wszystkie ostrzeżenia dotyczące clippingu, ciszy, poziomu RMS i długości segmentów.
2. Uruchomić `scripts/create_splits.py` na finalnej wersji metadata i **commitować `dataset/splits.json` dopiero po zamrożeniu datasetu**.
3. Uzupełnić `DATASET_CARD.md` o faktyczny czas nagrań, liczbę segmentów, sprzęt, preprocessing, metodę transkrypcji i licencję danych.
4. Uzupełnić `checkpoints/manifest.json` o zweryfikowane źródło aktywnego checkpointu. SHA-256 i rozmiar aktualnych obiektów są już zapisane.
5. Ustalić finalny seed i wszystkie parametry produkcyjnego treningu.
6. Po każdym eksporcie uruchamiać `scripts/smoke_test_voice.py` na finalnym `pl_PL-mateusz-medium.onnx`.

## P1. Ewaluacja jakości

1. Wygenerować mowę dla zamrożonego splitu testowego i `tests/polish_sentences.txt`.
2. Uruchomić niezależny ASR i policzyć WER/CER przez `scripts/evaluate_transcripts.py`.
3. Dodać speaker similarity z ustalonym modelem speaker-embedding.
4. Przeprowadzić ślepy odsłuch MOS lub CMOS zgodnie z `docs/EVALUATION.md`.
5. Zmierzyć RTF, latency, RAM i CPU na x86-64 oraz Raspberry Pi 5.
6. Zapisywać wyniki kolejnych wersji w `evaluations/` wraz z metadanymi środowiska.

## P1. Polska fonemizacja

CI sprawdza obecnie, czy wszystkie zdania z korpusu regresyjnego są poprawnie fonemizowane przez polski głos eSpeak NG. Kolejny etap to przypięcie konkretnej wersji eSpeak NG i zapisanie oczekiwanych sekwencji fonemów dla wybranych zdań.

Nie należy zamrażać oczekiwanych fonemów przed przypięciem wersji eSpeak NG, ponieważ aktualizacja upstreamu może celowo zmieniać wymowę.

## P1. Artefakty i reprodukowalność

1. Po ustaleniu pierwotnego źródła checkpointu dodać bezpieczne pobieranie z URL wskazanego w `checkpoints/manifest.json`.
2. Zapisywać wersje Python, PyTorch, Lightning, CUDA, Piper i eSpeak NG w rekordzie eksperymentu.
3. Usunąć niepotrzebne warianty checkpointów i duże modele bazowe z głównego drzewa po zapewnieniu stabilnego źródła pobierania.
4. Publikować finalne modele przez GitHub Releases lub Hugging Face zamiast jako zwykłe commity.
5. Rozważyć podpisywanie manifestów wydania po ustabilizowaniu procesu publikacji.

## P2. Publikacja modelu

1. Uzupełnić `MODEL_CARD.md` rzeczywistymi parametrami i wynikami.
2. Ustalić osobno licencję datasetu i finalnego modelu głosu.
3. Opublikować stały zestaw próbek porównawczych.
4. Dodać instrukcję instalacji modelu w Piper, Wyoming Piper i Home Assistant.
5. Uruchamiać `scripts/package_release.py` dla każdego kandydata do wydania i publikować wynik dopiero po smoke teście i ewaluacji.

## Kryterium wydania v1.0

Wydanie `pl_PL-mateusz-medium` można oznaczyć jako stabilne, gdy:

- dataset przechodzi pełną walidację sygnału,
- `dataset/splits.json` jest zamrożony i zgodny z SHA-256 metadata,
- trening można odtworzyć z wersjonowanej konfiguracji i wskazanego checkpointu,
- finalny ONNX przechodzi smoke test,
- dostępne są WER/CER, speaker similarity i benchmark Raspberry Pi 5/x86-64,
- `DATASET_CARD.md` i `MODEL_CARD.md` nie zawierają niewypełnionych danych krytycznych,
- licencje datasetu oraz modelu są jednoznaczne,
- opublikowana paczka zawiera checksumy i próbki audio.
