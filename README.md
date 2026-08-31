# piper-mat

Wydajna i elastyczna biblioteka oraz interfejs do syntezy mowy (TTS) oparty na silniku Piper.

---

## Opis projektu

piper-mat to narzędzie programistyczne oraz biblioteka Python stworzona w celu uproszczenia, przyspieszenia i zautomatyzowania procesu syntezy mowy (Text-to-Speech) przy użyciu silnika neuronowego Piper TTS.

Projekt umożliwia integrację lokalnej syntezy mowy w czasie rzeczywistym z aplikacjami zewnętrznymi, systemami wbudowanymi (Edge AI), botami oraz narzędziami przetwarzania języka naturalnego (NLP).

### Kluczowe cechy
* Niski narzut obliczeniowy dzięki zastosowaniu środowiska uruchomieniowego ONNX Runtime.
* Pełna praca w trybie offline bez konieczności połączenia z chmurą.
* Wygodne API języka Python oraz dedykowany interfejs wiersza poleceń (CLI).

---

## Funkcje

* Zaawansowane przetwarzanie i normalizacja tekstu wejściowego.
* Obsługa lokalnych modeli neuronowych w formacie ONNX wraz z plikami konfiguracji JSON.
* Wsparcie dla generowania strumieniowego audio z niskim opóźnieniem (low-latency).
* Eksport syntezy do plików WAV, MP3 oraz surowego formatu PCM.
* Regulacja parametrów syntezy: szybkości mowy, intonacji oraz pauz.
* Zwracanie wyników w postaci tablic NumPy dla dalszej analizy sygnałów.

---

## Wymagania systemowe

* Python: wersja 3.9 lub nowsza
* System operacyjny: Linux lub Windows

---

## Instalacja

### Procedura dla systemu Linux

1. Klonowanie repozytorium:
```bash
git clone [https://github.com/MatPomGit/piper-mat.git](https://github.com/MatPomGit/piper-mat.git)
cd piper-mat
```

2. Utworzenie środowiska wirtualnego:
```bash
python3 -m venv venv
```

3. Aktywacja środowiska wirtualnego:
```bash
source venv/bin/activate
```

4. Instalacja wymaganych pakietów:
```bash
pip install -r requirements.txt
```

5. Instalacja pakietu w trybie deweloperskim (opcjonalnie):
```bash
pip install -e .
```

---

### Procedura dla systemu Windows

1. Klonowanie repozytorium (Command Prompt / PowerShell):
```cmd
git clone [https://github.com/MatPomGit/piper-mat.git](https://github.com/MatPomGit/piper-mat.git)
cd piper-mat
```

2. Utworzenie środowiska wirtualnego:
```cmd
python -m venv venv
```

3. Aktywacja środowiska wirtualnego:

Dla Command Prompt (cmd.exe):
```cmd
venv\Scripts\activate.bat
```

Dla PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```

4. Instalacja wymaganych pakietów:
```cmd
pip install -r requirements.txt
```

5. Instalacja pakietu w trybie deweloperskim (opcjonalnie):
```cmd
pip install -e .
```

---

## Użycie wiersza poleceń (CLI)

### Polecenia dla systemu Linux

Synteza tekstu podanego bezpośrednio w konsoli:
```bash
piper-mat --model models/model.onnx --text "Dzień dobry, to jest test syntezy." --output wyjscie.wav
```

Synteza tekstu wczytanego z pliku:
```bash
piper-mat --model models/model.onnx --input-file plik_wejsciowy.txt --output wyjscie.wav
```

Uruchomienie z dodatkowymi parametrami szybkości i intonacji:
```bash
piper-mat --model models/model.onnx --text "Szybki tekst." --length-scale 0.8 --noise-scale 0.5 --output wyjscie.wav
```

---

### Polecenia dla systemu Windows

Synteza tekstu podanego bezpośrednio w konsoli (Command Prompt):
```cmd
piper-mat --model models\model.onnx --text "Dzień dobry, to jest test syntezy." --output wyjscie.wav
```

Synteza tekstu wczytanego z pliku (PowerShell):
```powershell
piper-mat --model .\models\model.onnx --input-file .\plik_wejsciowy.txt --output wyjscie.wav
```

Uruchomienie z dodatkowymi parametrami szybkości i intonacji:
```cmd
piper-mat --model models\model.onnx --text "Szybki tekst." --length-scale 0.8 --noise-scale 0.5 --output wyjscie.wav
```

---

## Użycie w języku Python

Poniższy przykład przedstawia podstawowy kod wczytujący model i wykonujący syntezę tekstu:

```python
from piper_mat import PiperMatEngine, VoiceConfig

# 1. Konfiguracja i inicjalizacja silnika
config = VoiceConfig(
    model_path="models/model.onnx",
    config_path="models/model.onnx.json"
)

engine = PiperMatEngine(config)

# 2. Synteza tekstu do pliku audio
text = "Witaj. To jest przykładowy tekst zsyntezowany w środowisku Python."
output_file = "wyjscie.wav"

engine.synthesize_to_file(text, output_file)
print(f"Wygenerowano plik: {output_file}")

# 3. Pobranie surowych danych audio w postaci tablicy NumPy
audio_data, sample_rate = engine.synthesize(text)
print(f"Czestotliwosc probkowania: {sample_rate} Hz, Liczba probek: {len(audio_data)}")
```

---

## Parametry konfiguracji

| Parametr | Typ | Wartość domyślna | Opis |
| :--- | :--- | :--- | :--- |
| `length_scale` | `float` | `1.0` | Szybkość wypowiedzi (wartości mniejsze niż 1.0 przyspieszają mowę). |
| `noise_scale` | `float` | `0.667` | Zmienność intonacji i generowanego szumu. |
| `noise_w` | `float` | `0.8` | Zmienność długości poszczególnych fonemów. |
| `sample_rate` | `int` | `22050` | Częstotliwość próbkowania sygnału wyjściowego w Hz. |

---

## Struktura projektu

```text
piper-mat/
├── piper_mat/
│   ├── __init__.py          # Inicjalizacja pakietu
│   ├── engine.py            # Glowna logika silnika syntezy
│   ├── audio.py             # Obsluga i zapis plikow audio
│   ├── text.py              # Normalizacja i przetwarzanie tekstu
│   └── cli.py               # Interfejs wiersza polecen
├── tests/                   # Testy jednostkowe
│   ├── test_engine.py
│   └── test_text.py
├── examples/                # Skrypty przykladowe
│   └── basic_synthesis.py
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── setup.py
```

---

## Uruchamianie testów

Uruchomienie pakietu testów jednostkowych w aktywowanym środowisku wirtualnym:

System Linux:
```bash
pytest tests/
```

System Windows:
```cmd
pytest tests/
```

---

## Licencja

Projekt udostępniany jest na warunkach licencji MIT. Szczegółowe informacje znajdują się w pliku LICENSE.

---

## Autorzy i kontakt

* Autor: dr inż. Mateusz Pomianek
* Repozytorium: https://github.com/MatPomGit/piper-mat
* Strona domowa: https://matpomgit.github.io/
