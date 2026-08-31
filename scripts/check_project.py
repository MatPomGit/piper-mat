#!/usr/bin/env python3
"""Lekkie kontrole integralności repozytorium odpowiednie dla CI."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; CONFIG=ROOT/"configs/pl_PL-mateusz-medium.json"
REQUIRED=[ROOT/"COPYING",ROOT/"dataset/DATASET_CARD.md",ROOT/"models/pl_PL-mateusz-medium/MODEL_CARD.md",ROOT/"docs/ROADMAP.md",ROOT/"docs/STAGED_TRAINING.md",ROOT/"docs/WINDOWS_GUI.md",ROOT/"dataset/metadata.csv",ROOT/"train.sh",ROOT/"train.ps1",ROOT/"START_PIPER_MAT_GUI.bat",ROOT/"tools/windows_setup_gui.py",ROOT/"tools/start_windows_gui.ps1",ROOT/"tools/windows_doctor.py",ROOT/"scripts/train_voice.py",ROOT/"scripts/train_sessions.py",ROOT/"scripts/report_training_session.py",ROOT/"scripts/check_training_ready.py",ROOT/"scripts/record_environment.py",ROOT/"scripts/validate_dataset.py"]
def main():
    errors=[]
    for p in REQUIRED:
        if not p.exists(): errors.append(f"brak wymaganej ścieżki: {p.relative_to(ROOT)}")
    if not CONFIG.is_file(): errors.append("brak konfiguracji głosu: configs/pl_PL-mateusz-medium.json")
    else:
        try:data=json.loads(CONFIG.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:errors.append(f"niepoprawna konfiguracja JSON: {e}")
        else:
            for k,v in {"language":"pl_PL","quality":"medium","sample_rate":22050,"espeak_voice":"pl"}.items():
                if data.get(k)!=v: errors.append(f"config {k!r}: oczekiwano {v!r}, otrzymano {data.get(k)!r}")
            export=data.get("export",{})
            if export.get("model_filename")!="pl_PL-mateusz-medium.onnx": errors.append("nieoczekiwana nazwa pliku modelu ONNX w konfiguracji")
            if export.get("config_filename")!="pl_PL-mateusz-medium.onnx.json": errors.append("nieoczekiwana nazwa pliku JSON modelu ONNX w konfiguracji")
            sessions=data.get("training",{}).get("sessions",{}); epochs=sessions.get("epochs_per_session")
            if not isinstance(epochs,list) or not epochs: errors.append("brak planu training.sessions.epochs_per_session")
            elif any(not isinstance(x,int) or x<=0 for x in epochs): errors.append("epochs_per_session musi zawierać wyłącznie dodatnie liczby całkowite")
            for k in ("runs_dir","state_dir","reports_dir"):
                if not sessions.get(k): errors.append(f"brak training.sessions.{k}")
    if (ROOT/"LICENSE").exists(): errors.append("istnieje niejednoznaczny plik LICENSE; licencja kodu GPL-3.0-or-later znajduje się w COPYING")
    for e in errors: print(f"BŁĄD: {e}",file=sys.stderr)
    if errors:return 1
    print("Kontrole integralności projektu zakończone powodzeniem."); return 0
if __name__=="__main__": raise SystemExit(main())
