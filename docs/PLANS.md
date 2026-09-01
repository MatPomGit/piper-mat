# Archiwalne plany projektu źródłowego

Ten dokument ma charakter historyczny. Zawierał krótkie plany odziedziczone z wcześniejszego etapu rozwoju projektu Piper i nie jest aktualnym planem rozwoju `piper-mat`.

Aktualne zadania, priorytety i kryteria ukończenia znajdują się w [ROADMAP.md](ROADMAP.md).

## Zachowane informacje historyczne

W odziedziczonym planie wskazywano dwa kierunki prac:

1. rozwój eksperymentalnej obsługi dopasowań fonemów do dźwięku,
2. migrację samodzielnego pliku wykonywalnego `piper.exe` do rozwiązania wykorzystującego `libpiper`.

Informacje te nie powinny być interpretowane jako otwarte zadania `piper-mat` bez ponownej weryfikacji aktualnego kodu projektu źródłowego.

## Dopasowania

Obsługa dopasowań jest obecnie istotna dla `piper-mat` przede wszystkim ze względu na planowaną synchronizację mowy z animacją twarzy. Aktualny opis znajduje się w [ALIGNMENTS.md](ALIGNMENTS.md), a zadania integracyjne są prowadzone w [ROADMAP.md](ROADMAP.md).

## `piper.exe`

Historyczna uwaga dotycząca migracji `piper.exe` nie jest zadaniem projektu głosu, dopóki nie zostanie wykazane, że brak tej funkcji blokuje trenowanie, ocenę, wydanie albo wdrożenie `pl_PL-mateusz-medium`.

Zgodnie z zasadą KISS nie należy przenosić do aktywnego planu prac odziedziczonych tylko dlatego, że występowały w starszej dokumentacji.
