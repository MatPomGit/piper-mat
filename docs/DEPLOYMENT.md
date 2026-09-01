# Wdrożenie modelu głosu

Wdrożenie (deployment) jest procesem przeniesienia zweryfikowanego modelu z etapu eksperymentalnego do środowiska, w którym będzie wykonywana rzeczywista synteza mowy. Obejmuje nie tylko skopiowanie plików, ale również sprawdzenie ich integralności, konfigurację usługi, test funkcjonalny, pomiar wydajności i przygotowanie możliwości wycofania wersji.

Ten rozdział opisuje wdrożenie `pl_PL-mateusz-medium` po przygotowaniu kompletnego wydania modelu.

## 1. Wymagane artefakty

Minimalny zestaw wykonawczy obejmuje:

```text
pl_PL-mateusz-medium.onnx
pl_PL-mateusz-medium.onnx.json
```

W wydaniu przeznaczonym do archiwizacji i dystrybucji powinny znaleźć się również:

```text
MODEL_CARD.md
checksums.txt
release-manifest.json
samples/
```

Model ONNX i jego konfiguracja JSON stanowią jedną wersjonowaną całość. Nie należy łączyć plików pochodzących z różnych eksperymentów lub wydań.

## 2. Weryfikacja przed wdrożeniem

Przed instalacją należy:

1. sprawdzić sumy kontrolne SHA-256,
2. potwierdzić zgodność modelu i konfiguracji,
3. wykonać podstawowy test poprawności (smoke test),
4. wykonać syntezę kilku zdań regresyjnych,
5. zapisać identyfikator wdrażanego wydania.

Podstawowy test modelu:

```bash
python scripts/smoke_test_voice.py \
  --model pl_PL-mateusz-medium.onnx
```

Dokładne argumenty należy sprawdzić przez `--help`, ponieważ skrypt jest częścią rozwijanego repozytorium.

## 3. Wdrożenie przez interfejs wiersza poleceń

Interfejs wiersza poleceń (command-line interface, CLI) jest najprostszą metodą weryfikacji modelu przed uruchomieniem go jako usługi.

Przykład:

```bash
piper \
  --model pl_PL-mateusz-medium.onnx \
  --output_file test.wav \
  -- "To jest test polskiego głosu."
```

Nazwa `--output_file` musi odpowiadać rzeczywistemu interfejsowi używanej wersji Pipera. Nie należy zmieniać istniejącej nazwy opcji tylko po to, aby dopasować ją do konwencji dokumentacji. Opcje CLI są zewnętrznym interfejsem programu, a nie identyfikatorami Pythona.

Jeżeli dana wersja programu używa innej nazwy opcji, źródłem prawdy jest:

```bash
piper --help
```

## 4. Wyoming Piper

Wyoming jest protokołem używanym między innymi do komunikacji usług głosowych z Home Assistant. Wyoming Piper utrzymuje model w procesie usługi, dzięki czemu nie trzeba ponownie wczytywać go dla każdej wypowiedzi.

W środowisku kontenerowym katalog z modelem i konfiguracją należy montować jako wolumin tylko do odczytu, jeżeli usługa nie musi modyfikować tych plików.

Przykładowy układ:

```text
/srv/piper/voices/
├── pl_PL-mateusz-medium.onnx
└── pl_PL-mateusz-medium.onnx.json
```

Po uruchomieniu lub restarcie usługi należy najpierw wykonać lokalny test syntezy. Dopiero później należy diagnozować integrację z kolejnymi warstwami systemu.

## 5. Home Assistant

Home Assistant powinien korzystać z Pipera przez integrację Wyoming. Dane uwierzytelniające, tokeny i inne sekrety nie mogą być przechowywane w repozytorium `piper-mat`.

Walidację integracji należy wykonywać warstwowo:

1. sprawdzić, czy proces Wyoming Piper działa,
2. sprawdzić, czy port usługi jest osiągalny z Home Assistant,
3. sprawdzić, czy Home Assistant wykrywa usługę,
4. sprawdzić dostępność `pl_PL-mateusz-medium`,
5. wykonać syntezę krótkiego zdania,
6. sprawdzić przekazanie wygenerowanego dźwięku do odtwarzacza,
7. sprawdzić początek i koniec wypowiedzi,
8. zmierzyć całkowite opóźnienie od żądania do rozpoczęcia odtwarzania.

Takie rozdzielenie diagnostyki pozwala ustalić, czy problem występuje w modelu TTS, usłudze Wyoming, Home Assistant, sieci czy urządzeniu odtwarzającym.

## 6. Opóźnienie końcowe

Opóźnienie końcowe (end-to-end latency) oznacza czas od wysłania żądania syntezy do momentu, w którym użytkownik rzeczywiście zaczyna słyszeć wypowiedź. Nie jest ono równe samemu czasowi wnioskowania modelu.

