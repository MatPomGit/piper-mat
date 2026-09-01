# Karta zbioru danych `pl_PL-mateusz`

Karta zbioru danych (dataset card) dokumentuje pochodzenie, sposób przygotowania, właściwości, ograniczenia i prawa do danych używanych podczas trenowania modelu. Jej celem jest umożliwienie odtworzenia procesu oraz wykrycie różnic pomiędzy kolejnymi wersjami zbioru.

Pola `TODO` należy uzupełniać wyłącznie na podstawie rzeczywistych danych i pomiarów.

## Przeznaczenie

Zbiór służy do trenowania i dostrajania (fine-tuning) pojedynczego polskiego głosu `pl_PL-mateusz-medium` dla Piper TTS.

Metadane treningowe znajdują się w `dataset/metadata.csv`. Nagrania mogą znajdować się w `dataset/wavs/` w środowisku roboczym, ale sposób ich wersjonowania i publikacji należy rozpatrywać niezależnie od kodu źródłowego.

## Stan

Zbiór jest w trakcie przygotowania i walidacji. Brak wartości w polu `TODO` oznacza brak zatwierdzonego pomiaru, a nie wartość zero.

## Dane podstawowe

- język: polski (`pl_PL`),
- liczba mówców: 1,
- mówca: Mateusz,
- docelowa częstotliwość próbkowania (sample rate): 22 050 Hz,
- docelowa liczba kanałów: 1, mono,
- format roboczy: WAV,
- liczba wypowiedzi: TODO,
- łączny czas nagrań: TODO,
- średnia długość segmentu: TODO,
- mediana długości segmentu: TODO,
- minimalna długość segmentu: TODO,
- maksymalna długość segmentu: TODO.

## Pochodzenie nagrań

Dla każdego źródła należy udokumentować co najmniej:

- typ materiału źródłowego: TODO,
- liczbę lub czas nagrań z danego źródła: TODO,
- sprzęt rejestrujący: TODO,
- mikrofon: TODO,
- środowisko akustyczne: TODO,
- pierwotną częstotliwość próbkowania: TODO,
- pierwotną liczbę kanałów: TODO,
- format źródłowy: TODO,
- sposób uzyskania transkrypcji: TODO.

Jeżeli zbiór łączy materiał nagrany w różnych warunkach, należy zachować informację o źródle segmentów. Pozwala to później sprawdzić, czy określone urządzenie lub środowisko nie wprowadza systematycznych różnic.

## Transkrypcje

Transkrypcja powinna odpowiadać temu, co rzeczywiście zostało wypowiedziane. Nie należy automatycznie „poprawiać” wypowiedzi do wersji, której nie ma w nagraniu.

Należy udokumentować:

- sposób wykonania transkrypcji: TODO,
- użyte narzędzia automatycznego rozpoznawania mowy, jeżeli występują: TODO,
- sposób ręcznej korekty: TODO,
- zasady zapisu liczb i skrótów: TODO,
- sposób traktowania przejęzyczeń i urwanych wypowiedzi: TODO.

Automatyczna transkrypcja może przyspieszyć przygotowanie danych, ale jej wynik powinien zostać zweryfikowany. Błędna transkrypcja uczy model nieprawidłowej relacji pomiędzy tekstem i dźwiękiem.

## Przygotowanie dźwięku

Należy udokumentować kolejno:

1. ekstrakcję dźwięku ze źródeł,
2. konwersję formatu,
3. zmianę częstotliwości próbkowania, jeżeli była wykonywana,
4. konwersję do jednego kanału,
5. segmentację wypowiedzi,
6. sposób traktowania ciszy,
7. normalizację poziomu sygnału, jeżeli była wykonywana,
8. redukcję szumu, jeżeli była wykonywana,
9. kryteria odrzucania segmentów,
10. końcową walidację plików.

Każda operacja zmieniająca sygnał powinna mieć uzasadnienie. Nadmierne odszumianie, agresywne bramkowanie lub silna normalizacja mogą usunąć naturalne cechy głosu albo wprowadzić artefakty.

## Segmentacja

Segmentacja (segmentation) dzieli długie nagrania na krótsze wypowiedzi wykorzystywane przez proces trenowania. Segment powinien tworzyć sensowną jednostkę mowy i mieć zgodną transkrypcję.

Zbyt długie segmenty zwiększają zapotrzebowanie na pamięć i mogą utrudniać trenowanie. Bardzo krótkie fragmenty mogą z kolei nie dostarczać wystarczającego kontekstu prozodycznego. Docelowe kryteria długości powinny zostać wyznaczone na podstawie rozkładu danych, a nie arbitralnie przyjętej jednej wartości.

Zastosowane kryteria segmentacji: TODO.

## Poziom sygnału i przesterowanie

