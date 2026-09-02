# Wyniki oceny

Katalog przechowuje wersjonowane wyniki oceny (evaluation) kolejnych modeli `pl_PL-mateusz-medium`.

Każdy kandydat do wydania powinien mieć osobny rekord JSON zawierający co najmniej:

- identyfikator modelu i SHA-256 pliku ONNX,
- SHA-256 konfiguracji JSON,
- SHA-256 `metadata.csv` i `dataset/splits.json`,
- WER i CER wraz z nazwą oraz wersją systemu ASR,
- wyniki podobieństwa głosu, jeśli zostały wykonane,
- wyniki MOS lub CMOS, jeśli przeprowadzono ocenę odsłuchową,
- wyniki wydajności wraz z jednoznacznie określonym zakresem pomiaru,
- identyfikator rekordu środowiska eksperymentu.

Przykładowy układ:

```text
evaluations/
├── README.md
├── v0.1.0-x86_64.json
└── v0.1.0-rpi5.json
```

Nie należy nadpisywać wyników poprzedniego modelu po zmianie punktu kontrolnego, danych treningowych lub konfiguracji. Każdy istotny eksperyment powinien pozostać możliwy do jednoznacznego odtworzenia.

Środowisko można zapisać poleceniem:

```bash
python scripts/record_environment.py \
  --output evaluations/environment-v0.1.0.json
```

## Benchmark procesowy CLI

Skrypt `benchmark_voice.py` mierzy obecnie czas całego procesu CLI. Każdy pomiar obejmuje uruchomienie interpretera Pythona, wczytanie modelu, syntezę i zapis pliku WAV.

```bash
python scripts/benchmark_voice.py \
  --model output/pl_PL-mateusz-medium.onnx \
  --output evaluations/benchmark-v0.1.0.json
```

Taki wynik jest użyteczny do oceny rzeczywistego kosztu pojedynczego wywołania programu, ale nie jest czystym pomiarem czasu wnioskowania modelu utrzymywanego już w pamięci.

W rekordzie wynikowym pola:

```text
benchmark_scope = process_level_cli
includes_process_startup = true
includes_model_loading = true
```

jednoznacznie określają zakres pomiaru.

Jeżeli w przyszłości powstanie benchmark modelu utrzymywanego w jednym procesie, należy zapisywać go jako osobny rodzaj pomiaru i nie porównywać bezpośrednio z wynikiem procesowego CLI bez wyjaśnienia różnicy metodologicznej.

Przed publikacją kandydata należy uruchomić:

```bash
python scripts/check_release_readiness.py
```

Kontrola ta celowo kończy się błędem, dopóki brakuje wymaganych artefaktów lub rzeczywistych wyników oceny.