Na opóźnienie mogą wpływać:

- przygotowanie tekstu,
- fonemizacja,
- wnioskowanie modelu,
- buforowanie dźwięku,
- komunikacja sieciowa,
- Home Assistant,
- inicjalizacja odtwarzacza,
- buforowanie po stronie urządzenia docelowego.

Dlatego obok współczynnika czasu rzeczywistego (Real-Time Factor, RTF) warto mierzyć również czas do pierwszego fragmentu dźwięku i całkowite opóźnienie systemu.

## 7. Problem obcinania początku wypowiedzi

Niektóre urządzenia odtwarzające mogą rozpocząć słyszalne odtwarzanie z opóźnieniem względem rozpoczęcia strumienia. W efekcie pierwsze głoski wypowiedzi mogą zostać obcięte.

Nie należy naprawiać tego problemu przez zmianę modelu TTS, jeżeli źródłem jest tor odtwarzania. Rozwiązaniem może być kontrolowane dodanie krótkiego odcinka ciszy przed właściwą wypowiedzią w warstwie integracyjnej.

Długość takiego odcinka należy dobrać eksperymentalnie dla konkretnego urządzenia. Powinna być możliwie mała, ale wystarczająca do stabilnego rozpoczęcia odtwarzania.

## 8. Aktualizacja modelu

Nową wersję należy wdrażać jako kompletny zestaw artefaktów.

Zalecana procedura:

1. pobrać nowe wydanie,
2. zweryfikować `checksums.txt`,
3. wykonać lokalny podstawowy test poprawności,
4. wykonać próbki regresyjne,
5. zachować poprzednią wersję,
6. zatrzymać lub przełączyć usługę w kontrolowany sposób,
7. podmienić model i konfigurację,
8. uruchomić usługę,
9. wykonać test funkcjonalny,
10. zmierzyć RTF i opóźnienie,
11. sprawdzić integrację z docelowym odtwarzaczem,
12. oznaczyć wdrożenie jako zaakceptowane dopiero po zakończeniu walidacji.

## 9. Wycofanie wersji

Wycofanie wersji (rollback) oznacza powrót do poprzedniego, znanego i poprawnie działającego wydania.

Procedura wycofania powinna być przygotowana przed aktualizacją. Poprzedni model i konfiguracja powinny pozostać dostępne do czasu zakończenia testów nowej wersji.

Wycofanie jest wymagane, jeżeli nowy model powoduje istotną regresję dotyczącą na przykład:

- zrozumiałości,
- podobieństwa głosu,
- wymowy języka polskiego,
- stabilności usługi,
- czasu odpowiedzi,
- zużycia zasobów,
- kompatybilności z integracją.

Po wycofaniu należy zapisać przyczynę i powiązać ją z konkretnym numerem wydania lub sumą kontrolną modelu.

## 10. Monitorowanie

Monitorowanie (monitoring) wdrożenia powinno obejmować co najmniej:

- dostępność procesu TTS,
- czas odpowiedzi,
- błędy syntezy,
- zużycie pamięci RAM,
- użycie CPU lub GPU,
- liczbę żądań,
- anomalie związane z wyjątkowo długimi tekstami.

W środowisku domowym nie ma potrzeby budowania rozbudowanej infrastruktury obserwowalności, jeżeli prostsze rozwiązanie dostarcza wystarczających informacji. Jest to zgodne z zasadą KISS.

## 11. Bezpieczeństwo

Usługa TTS powinna być dostępna tylko tam, gdzie jest potrzebna. Jeżeli Piper działa wyłącznie jako usługa dla Home Assistant w sieci lokalnej, nie ma uzasadnienia dla bezpośredniego wystawiania jego portu do Internetu.

Należy:

- ograniczyć dostęp sieciowy,
- przechowywać sekrety poza repozytorium,
- nie uruchamiać procesu z większymi uprawnieniami niż wymagane,
- montować artefakty modelu tylko do odczytu, jeżeli jest to możliwe,
- aktualizować zależności świadomie i testować zgodność po zmianie,
- wykonywać kopie konfiguracji potrzebnej do odtworzenia usługi.

## 12. Kryterium zakończenia wdrożenia

Wdrożenie można uznać za zakończone, gdy:

- integralność artefaktów została potwierdzona,
- model przechodzi podstawowy test poprawności,
- usługa uruchamia się powtarzalnie,
- synteza działa z docelowej aplikacji,
- dźwięk jest poprawnie odtwarzany na urządzeniu docelowym,
- zmierzono podstawowe parametry wydajności,
- nie występuje nieakceptowalna regresja jakości,
- istnieje sprawdzona procedura powrotu do poprzedniej wersji.
