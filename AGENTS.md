# Wytyczne dla agentów i osób rozwijających projekt

Niniejszy dokument określa zasady obowiązujące podczas modyfikowania kodu i dokumentacji `piper-mat`.

## Dokumentacja i terminologia

Dokumentacja użytkowa i projektowa jest prowadzona w języku polskim.

Przy pierwszym użyciu specjalistycznego terminu technicznego należy podać poprawny polski odpowiednik oraz angielską nazwę w nawiasie, np. „częstotliwość próbkowania (sample rate)”. Nie należy tworzyć dosłownych kalek językowych, jeżeli w polskiej terminologii technicznej istnieje poprawniejszy odpowiednik.

Źródłem obowiązującej terminologii jest `docs/TERMINOLOGIA.md`. Przed wprowadzeniem nowego terminu do dokumentacji należy sprawdzić słownik. Jeżeli terminu w nim nie ma, należy ustalić właściwy polski odpowiednik i dodać go do słownika.

Nazwy własne, identyfikatory kodu, nazwy parametrów, opcji wiersza poleceń, formatów i bibliotek, np. `batch_size`, `--checkpoint`, `ONNX`, `PyTorch`, `CUDA`, pozostają w postaci wymaganej technicznie. W tekście należy objaśnić ich znaczenie po polsku.

## Python

Nowy i modyfikowany kod Python powinien być zgodny z PEP 8 (Style Guide for Python Code) oraz PEP 257 (Docstring Conventions), z wyjątkiem sytuacji, w których zgodność naruszałaby kompatybilność projektu albo uzasadnioną, istniejącą konwencję danego modułu.

W szczególności:

- stosuj wcięcia z czterech spacji;
- utrzymuj czytelny podział importów na bibliotekę standardową, zależności zewnętrzne i moduły projektu;
- unikaj importów z symbolem wieloznacznym (`import *`);
- stosuj nazewnictwo zgodne z PEP 8;
- ograniczaj złożoność funkcji i metod;
- nie umieszczaj wielu instrukcji w jednym wierszu;
- komentarze mają wyjaśniać przyczynę lub kontekst, a nie powtarzać kod;
- publiczne moduły, klasy, funkcje i metody powinny mieć łańcuchy dokumentacyjne (docstrings) zgodne z PEP 257;
- jednowierszowy docstring powinien być krótkim zdaniem zakończonym kropką;
- wielowierszowy docstring powinien zaczynać się krótkim podsumowaniem, po którym następuje rozwinięcie oddzielone pustym wierszem;
- do docstringów używaj potrójnych podwójnych cudzysłowów (`"""`).

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
