# Wydawanie modelu

Wydanie (release) jest identyfikowalnym zestawem artefaktów modelu przeznaczonym do dystrybucji, wdrożenia lub archiwizacji. Nie powinno być utożsamiane z dowolnym wyeksportowanym plikiem ONNX.

Celem procesu wydawania jest zapewnienie, że odbiorca może ustalić, jaki model otrzymał, zweryfikować integralność plików, poznać wyniki oceny i odtworzyć najważniejsze informacje o pochodzeniu modelu.

## 1. Kandydat do wydania

Kandydat do wydania (release candidate) jest modelem, który zakończył trenowanie i został wybrany do pełnej walidacji przed publikacją.

Nie należy wybierać kandydata wyłącznie na podstawie numeru epoki lub pojedynczej wartości funkcji straty. Decyzja powinna uwzędniać co najmniej poprawność techniczną, odsłuch, zrozumiałość i brak istotnych regresji.

## 2. Warunki rozpoczęcia procesu wydania

Przed przygotowaniem paczki należy mieć:

- wybrany i jednoznacznie zidentyfikowany punkt kontrolny,
- wyeksportowany model ONNX,
- odpowiadającą mu konfigurację JSON,
- zamrożony zbiór testowy,
- wyniki wymaganej oceny,
- uzupełnioną kartę modelu,
- określoną licencję modelu,
- znane pochodzenie zbioru danych i prawo do wykorzystania głosu.

Jeżeli brakuje krytycznych danych, artefakt może pozostać wynikiem eksperymentu, ale nie powinien być oznaczany jako stabilne wydanie.

## 3. Zawartość wydania

Minimalny pakiet powinien zawierać:

```text
pl_PL-mateusz-medium.onnx
pl_PL-mateusz-medium.onnx.json
MODEL_CARD.md
release-manifest.json
checksums.txt
samples/
```

### Model ONNX

`pl_PL-mateusz-medium.onnx` jest wykonawczym modelem sieci neuronowej.

### Konfiguracja JSON

`pl_PL-mateusz-medium.onnx.json` zawiera konfigurację potrzebną do poprawnego użycia modelu przez Pipera. Musi pochodzić z tego samego eksperymentu co ONNX.

### Karta modelu

`MODEL_CARD.md` opisuje pochodzenie, parametry, ocenę, ograniczenia i licencję modelu.

### Manifest wydania

Manifest wydania (release manifest) jest maszynowo czytelnym opisem zawartości paczki. Powinien umożliwiać automatyczne ustalenie, jakie artefakty należą do konkretnego wydania.

### Sumy kontrolne

`checksums.txt` przechowuje sumy SHA-256. Umożliwiają one sprawdzenie, czy pobrany plik jest identyczny z plikiem przygotowanym podczas wydania.

### Próbki

Katalog `samples/` powinien zawierać reprezentatywne próbki dźwięku. Nie należy wybierać wyłącznie wypowiedzi, dla których model osiąga wyjątkowo dobry wynik.

## 4. Przygotowanie paczki

Pakiet można przygotować skryptem:

```bash
python scripts/package_release.py \
  --model output/pl_PL-mateusz-medium.onnx \
  --config output/pl_PL-mateusz-medium.onnx.json \
  --samples samples/pl_PL-mateusz-medium \
  --output dist/pl_PL-mateusz-medium
```

Skrypt wymaga pustej, nieistniejącej ścieżki wyjściowej. Dzięki temu starsze pliki nie pozostają przypadkowo w nowej paczce i nie omijają manifestu.

Jeżeli katalog wyjściowy ma zostać świadomie zastąpiony, należy użyć:

```bash
python scripts/package_release.py \
  --model output/pl_PL-mateusz-medium.onnx \
  --config output/pl_PL-mateusz-medium.onnx.json \
  --samples samples/pl_PL-mateusz-medium \
  --output dist/pl_PL-mateusz-medium \
  --overwrite
```

Opcja `--overwrite` usuwa wyłącznie wskazany katalog `--output` przed utworzeniem nowej paczki. Nie powinna być używana z przypadkową lub zbyt ogólną ścieżką.

Opcje takie jak `--model`, `--config`, `--samples`, `--output` i `--overwrite` są nazwami interfejsu CLI i należy zachowywać ich zapis dokładnie zgodnie z implementacją.

Katalog `dist/` jest lokalnym katalogiem artefaktów budowania i nie powinien być wersjonowany jako zwykła część kodu źródłowego.

