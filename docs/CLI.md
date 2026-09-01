# Interfejs wiersza poleceń

Interfejs wiersza poleceń (command-line interface, CLI) Pipera umożliwia syntezę mowy bezpośrednio z terminala. Jest szczególnie przydatny do testów modelu, automatyzacji i diagnostyki.

Przy wielu kolejnych żądaniach każdorazowe uruchamianie programu może być nieefektywne, ponieważ model musi zostać ponownie wczytany. W takim przypadku należy rozważyć proces utrzymujący model w pamięci, np. [interfejs HTTP](API_HTTP.md) albo usługę Wyoming Piper.

Nazwy opcji CLI pozostają w oryginalnej postaci, ponieważ są częścią interfejsu programu. Terminologię dokumentacji opisano w [słowniku](TERMINOLOGIA.md).

## Instalacja

Dla opublikowanej wersji Pipera:

```bash
pip install piper-tts
```

Podczas prac nad kodem `piper-mat` należy korzystać z odizolowanego środowiska projektu zgodnie z [instrukcją trenowania](TRAINING.md).

## Synteza głosem projektu

Jeżeli pliki modelu znajdują się w bieżącym katalogu:

```bash
python -m piper \
  --model pl_PL-mateusz-medium.onnx \
  --output-file test.wav \
  -- "To jest test polskiego modelu głosu."
```

Model wymaga odpowiadającego mu pliku konfiguracji:

```text
pl_PL-mateusz-medium.onnx
pl_PL-mateusz-medium.onnx.json
```

Nie należy łączyć modelu ONNX z plikiem JSON pochodzącym z innej wersji głosu.

## Katalog modeli

Jeżeli modele znajdują się w innym katalogu, można wskazać katalog danych opcją `--data-dir`, o ile używana wersja Pipera ją obsługuje:

```bash
python -m piper \
  --data-dir /path/to/voices \
  --model pl_PL-mateusz-medium \
  --output-file test.wav \
  -- "Próba syntezy mowy."
```

Przed automatyzacją należy sprawdzić dokładną składnię zainstalowanej wersji:

```bash
python -m piper --help
```

## Przyspieszenie GPU

Opcja `--cuda` włącza wykonywanie obsługiwanych obliczeń za pomocą CUDA. Wymaga odpowiedniej wersji `onnxruntime-gpu` i zgodnego środowiska sterowników.

```bash
python -m piper \
  --cuda \
  --model pl_PL-mateusz-medium.onnx \
  --output-file test.wav \
  -- "Test syntezy z wykorzystaniem GPU."
```

Przyspieszenie GPU nie zawsze zmniejsza całkowity czas pojedynczej krótkiej syntezy, ponieważ znaczenie mają również koszty inicjalizacji i przesyłania danych. Wydajność należy mierzyć, a nie zakładać.

## Przydatne opcje

W zależności od wersji Pipera dostępne mogą być między innymi:

- `--cuda`: użycie CUDA,
- `--input-file`: odczyt tekstu z pliku,
- `--sentence-silence`: dodatkowa cisza pomiędzy zdaniami,
- `--volume`: mnożnik poziomu sygnału,
- `--no-normalize`: wyłączenie normalizacji sygnału,
- `--output-raw`: zapis surowych danych dźwiękowych.

Aktualnym źródłem prawdy dla konkretnej instalacji pozostaje wynik `--help`.

## Cisza pomiędzy zdaniami

Parametr `--sentence-silence` określa czas ciszy dodawanej pomiędzy kolejnymi zdaniami. Przykładowo wartość `0.2` oznacza około 200 ms dodatkowej przerwy.

Zbyt mała wartość może powodować nienaturalne łączenie zdań. Zbyt duża sprawia, że wypowiedź brzmi fragmentarycznie. Parametr należy dobierać do zastosowania, a nie traktować jako sposób naprawiania błędnej prozodii modelu.

## Głośność

`--volume` jest mnożnikiem amplitudy. Wartość `1.0` oznacza brak zamierzonej zmiany poziomu, `0.5` zmniejsza amplitudę, a wartości większe od `1.0` ją zwiększają.

Zwiększanie tego parametru może prowadzić do przesterowania (clipping), dlatego wynik należy kontrolować również na poziomie sygnału, a nie tylko odsłuchowo.

## Surowe fonemy

Piper może umożliwiać przekazywanie fonemów eSpeak NG bezpośrednio w tekście. Jest to funkcja diagnostyczna i zaawansowana. Nie należy jej używać do ręcznego poprawiania całego korpusu zamiast naprawienia źródłowego procesu fonemizacji.

Fonemy dla tekstu można sprawdzić narzędziem eSpeak NG, np. dla języka polskiego:

```bash
espeak-ng -v pl --ipa=3 -q "przykład"
```

Takie testy są przydatne przy diagnozowaniu pojedynczych błędów wymowy.

## Zastosowanie w automatyzacji

CLI jest odpowiednie przede wszystkim do:

- podstawowych testów poprawności,
- skryptów przetwarzania wsadowego,
- diagnostyki konkretnego modelu,
- testowania parametrów syntezy,
- przygotowywania danych do oceny jakości.

Dla aplikacji czasu rzeczywistego należy unikać architektury uruchamiającej nowy proces i wczytującej model dla każdego krótkiego fragmentu tekstu. Model powinien pozostawać w pamięci pomiędzy żądaniami.
