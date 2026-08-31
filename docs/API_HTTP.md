# 🌐 HTTP API

Zainstaluj niezbędne zależności:

``` sh
python3 -m pip install piper-tts[http]
```

Pobierz głos, na przykład:

``` sh
python3 -m piper.download_voices en_US-lessac-medium
```

Uruchom serwer WWW:

``` sh
python3 -m piper.http_server -m en_US-lessac-medium
```

Spowoduje to uruchomienie serwera HTTP na porcie 5000 (użyj `--host` i `--port`, aby to zmienić).
Jeśli głosy znajdują się w innym katalogu, użyj `--data-dir <DIR>`.

## Interfejs WWW

Otwórz [http://localhost:5000](http://localhost:5000) w przeglądarce, aby przetestować głos:
wpisz tekst, kliknij **Speak** i posłuchaj wyniku. Strona wyświetla również
informacje o głosie (nazwę, język i liczbę mówców), a dla ostatnio
zsyntetyzowanej wypowiedzi — czas syntezy wraz z fonemami i ich dopasowaniami
dźwięku.

Te same informacje są dostępne w formacie JSON w punkcie końcowym `/info`:

``` sh
curl localhost:5000/info
```

## Syntezowanie dźwięku

Pliki WAV można pobierać przez HTTP, wysyłając żądanie POST do `/synthesize`:

``` sh
curl -X POST -H 'Content-Type: application/json' -d '{ "text": "This is a test." }' -o test.wav localhost:5000/synthesize
```

Pola danych JSON:

* `text` (wymagane) — tekst do syntezy
* `voice` (opcjonalne) — nazwa używanego głosu; domyślnie `-m <VOICE>`
* `speaker` (opcjonalne) — nazwa mówcy w przypadku głosów wielomówcowych
* `speaker_id` (opcjonalne) — identyfikator mówcy w przypadku głosów wielomówcowych; zastępuje `speaker`
* `length_scale` (opcjonalne) — szybkość mowy; domyślnie 1
* `noise_scale` (opcjonalne) — zmienność mowy
* `noise_w_scale` (opcjonalne) — zmienność długości fonemów

Dostępne głosy można pobrać za pomocą:

``` sh
curl localhost:5000/voices
```
