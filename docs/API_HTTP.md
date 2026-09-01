# Interfejs HTTP

Interfejs HTTP (HTTP API) udostępnia syntezę mowy jako usługę sieciową. Model może dzięki temu pozostać w pamięci pomiędzy kolejnymi żądaniami, a aplikacje klienckie nie muszą bezpośrednio korzystać z biblioteki Pythona.

Rozwiązanie jest przydatne do prototypowania, integracji usług oraz testów. Przed wystawieniem serwera poza zaufaną sieć należy jednak uwzględnić bezpieczeństwo, uwierzytelnianie, ograniczanie liczby żądań i warstwę TLS. Wbudowanego serwera nie należy automatycznie traktować jako kompletnej bramy produkcyjnej.

Nazwy punktów końcowych (endpoints), pól JSON i opcji programu pozostają bez zmian. Terminologię dokumentacji opisano w [słowniku](TERMINOLOGIA.md).

## Instalacja

```bash
python -m pip install "piper-tts[http]"
```

Podczas rozwoju `piper-mat` należy korzystać z odizolowanego środowiska projektu.

## Uruchomienie głosu projektu

```bash
python -m piper.http_server \
  --model pl_PL-mateusz-medium.onnx
```

Dokładna nazwa opcji modelu może zależeć od używanej wersji Pipera. Przed automatyzacją należy sprawdzić:

```bash
python -m piper.http_server --help
```

Domyślnie serwer może nasłuchiwać na porcie `5000`. Adres i port można zmienić opcjami `--host` i `--port`, jeżeli obsługuje je dana wersja.

## Adres nasłuchiwania

Adres nasłuchiwania (bind address) określa interfejs sieciowy, na którym serwer przyjmuje połączenia.

`127.0.0.1` ogranicza dostęp do komputera lokalnego i jest właściwym ustawieniem domyślnym do testów. `0.0.0.0` pozwala nasłuchiwać na wszystkich interfejsach IPv4, przez co usługa może stać się dostępna z innych urządzeń w sieci.

Nie należy zmieniać adresu na `0.0.0.0` bez świadomego określenia reguł zapory sieciowej i sposobu ochrony usługi.

## Informacje o usłudze

Punkt końcowy `/info` zwraca informacje o aktywnym modelu i ostatniej syntezie w formacie JSON:

```bash
curl http://127.0.0.1:5000/info
```

W zależności od wersji serwera odpowiedź może zawierać między innymi nazwę głosu, język, informacje o mówcach oraz dane związane z syntezą i dopasowaniami fonemów.

## Lista głosów

Jeżeli serwer obsługuje wiele modeli, dostępne głosy można sprawdzić przez:

```bash
curl http://127.0.0.1:5000/voices
```

## Synteza mowy

Żądanie `POST` do `/synthesize` przyjmuje dane JSON i zwraca dźwięk WAV.

```bash
curl \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"text":"To jest test polskiego głosu."}' \
  -o test.wav \
  http://127.0.0.1:5000/synthesize
```

Pole `text` jest tekstem przeznaczonym do syntezy. Nie należy przesyłać pustego tekstu ani nieograniczonych rozmiarowo danych pochodzących bezpośrednio od niezaufanego klienta.

## Parametry żądania

W zależności od wersji API dostępne mogą być między innymi następujące pola:

- `text`: tekst do syntezy, wymagany,
- `voice`: nazwa głosu,
- `speaker`: nazwa mówcy w modelu wielomówcowym,
- `speaker_id`: identyfikator mówcy,
- `length_scale`: skala długości (length scale),
- `noise_scale`: skala szumu (noise scale),
- `noise_w_scale`: skala szumu długości (noise width scale).

Znaczenie parametrów syntezy opisano szerzej w [dokumentacji API Pythona](API_PYTHON.md).

### `length_scale`

Skala długości wpływa na czas trwania wypowiedzi. Wartość około `1.0` odpowiada nominalnej charakterystyce modelu. Wartości większe wydłużają mowę, a mniejsze ją skracają.

### `noise_scale`

Skala szumu wpływa na zmienność generowania. Nie oznacza dodawania szumu akustycznego do końcowego pliku WAV.

### `noise_w_scale`

Skala szumu długości wpływa na zmienność czasów trwania elementów wypowiedzi, a więc również na rytm mowy.

Przy ocenie modeli parametry te powinny być ustalone i zapisane, aby porównanie było powtarzalne.

## Interfejs przeglądarkowy

Jeżeli używana wersja serwera udostępnia stronę testową, można ją otworzyć lokalnie pod adresem serwera. Interfejs ten służy przede wszystkim do diagnostyki i ręcznych prób syntezy, a nie jako docelowy interfejs użytkownika systemu.

## Obsługa błędów po stronie klienta

Klient powinien rozróżniać co najmniej:

1. brak połączenia z usługą,
2. przekroczenie czasu oczekiwania,
3. odpowiedź HTTP sygnalizującą błąd,
4. niepoprawny format odpowiedzi,
5. błąd dekodowania lub odtwarzania otrzymanego WAV.

Nie należy traktować każdej awarii jako „błędu TTS”, ponieważ problem może wystąpić w warstwie sieciowej, aplikacyjnej albo dźwiękowej.

## Bezpieczeństwo

W przypadku dostępu spoza hosta lokalnego należy co najmniej:

- ograniczyć dostęp sieciowy do wymaganych klientów,
- nie przechowywać sekretów w repozytorium,
- zastosować uwierzytelnianie w warstwie pośredniczącej, jeżeli usługa jest dostępna dla niezaufanych klientów,
- zastosować TLS dla ruchu przechodzącego przez niezaufaną sieć,
- ograniczyć maksymalną długość tekstu i częstotliwość żądań,
- monitorować zużycie CPU, GPU i pamięci,
- nie zwracać klientowi niepotrzebnych szczegółów wyjątków wewnętrznych.

Dla wdrożeń domowych i integracji z Home Assistant preferowane jest utrzymywanie Pipera w zaufanej sieci lokalnej i wystawianie na zewnątrz tylko kontrolowanej warstwy aplikacyjnej, jeżeli jest to rzeczywiście potrzebne.
