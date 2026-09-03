# Wznowienie trenowania

## Definicja

Wznowienie trenowania (resume training) kontynuuje konkretny przebieg z zapisanego punktu kontrolnego wraz ze stanem potrzebnym do dalszej optymalizacji.

## Znaczenie w `piper-mat`

W `piper-mat` pozwala dzielić długie trenowanie na sesje i wyłączać komputer między nimi bez rozpoczynania przebiegu od nowa.

## Użycie w procesie

Menedżer sesji czyta `output/training_state/state.json`, wybiera `last.ckpt` poprzedniej sesji i odtwarza model, optymalizatory, harmonogramy oraz liczniki. Status można sprawdzić bez uruchamiania obliczeń.

## Parametry, jednostki i formaty

Istotne są numer sesji, epoka, krok, plan `epochs_per_session`, ścieżka `.ckpt` i spójna konfiguracja. Plik stanu ma format JSON.

## Praktyczne wartości i ich skutki

| Stan | Zachowanie następnego uruchomienia |
| --- | --- |
| Ukończono 0 z 4 sesji | Menedżer rozpoczyna pierwszą sesję od punktu bazowego. |
| Ukończono 2 z 4 sesji | Wybiera `session_02/last.ckpt` i planuje sesję trzecią. |
| Ukończono 4 z 4 sesji | Plan nie zawiera kolejnej sesji; potrzebna jest świadoma zmiana konfiguracji. |

Jeśli sesja zaczęła się od epoki 2 164 i ma dodać 250 epok, jej cel wynosi 2 414 epok. Nie należy ustawiać celu na `250`, ponieważ byłby niższy od stanu początkowego.

## Przykład z repozytorium

```bash
./train.sh --status
./train.sh
```

## Typowe błędy interpretacyjne

- Mylenie wznowienia z dostrajaniem nowego eksperymentu z samych parametrów bazowych.
- Ręczne wskazywanie przypadkowego punktu mimo istniejącego stanu sesji.
- Zmiana znaczenia eksperymentu podczas kontynuacji bez udokumentowania tego.

## Powiązane artykuły i procedury

- [Punkt kontrolny](punkt-kontrolny.md)
- [Trenowanie](trenowanie.md)
- [Procedura sesji](../STAGED_TRAINING.md)
- [Punkty kontrolne](../CHECKPOINTS.md)
