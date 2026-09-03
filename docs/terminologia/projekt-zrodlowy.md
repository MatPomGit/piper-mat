# Projekt źródłowy

## Definicja

Projekt źródłowy (upstream) jest repozytorium lub projektem, z którego pochodzi rozwijany kod i do którego można przekazywać ogólne poprawki.

## Znaczenie w `piper-mat`

`piper-mat` rozwija Piper do konkretnego polskiego głosu. Rozróżnienie pomaga ustalić, czy zmiana jest lokalną konfiguracją projektu, czy poprawką użyteczną dla wszystkich użytkowników Pipera.

## Co zmienia w praktyce

Projekt źródłowy identyfikuje się adresem repozytorium, rewizją Git i wersją. Praktycznie zapis skrótu zatwierdzenia, na przykład 7 do 40 znaków, pozwala odtworzyć użyty kod.

## Przykład z repozytorium

Polecenie `git remote -v` pokazuje skonfigurowane zdalne repozytoria, a `git rev-parse HEAD` bieżącą rewizję.

## Typowe błędy interpretacyjne

Nie oznacza automatycznie gałęzi `main` ani najnowszego wydania. Lokalna kopia może być wiele rewizji za projektem źródłowym.

## Powiązane artykuły i procedury

[Wydanie](wydanie.md), [budowanie](../BUILDING.md), [strona projektu](../index.md).
