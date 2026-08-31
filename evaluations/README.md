# Wyniki ewaluacji

Katalog przechowuje wersjonowane wyniki pomiarów kolejnych modeli `pl_PL-mateusz-medium`.

Każdy kandydat do wydania powinien mieć osobny rekord JSON zawierający co najmniej:

- identyfikator modelu i SHA-256 pliku ONNX,
- SHA-256 konfiguracji JSON,
- SHA-256 `metadata.csv` i `dataset/splits.json`,
- WER i CER wraz z nazwą oraz wersją systemu ASR,
- wyniki podobieństwa głosu, jeśli zostały wykonane,
- wyniki MOS lub CMOS, jeśli przeprowadzono ocenę odsłuchową,
- benchmark RTF dla wskazanego sprzętu,
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

Benchmark modelu:

```bash
python scripts/benchmark_voice.py \
  --model output/pl_PL-mateusz-medium.onnx \
  --output evaluations/benchmark-v0.1.0.json
```

Przed publikacją kandydata należy uruchomić:

```bash
python scripts/check_release_readiness.py
```

Kontrola ta celowo kończy się błędem, dopóki brakuje wymaganych artefaktów lub rzeczywistych wyników ewaluacji.
