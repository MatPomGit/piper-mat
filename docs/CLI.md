# 🖥️ Interfejs wiersza poleceń

Interfejs wiersza poleceń Pipera pozwala szybko uzyskać dźwięk z tekstu i wypróbować różne głosy. Może jednak działać wolno, ponieważ za każdym razem musi wczytać model głosu. Przy wielokrotnym użyciu zalecany jest [serwer WWW](API_HTTP.md).

## Instalowanie

Zainstaluj za pomocą:

``` sh
pip install piper-tts
```

## Pobieranie głosów

Wyświetl listę głosów za pomocą:

``` sh
python3 -m piper.download_voices
```

Wybierz głos ([próbki są dostępne tutaj][samples]) i pobierz go. Na przykład:

``` sh
python3 -m piper.download_voices en_US-lessac-medium
```

Głos zostanie pobrany do bieżącego katalogu. Można to zmienić za pomocą `--data-dir <DIR>`.

## Uruchamianie

Po pobraniu powyższego przykładowego głosu uruchom:

``` sh
python3 -m piper -m en_US-lessac-medium -f test.wav -- 'This is a test.'
```

Spowoduje to zapisanie zdania „This is a test.” w pliku `test.wav`.
Jeśli głosy znajdują się w innym katalogu, użyj `--data-dir <DIR>`.

Jeśli zainstalowano [ffplay][], pomiń `-f`, aby od razu usłyszeć dźwięk:

``` sh
python3 -m piper -m en_US-lessac-medium -- 'This will play on your speakers.'
```

Uruchamianie Pipera w ten sposób jest powolne, ponieważ za każdym razem trzeba wczytać model. Uruchom [serwer WWW](API_HTTP.md), chyba że konieczne jest strumieniowanie dźwięku (zobacz `--output-raw` w `--help`).

Inne przydatne opcje wiersza poleceń:

* `--cuda` — włącza przyspieszenie GPU (wymaga pakietu `onnxruntime-gpu`)
* `--input-file` — odczytuje tekst wejściowy z jednego lub wielu plików
* `--sentence-silence` — dodaje sekundy ciszy do wszystkich zdań poza ostatnim
* `--volume` — dostosowuje mnożnik głośności (domyślnie: 1.0)
* `--no-normalize` — wyłącza automatyczną normalizację głośności

### Surowe fonemy

Surowe fonemy espeak-ng można wstrzykiwać za pomocą bloków `[[ <phonemes> ]]`. Na przykład:

```
I am the [[ bˈætmæn ]] not [[bɹˈuːs wˈe‍ɪn]]
```

Aby pobrać fonemy z espeak-ng, użyj:

``` sh
espeak-ng -v <VOICE> --ipa=3 -q <TEXT>
```

Na przykład:

``` sh
espeak-ng -v en-us --ipa=3 -q batman
bˈætmæn
```

## Wydania binarne

* [amd64](https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz) (64-bitowy komputer z systemem Linux)
* [arm64](https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz) (64-bitowy Raspberry Pi 4)
* [armv7](https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_armv7.tar.gz) (32-bitowy Raspberry Pi 3/4)

<!-- Odnośniki -->
[samples]: https://rhasspy.github.io/piper-samples/
[ffplay]: https://ffmpeg.org/ffplay.html
