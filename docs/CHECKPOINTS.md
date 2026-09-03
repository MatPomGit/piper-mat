# Punkty kontrolne modelu

[Punkt kontrolny (checkpoint)](terminologia/punkt-kontrolny.md) jest zapisem stanu modelu powstałym podczas trenowania. Może zawierać parametry sieci, a zależnie od sposobu zapisu również stan optymalizatora, harmonogramu współczynnika uczenia i inne informacje potrzebne do wznowienia trenowania.

Punkty kontrolne są dużymi artefaktami binarnymi. Nie należy traktować ich tak samo jak kodu źródłowego ani tworzyć wielu nieopisanych kopii o nazwach typu `final2.ckpt` lub `fixed_new.ckpt`.

## Rola bazowego punktu kontrolnego

[Dostrajanie (fine-tuning)](terminologia/dostrajanie.md) rozpoczyna trenowanie od parametrów istniejącego modelu zamiast od losowej inicjalizacji. Pozwala wykorzystać reprezentacje mowy wyuczone wcześniej i zwykle znacząco skraca proces uzyskiwania użytecznego modelu.

Bazowy punkt kontrolny nie musi reprezentować tego samego mówcy. Musi natomiast być technicznie zgodny z konfiguracją modelu, którą zamierzamy dostrajać.

## Aktywny bazowy punkt kontrolny

Aktywny `base.ckpt` został zidentyfikowany jako publiczny punkt kontrolny `en_US-lessac-medium`:

```text
epoch=2164-step=1355540.ckpt
```

Zweryfikowane dane:

- SHA-256: `ab7e5b8dab40f834b7cc58ae4ad7b7009c954b901e4ddbb784bbe11ce379a1cd`,
- rozmiar: `845898328` bajtów,
- rewizja źródłowa: `19ca249c3d7c490dbbefbaf775f74df10681d9a4`.

Dane identyfikacyjne są zapisane w `checkpoints/manifest.json`. Manifest jest źródłem prawdy dla automatycznego pobierania i weryfikacji artefaktu.

## Dlaczego używamy SHA-256

Suma kontrolna SHA-256 jest skrótem kryptograficznym zawartości pliku. Jeżeli choć część pliku ulegnie zmianie, obliczona suma z bardzo dużym prawdopodobieństwem będzie inna.

W tym projekcie SHA-256 służy do potwierdzenia, że dwie osoby lub dwa środowiska rzeczywiście używają tego samego punktu kontrolnego. Sama zgodność nazwy pliku nie jest wystarczająca.

## Pobieranie

Bazowy punkt kontrolny można pobrać na podstawie manifestu:

```bash
python scripts/download_checkpoint.py base.ckpt
```

Skrypt powinien najpierw zapisać dane do pliku tymczasowego, następnie sprawdzić rozmiar i SHA-256, a dopiero po poprawnej weryfikacji zastąpić plik docelowy. Zapobiega to pozostawieniu częściowo pobranego pliku pod prawidłową nazwą.

## Weryfikacja istniejącego pliku

```bash
python scripts/verify_checkpoint.py checkpoints/base.ckpt
```

Weryfikację należy wykonywać między innymi po ręcznym kopiowaniu artefaktu, odtworzeniu go z kopii zapasowej lub przeniesieniu środowiska treningowego na inną maszynę.

Skrypt rozpoznaje również wskaźnik Git LFS. Wskaźnik Git LFS (Git LFS pointer) jest małym plikiem tekstowym opisującym duży artefakt przechowywany poza zwykłą historią Git. Nie jest właściwym punktem kontrolnym i nie może zostać przekazany do procesu trenowania jako model.

## Punkt kontrolny a wznowienie trenowania

Należy rozróżnić dwa przypadki:

1. **dostrajanie z modelu bazowego**, gdy wykorzystujemy parametry istniejącego modelu jako punkt startowy nowego eksperymentu,
2. **[wznowienie trenowania (resume training)](terminologia/wznowienie-trenowania.md)**, gdy kontynuujemy konkretny wcześniejszy przebieg wraz z jego zapisanym stanem.

Rozróżnienie jest ważne dla powtarzalności eksperymentów. Samo wskazanie pliku `.ckpt` nie opisuje jeszcze intencji jego użycia.

Proces trenowania etapowego opisano w [STAGED_TRAINING.md](STAGED_TRAINING.md).

## Nazewnictwo wynikowych punktów kontrolnych

Automatycznie tworzone nazwy zawierające epokę i krok, np.:

```text
epoch=0123-step=045678.ckpt
```

są bardziej informacyjne niż ręczne nazwy typu `best_final.ckpt`. Jeżeli dodatkowo wybierany jest „najlepszy” model według konkretnej metryki, kryterium wyboru powinno być zapisane w konfiguracji lub raporcie eksperymentu.

Nie należy zakładać, że punkt kontrolny z ostatniej epoki jest automatycznie najlepszym modelem.

## Warianty historyczne

`base_clean.ckpt`, `base_fixed.ckpt` i `base_win.ckpt` powstały podczas lokalnych prac nad zgodnością środowisk. Nie należy traktować ich jako niezależnych modeli bazowych bez udokumentowania:

- źródła,
- wykonanej transformacji,
- przyczyny utworzenia,
- SHA-256 przed i po transformacji,
- potwierdzenia, że zmiana była konieczna.

Jeżeli aktywny `base.ckpt` umożliwia powtarzalne trenowanie, zbędne warianty należy usunąć z bieżącego drzewa repozytorium. Czyszczenie historycznych obiektów Git LFS jest osobną operacją i nie jest konieczne do codziennej pracy z projektem.

## Zasady dla nowych punktów kontrolnych

Dla każdego punktu kontrolnego używanego jako istotny artefakt eksperymentu należy zachować co najmniej:

- jego rolę,
- pochodzenie,
- SHA-256,
- rozmiar,
- powiązaną konfigurację,
- wersję kodu,
- informację, czy służy do dostrajania, wznowienia czy eksportu modelu.

Pozwala to uniknąć sytuacji, w której model działa, ale nie można później ustalić, z jakiego stanu został utworzony.