Przesterowanie (clipping) występuje wtedy, gdy amplituda sygnału przekracza zakres możliwy do reprezentacji i zostaje obcięta. Tak uszkodzonego fragmentu nie można w pełni naprawić zwykłym zmniejszeniem głośności.

Dla zbioru należy raportować co najmniej:

- liczbę segmentów z wykrytym przesterowaniem: TODO,
- rozkład wartości szczytowych: TODO,
- rozkład poziomu RMS: TODO.

RMS opisuje skuteczną wartość amplitudy sygnału i jest użytecznym przybliżeniem jego poziomu energetycznego. Nie należy jednak ustalać jakości nagrania wyłącznie na podstawie jednej wartości RMS.

## Kontrola techniczna

Podstawową kontrolę można uruchomić poleceniem:

```bash
python scripts/validate_dataset.py \
  --metadata dataset/metadata.csv \
  --audio-dir dataset/wavs
```

Walidacja powinna obejmować co najmniej:

- brakujące pliki,
- pliki nieujęte w metadanych,
- duplikaty,
- puste transkrypcje,
- niezgodne formaty,
- niezgodną częstotliwość próbkowania,
- nagrania wielokanałowe,
- długości segmentów,
- przesterowanie,
- poziom sygnału,
- udział ciszy,
- pokrycie znaków języka polskiego.

Jeżeli wykonywana jest fonemizacja całego zbioru, warto dodatkowo raportować pokrycie fonemów oraz przypadki, których eSpeak NG nie przetwarza zgodnie z oczekiwaniem.

## Podział danych

Podział zbioru danych (data split) tworzy niezależne części wykorzystywane do różnych etapów pracy:

- zbiór treningowy (training set) służy do aktualizacji parametrów modelu,
- zbiór walidacyjny (validation set) służy do obserwacji procesu i wyboru konfiguracji lub punktu kontrolnego,
- zbiór testowy (test set) służy do końcowej oceny modelu.

Po zatwierdzeniu podział powinien zostać zamrożony i wersjonowany. Zmiana zawartości zbioru testowego pomiędzy eksperymentami utrudnia bezpośrednie porównywanie wyników.

- zbiór treningowy: TODO,
- zbiór walidacyjny: TODO,
- zbiór testowy: TODO,
- ziarno losowania (seed): TODO,
- plik definiujący podział: TODO.

## Pokrycie języka polskiego

Zbiór powinien zawierać wystarczającą reprezentację charakterystycznych elementów języka polskiego. Należy analizować co najmniej:

- występowanie `ą`, `ć`, `ę`, `ł`, `ń`, `ó`, `ś`, `ź`, `ż`,
- rozkład fonemów,
- częste połączenia fonemów,
- liczby i formy fleksyjne,
- skróty i jednostki,
- różne typy zdań i interpunkcji,
- nazwy własne, jeśli mają być istotnym zastosowaniem modelu.

Sama obecność znaku lub fonemu w zbiorze nie oznacza jeszcze wystarczającego pokrycia. Istotna jest liczba i różnorodność kontekstów.

## Duplikaty i przeciek danych

Duplikaty lub bardzo podobne fragmenty nie powinny znaleźć się jednocześnie w zbiorze treningowym i testowym. Taki przeciek danych (data leakage) może sztucznie poprawić wyniki oceny, ponieważ model jest testowany na materiale, który w praktyce już widział.

Kontrola powinna obejmować zarówno identyczne pliki, jak i segmenty pochodzące z tej samej dłuższej wypowiedzi, jeśli ich podobieństwo mogłoby zafałszować ocenę.

## Prywatność i prawa do głosu

Nagrania przedstawiają głos jednej konkretnej osoby. Prawo do wykorzystania kodu Piper nie oznacza automatycznie prawa do publikowania zbioru nagrań ani modelu odtwarzającego tożsamość głosową mówcy.

Przed publicznym udostępnieniem należy jednoznacznie określić:

- właściciela lub właścicieli praw do nagrań,
- zgodę mówcy na wykorzystanie głosu,
- zgodę na trenowanie modelu,
- zgodę lub jej brak na publikację nagrań,
- zgodę lub jej brak na publikację modelu głosu,
- dopuszczalne zastosowania i ograniczenia wynikające z licencji.

## Wersjonowanie

Każda wersja zbioru użyta do istotnego eksperymentu powinna być identyfikowalna. Należy zachować co najmniej:

- wersję lub identyfikator zatwierdzenia metadanych,
- statystyki zbioru,
- definicję podziału,
- opis procesu przygotowania,
- informacje o narzędziach użytych do transformacji.

Dzięki temu można ustalić, czy zmiana jakości modelu wynikała z kodu, parametrów trenowania czy zmiany danych.

## Licencja

Licencja zbioru danych: TODO.

Musi zostać określona niezależnie od GPL-3.0-or-later obejmującej kod Piper. Warunki publikacji powinny wynikać z praw do nagrań oraz świadomej decyzji właściciela głosu.
