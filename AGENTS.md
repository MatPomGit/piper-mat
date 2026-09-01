# Wytyczne dla agentów i osób rozwijających projekt

Niniejszy dokument określa zasady obowiązujące podczas modyfikowania kodu i dokumentacji `piper-mat`.

## Dokumentacja i terminologia

Dokumentacja użytkowa i projektowa jest prowadzona w języku polskim.

Przy pierwszym użyciu specjalistycznego terminu technicznego należy podać poprawny polski odpowiednik oraz angielską nazwę w nawiasie, np. „częstotliwość próbkowania (sample rate)”. Nie należy tworzyć dosłownych kalek językowych, jeżeli w polskiej terminologii technicznej istnieje poprawniejszy odpowiednik.

Źródłem obowiązującej terminologii jest `docs/TERMINOLOGIA.md`. Przed wprowadzeniem nowego terminu do dokumentacji należy sprawdzić słownik. Jeżeli terminu w nim nie ma, należy ustalić właściwy polski odpowiednik i dodać go do słownika.

Nazwy własne, identyfikatory kodu, nazwy parametrów, opcji wiersza poleceń, formatów i bibliotek, np. `batch_size`, `--checkpoint`, `ONNX`, `PyTorch`, `CUDA`, pozostają w postaci wymaganej technicznie. W tekście należy objaśnić ich znaczenie po polsku.

W dokumentacji nie należy używać pauzy em (em dash, `—`). Należy stosować polską interpunkcję odpowiednią do zdania, najczęściej przecinek, dwukropek, średnik, nawias albo osobne zdanie. Łącznik `-` należy stosować wyłącznie tam, gdzie pełni funkcję łącznika, np. w nazwie technicznej wymagającej takiego zapisu.

## Python

Nowy i modyfikowany kod Python powinien być zgodny z PEP 8 (Style Guide for Python Code) oraz PEP 257 (Docstring Conventions), z wyjątkiem sytuacji, w których zgodność naruszałaby kompatybilność projektu albo uzasadnioną, istniejącą konwencję danego modułu.

W szczególności:

- stosuj wcięcia z czterech spacji;
- utrzymuj czytelny podział importów na bibliotekę standardową, zależności zewnętrzne i moduły projektu;
- unikaj importów z symbolem wieloznacznym (`import *`);
- ograniczaj złożoność funkcji i metod;
- nie umieszczaj wielu instrukcji w jednym wierszu;
- komentarze mają wyjaśniać przyczynę lub kontekst, a nie powtarzać kod;
- publiczne moduły, klasy, funkcje i metody powinny mieć łańcuchy dokumentacyjne (docstrings) zgodne z PEP 257;
- jednowierszowy docstring powinien być krótkim zdaniem zakończonym kropką;
- wielowierszowy docstring powinien zaczynać się krótkim podsumowaniem, po którym następuje rozwinięcie oddzielone pustym wierszem;
- do docstringów używaj potrójnych podwójnych cudzysłowów (`"""`).

### Nazewnictwo zgodne z PEP 8

Konwencję należy dobierać do rodzaju elementu. Nie należy stosować jednego stylu nazw do wszystkich artefaktów projektu.

| Element | Konwencja | Przykład |
| --- | --- | --- |
| funkcje | `snake_case` | `load_voice_model()` |
| metody | `snake_case` | `validate_dataset()` |
| zmienne lokalne | `snake_case` | `sample_rate` |
| parametry funkcji | `snake_case` | `audio_path` |
| atrybuty instancji | `snake_case` | `self.voice_name` |
| moduły Pythona | krótkie nazwy małymi literami, w razie potrzeby `snake_case` | `voice_export.py` |
| pakiety Pythona | krótkie nazwy małymi literami; podkreślenia stosować tylko wtedy, gdy są rzeczywiście potrzebne | `piper`, `audio_utils` |
| klasy | `CapWords` / `PascalCase` | `VoiceEvaluator` |
| wyjątki | `CapWords`, zwykle z końcówką `Error` | `DatasetValidationError` |
| stałe modułu | `UPPER_CASE_WITH_UNDERSCORES` | `DEFAULT_SAMPLE_RATE` |
| nazwy chronione konwencją | pojedyncze podkreślenie z przodu | `_load_metadata()` |

`snake_case` oznacza zapis małymi literami, w którym wyrazy rozdziela znak podkreślenia, np. `sample_rate`.

`CapWords`, nazywany też `PascalCase`, rozpoczyna każdy człon wielką literą bez separatorów, np. `SynthesisConfig`.

`UPPER_CASE_WITH_UNDERSCORES` stosuje wielkie litery i podkreślenia, np. `MAX_AUDIO_SECONDS`.

### Gdzie nie stosować `kebab-case`

`kebab-case`, np. `sample-rate`, nie jest poprawną konwencją dla identyfikatorów Pythona. Znak `-` jest w składni Pythona operatorem odejmowania, dlatego nie może występować w nazwie zmiennej, funkcji, klasy ani importowanego modułu.

Nie należy więc tworzyć w kodzie nazw takich jak:

```text
sample-rate
voice-model
load-audio
```

Ich odpowiedniki w Pythonie to odpowiednio:

