# Fonemizacja

## Definicja

Fonemizacja (phonemization) jest zamianą tekstu na reprezentację fonemiczną używaną przez model syntezy mowy.

## Znaczenie w `piper-mat`

W `piper-mat` łączy polski tekst z wejściem modelu. Konfiguracja `data.espeak_voice` wybiera reguły eSpeak NG, dlatego zmiana tego ustawienia może zmienić wymowę i identyfikatory wejściowe.

## Użycie w procesie

Fonemizacja zachodzi podczas przygotowania przykładów treningowych oraz wnioskowania. Te same zasady powinny obowiązywać w obu procesach. Wynik może następnie służyć do wyznaczenia czasów fonemów.

## Parametry, jednostki i formaty

Najważniejsze są język głosu `pl`, alfabet fonemiczny używany przez eSpeak NG oraz mapowanie symboli na całkowitoliczbowe identyfikatory fonemów. Tekst wejściowy jest zwykle zapisany w UTF-8.

## Praktyczne wartości i ich skutki

| Ustawienie lub tekst | Praktyczny skutek |
| --- | --- |
| `data.espeak_voice=pl` | Stosowane są reguły wymowy języka polskiego wymagane przez bieżący eksperyment. |
| `data.espeak_voice=en-us` | Ten sam zapis może otrzymać angielską wymowę; nie jest to zamiennik wartości `pl`. |
| `123` i `sto dwadzieścia trzy` | Po normalizacji mogą prowadzić do podobnej wymowy, ale przed fonemizacją są innymi zapisami wejściowymi. |

Przy zmianie głosu eSpeak NG należy ponownie przygotować pamięć podręczną i traktować wynik jako nowy eksperyment.

## Przykład z repozytorium

```bash
python -m piper.train fit \
  --data.espeak_voice pl \
  --data.csv_path dataset/metadata.csv \
  --data.audio_dir dataset/wavs
```

## Typowe błędy interpretacyjne

- Utożsamianie znaku, litery, fonemu i identyfikatora fonemu.
- Zmiana fonemizatora tylko dla wdrożenia, bez zachowania ustawień trenowania.
- Traktowanie fonemizacji jako rozpoznawania mowy.

## Powiązane artykuły i procedury

- [Dopasowanie fonemów](dopasowanie-fonemow.md)
- [Trenowanie](trenowanie.md)
- [Dopasowania w integracji](../ALIGNMENTS.md)
- [Podstawy trenowania](../TRAINING.md)