## 5. Numerowanie wersji

Wersja modelu powinna jednoznacznie wskazywać konkretne wydanie. Po ustabilizowaniu procesu zalecane jest stosowanie wersjonowania semantycznego (Semantic Versioning, SemVer) na poziomie publikowanych wydań, jeżeli znaczenie zmian da się wiarygodnie przypisać do kategorii `MAJOR.MINOR.PATCH`.

Przykład:

```text
v1.0.0
v1.1.0
v1.1.1
```

Dla modelu uczenia maszynowego sama zmiana numeru wersji nie opisuje jednak pełnej różnicy. Karta modelu i manifest muszą nadal wskazywać wersję danych, kodu, konfiguracji i wyników oceny.

Przed osiągnięciem stabilnego `v1.0.0` można używać wydań przedpremierowych, np.:

```text
v1.0.0-rc.1
v1.0.0-rc.2
```

## 6. Nazewnictwo artefaktów

Nazwa modelu `pl_PL-mateusz-medium` wynika z konwencji identyfikowania głosu i nie jest identyfikatorem Pythona. Nie należy jej zmieniać na `pl_PL_mateusz_medium` wyłącznie w celu dopasowania do PEP 8.

PEP 8 dotyczy identyfikatorów kodu Pythona. Nazwy artefaktów, modeli, wydań i opcji CLI podlegają konwencji właściwej dla danego interfejsu lub formatu.

W nowych skryptach Pythona należy natomiast używać `snake_case` dla nazw modułów, funkcji i zmiennych oraz `CapWords` dla klas.

## 7. Kontrola gotowości

Przed utworzeniem wydania należy uruchomić:

```bash
python scripts/check_release_readiness.py
```

Kontrola automatyczna nie zastępuje oceny odsłuchowej. Jej zadaniem jest wykrycie brakujących artefaktów, danych lub niespełnionych warunków, które można sprawdzić programowo.

## 8. Publikacja

Docelowo model należy publikować jako formalne wydanie repozytorium lub w repozytorium modeli przeznaczonym do dystrybucji dużych artefaktów. Dużych plików ONNX nie należy dodawać do historii Git bez świadomego uzasadnienia.

Przed publikacją należy:

1. uruchomić pełną kontrolę gotowości,
2. zweryfikować SHA-256,
3. sprawdzić zawartość manifestu,
4. sprawdzić kartę modelu,
5. wykonać syntezę z plików znajdujących się już w gotowej paczce,
6. sprawdzić próbki,
7. potwierdzić licencję,
8. oznaczyć wydanie jednoznacznym numerem wersji.

## 9. Niezmienność wydania

Opublikowanego wydania nie należy po cichu zastępować innym modelem pod tym samym numerem wersji. Jeżeli model ONNX, konfiguracja lub inny istotny artefakt uległ zmianie, należy utworzyć nowe wydanie.

Ta zasada pozwala traktować numer wersji i sumy kontrolne jako wiarygodny identyfikator konkretnego stanu modelu.

## 10. Wydanie a eksperyment

Nie każdy eksperyment wymaga publikacji. W trakcie trenowania może powstać wiele punktów kontrolnych i eksportów ONNX. Powinny być one przechowywane jako artefakty eksperymentalne do czasu wyboru kandydata.

Proces powinien mieć kierunek:

```text
eksperyment
  ↓
punkt kontrolny
  ↓
kandydat do wydania
  ↓
pełna ocena
  ↓
paczka wydania
  ↓
publikacja
  ↓
wdrożenie
```

Takie rozdzielenie zapobiega publikowaniu przypadkowych plików i ułatwia ustalenie, który model jest aktualnie wersją stabilną.

## 11. Kryteria akceptacji wydania

Wydanie można zaakceptować, gdy:

- model i konfiguracja są zgodne,
- podstawowy test poprawności kończy się powodzeniem,
- znane są WER i CER,
- wykonano wymaganą ocenę podobieństwa głosu,
- wykonano ocenę odsłuchową,
- zmierzono wydajność na platformach docelowych,
- karta modelu nie zawiera braków krytycznych,
- licencja jest jednoznaczna,
- manifest i sumy kontrolne są kompletne,
- próbki reprezentują rzeczywiste zachowanie modelu,
- istnieje możliwość odtworzenia pochodzenia modelu od zbioru danych do artefaktu ONNX.
