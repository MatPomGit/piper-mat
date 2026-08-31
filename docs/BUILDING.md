# 🛠️ Ręczne kompilowanie

Do zbudowania modułu Python, który bezpośrednio osadza [espeak-ng][], używamy [scikit-build-core](https://github.com/scikit-build/scikit-build-core) wraz z [cmake](https://cmake.org/).

Należy zainstalować następujące pakiety systemowe (`apt-get`):

* `build-essential`
* `cmake`
* `ninja-build`

Aby utworzyć środowisko deweloperskie:

``` sh
git clone https://github.com/OHF-voice/piper1-gpl.git
cd piper1-gpl
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .[dev]
```

Następnie uruchom `script/dev_build` lub ręcznie zbuduj rozszerzenie:

``` sh
python3 setup.py build_ext --inplace
```

Teraz można użyć `script/run` lub ręcznie uruchomić Pipera:

``` sh
python3 -m piper --help
```

Pakiety wheel można zbudować ręcznie za pomocą:

``` sh
python3 -m build
```

## Decyzje projektowe

[espeak-ng][] jest używany za pośrednictwem niewielkiego mostu Python w pliku `espeakbridge.c`, który korzysta z [ograniczonego API][limited-api] języka Python. Pozwala to korzystać ze [stabilnego ABI][stable-abi] języka Python, dzięki czemu pakiety wheel Pipera trzeba budować tylko raz dla każdej platformy (Linux, Mac, Windows), zamiast dla każdej platformy **i** wersji języka Python.

Budujemy źródłowy projekt [espeak-ng][], ponieważ dodano w nim funkcję `espeak_TextToPhonemesWithTerminator`, od której zależy Piper. Funkcja ta pobiera fonemy tekstu, a także „terminator” kończący każdą klauzulę tekstu, taki jak przecinek lub kropka. Piper wymaga tego terminatora, ponieważ znaki interpunkcyjne są przekazywane do modelu głosu jako „fonemy”, aby mogły wpływać na syntezę. Na przykład głos wytrenowany z użyciem zdań oznajmujących (kończących się „.”), pytań (kończących się „?”) i wykrzyknień (kończących się „!”) może inaczej wymawiać zdania zakończone każdym z tych znaków. Przecinki, dwukropki i średniki są również przydatne do uzyskania właściwych pauz w zsyntetyzowanym dźwięku.

<!-- Odnośniki -->
[espeak-ng]: https://github.com/espeak-ng/espeak-ng
[limited-api]: https://docs.python.org/3/c-api/stable.html#limited-c-api
[stable-abi]: https://docs.python.org/3/c-api/stable.html#stable-abi