```text
sample_rate
voice_model
load_audio
```

### Gdzie `kebab-case` jest właściwy

`kebab-case` może być stosowany w interfejsie wiersza poleceń (command-line interface, CLI), ponieważ opcje CLI nie są identyfikatorami Pythona. Przykłady:

```text
--sample-rate
--output-file
--data-dir
```

Kod obsługujący taką opcję powinien jednak używać nazwy zgodnej z Pythonem, np. `sample_rate`, o ile biblioteka CLI nie narzuca innego rozwiązania.

Jeżeli istniejący interfejs programu definiuje konkretną nazwę, np. `--output-file`, `--data.batch_size` albo `--checkpoint`, należy zachować ją dokładnie. Nie wolno zmieniać publicznego API lub CLI wyłącznie w celu ujednolicenia wyglądu nazw.

### Wielkość liter

Należy zachowywać znaczenie wielkości liter i nie tworzyć wariantów nazw różniących się tylko zapisem.

Poprawne przykłady:

```python
DEFAULT_SAMPLE_RATE = 22_050


def load_voice_model(model_path: str):
    ...


class VoiceModel:
    ...
```

Należy unikać nazw takich jak `Sample_rate`, `sampleRate`, `VOICEModel` lub `LoadVoiceModel`, jeśli nie wynikają z zewnętrznego API wymagającego takiego zapisu.

Nazwy akronimów wewnątrz klas należy traktować zgodnie z zasadą czytelnego `CapWords`, np. `HttpServer`, jeżeli jest to nowa nazwa projektowa. Nie należy jednak samodzielnie zmieniać istniejących publicznych nazw klas lub bibliotek, np. `ONNX`, `CUDA`, `HTTP`, `PiperVoice`, jeżeli stanowią one ustalone API lub nazwę własną.

### Podkreślenia specjalne

Pojedyncze podkreślenie na początku, np. `_helper`, sygnalizuje element przeznaczony do użytku wewnętrznego.

Podwójne podkreślenie na początku nazwy atrybutu klasy uruchamia mechanizm przekształcania nazwy (name mangling) i nie powinno być używane jako zwykły sposób oznaczania elementów prywatnych.

Nazwy postaci `__name__`, `__init__` lub `__str__` są zarezerwowane dla specjalnych nazw Pythona. Nie należy tworzyć własnych nowych nazw typu `__custom__`.

### Nazwy plików i katalogów

Pliki będące modułami Pythona powinny mieć nazwy zgodne z PEP 8, np. `voice_export.py`, a nie `VoiceExport.py` ani `voice-export.py`.

Dla plików, które nie są modułami Pythona, PEP 8 nie narzuca `snake_case` ani `kebab-case`. Należy stosować konwencję właściwą dla danego typu artefaktu i zachowywać istniejącą strukturę projektu. Przykładowo dokumenty `README.md`, `AGENTS.md` i `MODEL_CARD.md` mogą zachować ustalone nazwy.

Nie należy masowo zmieniać nazw istniejących plików tylko po to, aby wymusić jedną konwencję, jeżeli spowodowałoby to zerwanie odnośników, importów, skryptów lub publicznych ścieżek.

Normy źródłowe:

- PEP 8: https://peps.python.org/pep-0008/
- PEP 257: https://peps.python.org/pep-0257/

## Projektowanie kodu

Podstawową regułą projektu jest KISS (Keep It Simple, Stupid), rozumiana jako wybieranie najprostszego rozwiązania, które poprawnie spełnia wymagania.

Należy:

- preferować prosty przepływ sterowania zamiast nadmiernej abstrakcji;
- wydzielać funkcje i klasy według rzeczywistej odpowiedzialności;
- unikać przedwczesnej generalizacji i projektowania mechanizmów na hipotetyczne przyszłe potrzeby;
- eliminować zbędne powtórzenia, ale nie kosztem tworzenia sztucznych abstrakcji;
- nadawać zmiennym, funkcjom i klasom jednoznaczne nazwy;
- ograniczać efekty uboczne i zależności globalne;
- jawnie obsługiwać błędy w miejscach, w których można podjąć sensowną decyzję;
- usuwać martwy kod zamiast pozostawiać zakomentowane implementacje;
- zachowywać zgodność wsteczną, jeżeli nie ma świadomej decyzji o jej zerwaniu;
- dodawać lub aktualizować testy przy zmianie zachowania programu.

Czytelność i poprawność mają pierwszeństwo przed skracaniem kodu. Optymalizację należy wprowadzać na podstawie rzeczywistej potrzeby lub pomiarów, a nie kosztem zrozumiałości bez uzasadnienia.

## Zakres zmian

Zmiana powinna być możliwie mała i skupiona na konkretnym problemie. Nie należy wykonywać niezwiązanych refaktoryzacji przy okazji poprawki, chyba że są konieczne do bezpiecznego wdrożenia zmiany.

Po zmianie kodu należy sprawdzić odpowiednie testy, narzędzia kontroli jakości oraz zgodność dokumentacji z rzeczywistym zachowaniem programu. Dokumentacja, testy i kod powinny opisywać ten sam stan projektu.
