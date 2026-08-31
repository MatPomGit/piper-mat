# Roadmap piper-mat

Dokument opisuje dalsze prace konieczne do przekształcenia repozytorium w powtarzalny i dobrze udokumentowany projekt polskiego głosu Piper.

## P0. Stabilizacja procesu treningu

1. **Zweryfikować pełny dataset.** Rozszerzyć `scripts/validate_dataset.py` o pomiar peak/RMS, clippingu, udziału ciszy i rozkładu długości. Dodać kontrolę zgodności plików znajdujących się w `wavs/`, ale nieobecnych w `metadata.csv`.
2. **Utworzyć trwały podział train/validation/test.** Podział powinien używać stałego seed i być wersjonowany, aby kolejne eksperymenty były porównywalne.
3. **Uzupełnić `DATASET_CARD.md`.** Wpisać faktyczny czas datasetu, liczbę segmentów, sprzęt, źródła nagrań, preprocessing, metodę transkrypcji i licencję.
4. **Ustalić checkpoint bazowy.** Zapisać jego źródło, wersję i SHA-256. Nie wersjonować dużego checkpointu w zwykłym Git.
5. **Ustalić seed i pełne parametry eksperymentu.** Zaktualizować `configs/pl_PL-mateusz-medium.json` po wybraniu konfiguracji produkcyjnej.
6. **Dodać automatyczny smoke test eksportowanego ONNX.** Test powinien ładować model i konfigurację, syntetyzować krótkie polskie zdanie i potwierdzać powstanie niepustego audio.

## P1. Ewaluacja jakości

1. Przygotować zamrożony zestaw zdań testowych dla języka polskiego.
2. Wyznaczać WER i CER przez niezależny system ASR dla syntetyzowanych zdań.
3. Dodać speaker similarity na podstawie embeddingów mówcy.
4. Przygotować prosty protokół odsłuchowy MOS lub CMOS.
5. Raportować RTF, czas pierwszego audio, RAM i CPU na x86-64 oraz Raspberry Pi 5.
6. Zapisywać wyniki każdego modelu w wersjonowanym pliku, np. `evaluations/<version>.json`.

## P1. Reprodukowalność i CI

1. Rozszerzyć CI o testy jednostkowe po ustabilizowaniu zależności kompilacyjnych Pipera.
2. Dodać testy regresyjne polskiej fonemizacji oparte na eSpeak NG.
3. Sprawdzać zgodność par `.onnx` i `.onnx.json` w artefaktach wydania.
4. Generować `checksums.txt` dla publicznych artefaktów.
5. Zapisywać wersje Python, PyTorch, Lightning, CUDA, Piper i eSpeak NG w raporcie eksperymentu.

## P1. Porządkowanie artefaktów

1. Usunąć duże modele bazowe z głównego drzewa repozytorium po zapewnieniu ich stabilnego źródła pobierania.
2. Nie dodawać kolejnych checkpointów ani finalnych ONNX bezpośrednio do historii Git.
3. Publikować finalne modele przez GitHub Releases lub Hugging Face.
4. Dodać skrypt pobierający wskazany checkpoint bazowy i weryfikujący SHA-256.

## P2. Publikacja modelu

1. Uzupełnić `models/pl_PL-mateusz-medium/MODEL_CARD.md` faktycznymi parametrami i wynikami.
2. Ustalić licencję datasetu i osobno licencję modelu.
3. Opublikować stały zestaw próbek porównawczych.
4. Dodać instrukcję instalacji głosu w Piper, Wyoming Piper i Home Assistant.
5. Zautomatyzować tworzenie paczki wydania zawierającej ONNX, JSON, model card, checksumy i próbki.

## P2. Testy języka polskiego

Zestaw regresyjny powinien obejmować co najmniej:

- polskie znaki diakrytyczne,
- liczby ujemne i dziesiętne,
- daty i godziny,
- jednostki SI,
- tytuły i skróty,
- adresy URL i e-mail,
- nazwiska i nazwy własne,
- zapożyczenia,
- interpunkcję,
- bardzo krótkie i długie wypowiedzi.

## Kryterium wydania v1.0 głosu

Pierwsze stabilne wydanie można uznać za gotowe, gdy jednocześnie:

- dataset przechodzi walidację bez błędów,
- train/validation/test są zamrożone,
- trening można odtworzyć z wersjonowanej konfiguracji,
- ONNX przechodzi smoke test,
- istnieją wyniki WER/CER, ocena podobieństwa oraz benchmark CPU/Raspberry Pi 5,
- `DATASET_CARD.md` i `MODEL_CARD.md` są kompletne,
- licencje datasetu i modelu są jednoznaczne,
- wydanie zawiera checksumy i próbki audio.
