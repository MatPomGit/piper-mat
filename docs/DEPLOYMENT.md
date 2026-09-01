# Wdrożenie modelu głosu

Wdrożenie (deployment) jest procesem przeniesienia zweryfikowanego modelu z etapu eksperymentalnego do środowiska, w którym będzie wykonywana rzeczywista synteza mowy. Obejmuje sprawdzenie integralności artefaktów, konfigurację usługi, test funkcjonalny, pomiar wydajności i przygotowanie możliwości wycofania wersji.

Ten rozdział opisuje wdrożenie `pl_PL-mateusz-medium` po przygotowaniu kompletnego wydania modelu.

## Wymagane artefakty

Minimalny zestaw wykonawczy:

```text
pl_PL-mateusz-medium.onnx
pl_PL-mateusz-medium.onnx.json
```

W paczce wydania powinny znajdować się również karta modelu, manifest, sumy kontrolne i reprezentatywne próbki. Ich przygotowanie opisano w [RELEASES.md](RELEASES.md).

Model ONNX i konfiguracja JSON stanowią jedną wersjonowaną całość. Nie należy łączyć plików pochodzących z różnych wydań.

## Weryfikacja przed wdrożeniem

Przed instalacją należy:

1. sprawdzić SHA-256,
2. potwierdzić zgodność modelu i konfiguracji,
3. wykonać podstawowy test poprawności (smoke test),
4. wykonać syntezę zdań regresyjnych,
5. zapisać identyfikator wdrażanego wydania.

Przykład:

```bash
python scripts/smoke_test_voice.py \
  --model pl_PL-mateusz-medium.onnx
```

Aktualne argumenty skryptu należy w razie potrzeby sprawdzić przez `--help`.

## Test przez CLI

Interfejs wiersza poleceń (command-line interface, CLI) jest najprostszą metodą niezależnego sprawdzenia modelu przed uruchomieniem go jako usługi.

```bash
piper \
  --model pl_PL-mateusz-medium.onnx \
  --output-file test.wav \
  -- "To jest test polskiego głosu."
```

Pythonowy CLI Pipera akceptuje obecnie zarówno `--output-file`, jak i zgodnościowy alias `--output_file`. W dokumentacji należy preferować kanoniczną postać `--output-file`. Wewnętrzna zmienna Pythona pozostaje zapisana jako `output_file` zgodnie z `snake_case`.

Szczegóły CLI znajdują się w [CLI.md](CLI.md).

## Wyoming Piper i Home Assistant

Wyoming Piper utrzymuje model w procesie usługi, dzięki czemu nie trzeba wczytywać go ponownie dla każdej wypowiedzi.

Przykładowy katalog głosu:

```text
/srv/piper/voices/
├── pl_PL-mateusz-medium.onnx
└── pl_PL-mateusz-medium.onnx.json
```

Jeżeli usługa nie musi modyfikować modelu, katalog powinien być montowany tylko do odczytu.

Walidację integracji należy wykonywać warstwowo:

1. sprawdzić proces Wyoming Piper,
2. sprawdzić osiągalność usługi,
3. sprawdzić wykrywanie usługi przez Home Assistant,
4. sprawdzić dostępność `pl_PL-mateusz-medium`,
5. wykonać krótką syntezę,
6. sprawdzić przekazanie dźwięku do odtwarzacza,
7. sprawdzić początek i koniec wypowiedzi,
8. zmierzyć całkowite opóźnienie.

Sekrety i tokeny integracji nie mogą być przechowywane w repozytorium.

## Opóźnienie końcowe

Opóźnienie końcowe (end-to-end latency) oznacza czas od wysłania żądania do rozpoczęcia słyszalnego odtwarzania. Obejmuje więcej niż samo wnioskowanie modelu.

Wpływają na nie między innymi fonemizacja, synteza, buforowanie, sieć, warstwa Home Assistant i urządzenie odtwarzające.

Dlatego obok współczynnika czasu rzeczywistego (Real-Time Factor, RTF) warto mierzyć czas do pierwszego fragmentu dźwięku oraz całkowite opóźnienie systemu.

## Obcinanie początku wypowiedzi

Jeżeli urządzenie odtwarzające potrzebuje czasu na rozpoczęcie reprodukcji, pierwsze głoski mogą zostać utracone. Nie jest to automatycznie wada modelu TTS.

Rozwiązaniem na poziomie integracji może być dodanie krótkiego odcinka ciszy przed wypowiedzią. Jego długość należy dobrać pomiarowo dla konkretnego toru odtwarzania, zamiast wpisywać jedną wartość jako uniwersalny parametr modelu.

## Aktualizacja

Nową wersję należy wdrażać jako kompletny zestaw artefaktów:

1. pobrać wydanie,
2. zweryfikować sumy kontrolne,
3. wykonać lokalny test poprawności,
4. zachować poprzednią wersję,
5. podmienić model i konfigurację,
6. uruchomić usługę,
7. wykonać test funkcjonalny,
8. zmierzyć RTF i opóźnienie,
9. sprawdzić odtwarzanie docelowe,
10. zaakceptować wdrożenie dopiero po zakończeniu walidacji.

## Wycofanie wersji

Wycofanie wersji (rollback) oznacza powrót do poprzedniego, znanego i poprawnie działającego wydania.

Należy je wykonać, jeżeli nowy model powoduje istotną regresję zrozumiałości, podobieństwa głosu, wymowy, stabilności, wydajności albo kompatybilności integracyjnej.

Poprzednie artefakty należy zachować co najmniej do zakończenia testów nowej wersji. Przyczynę wycofania trzeba powiązać z konkretnym wydaniem.

## Monitorowanie

Monitorowanie (monitoring) powinno być proporcjonalne do środowiska. Warto obserwować:

- dostępność usługi,
- czas odpowiedzi,
- błędy syntezy,
- zużycie pamięci RAM,
- użycie CPU lub GPU,
- nietypowo długie żądania.

Nie ma potrzeby budowania rozbudowanego systemu obserwowalności, jeżeli prostszy mechanizm dostarcza informacji potrzebnych do utrzymania usługi.

## Bezpieczeństwo

Jeżeli Piper jest potrzebny wyłącznie w zaufanej sieci lokalnej, nie należy bezpośrednio udostępniać jego portu w Internecie.

Należy ograniczyć dostęp sieciowy, przechowywać sekrety poza repozytorium, stosować minimalne wymagane uprawnienia i montować artefakty modelu tylko do odczytu, jeżeli jest to możliwe.

## Kryterium zakończenia wdrożenia

Wdrożenie jest zakończone, gdy integralność artefaktów została potwierdzona, model przechodzi test poprawności, usługa uruchamia się powtarzalnie, aplikacja docelowa może wykonać syntezę, dźwięk jest poprawnie odtwarzany, zmierzono podstawową wydajność i sprawdzono procedurę powrotu do poprzedniej wersji.
