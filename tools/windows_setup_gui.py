#!/usr/bin/env python3
"""Prosty kreator przygotowania i treningu piper-mat dla Windows 11."""

from __future__ import annotations

import os
import queue
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, X, BooleanVar, StringVar, Tk, filedialog, messagebox
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

REPO_URL = "https://github.com/MatPomGit/piper-mat.git"
REPO_NAME = "piper-mat"
DEFAULT_PARENT = Path.home() / "Documents"


@dataclass(frozen=True)
class Step:
    number: int
    title: str
    short: str
    explanation: str
    button: str
    action: str


STEPS = [
    Step(1, "Wybierz miejsce na projekt", "Wskaż folder, w którym ma znaleźć się piper-mat.", "Najprościej zostawić domyślny folder Dokumenty. Program utworzy w nim katalog „piper-mat”. Nie wybieraj pendrive'a ani katalogu tymczasowego.", "Wybierz folder", "choose_folder"),
    Step(2, "Pobierz albo zaktualizuj repozytorium", "Program pobierze pliki projektu z GitHub.", "Repozytorium to po prostu folder z kodem programu. Jeśli masz go już na komputerze, ten krok tylko pobierze najnowsze zmiany. Twoje lokalne wyniki treningu nie są przez to usuwane.", "Pobierz / zaktualizuj", "clone_or_update"),
    Step(3, "Pobierz duże pliki treningowe", "Git LFS pobierze nagrania WAV i bazowy checkpoint.", "Część plików jest zbyt duża dla zwykłego Git. Git LFS przechowuje je osobno. Ten krok może potrwać i pobrać dużo danych. Bez niego trening nie ruszy.", "Pobierz duże pliki", "git_lfs_pull"),
    Step(4, "Utwórz prywatne środowisko Pythona", "Program utworzy folder .venv tylko dla tego projektu.", "To osobny, bezpieczny zestaw bibliotek. Dzięki temu instalacja Pipera nie miesza się z innymi programami na komputerze. Ten krok wykonuje się zwykle tylko raz.", "Utwórz środowisko", "create_venv"),
    Step(5, "Zainstaluj biblioteki do treningu", "Zainstalowane zostaną PyTorch, Lightning i pozostałe składniki.", "To właściwe narzędzia, których Piper potrzebuje do uczenia głosu. Pobieranie może potrwać kilka minut i zajmie kilka GB. Nie zamykaj okna w trakcie instalacji.", "Zainstaluj biblioteki", "install_dependencies"),
    Step(6, "Zbuduj brakujący moduł treningowy", "Program skompiluje monotonic_align wymagany przez Piper.", "To techniczny moduł używany podczas dopasowywania tekstu do dźwięku. Jeśli Windows nie ma potrzebnych narzędzi C++, program pokaże czytelny komunikat. Trzeba wtedy doinstalować Visual Studio 2022 Build Tools z opcją „Desktop development with C++”.", "Zbuduj moduł", "build_extension"),
    Step(7, "Sprawdź nagrania", "Program sprawdzi metadane i pliki WAV przed treningiem.", "Ten krok nie zmienia nagrań. Szuka brakujących plików, złego formatu, ciszy, przesterowania i innych problemów, które mogłyby zepsuć trening.", "Sprawdź nagrania", "validate_dataset"),
    Step(8, "Sprawdź, czy komputer jest gotowy", "Uruchomiona zostanie pełna kontrola konfiguracji treningu.", "Program sprawdzi m.in. checkpoint, Git LFS, moduły Pythona, moduł monotonic_align, miejsce na dysku i możliwość odczytania checkpointu na Windows. Zielony wynik oznacza, że można trenować.", "Sprawdź gotowość", "check_ready"),
    Step(9, "Sprawdź plan treningu", "Zobaczysz liczbę zaplanowanych sesji i aktualny postęp.", "Trening jest podzielony na kilka podejść. Po każdej sesji zapisuje się checkpoint i raport. Możesz wyłączyć komputer i wrócić do treningu następnego dnia.", "Pokaż plan", "training_status"),
    Step(10, "Uruchom następną sesję treningu", "Piper będzie trenował do końca najbliższego zaplanowanego etapu.", "To długi krok. Podczas treningu komputer będzie mocno używał GPU. Po zakończeniu program zapisze postęp, najlepsze checkpointy i raport z wykresami. Dopiero wtedy bezpiecznie wyłącz komputer.", "START następnej sesji", "start_training"),
    Step(11, "Otwórz raport z ostatniej sesji", "Po treningu możesz obejrzeć opis wyników i wykresy.", "Raport pokazuje przebieg metryk treningowych. Nie musisz rozumieć każdego wykresu. Najważniejsze jest, że raport pozwala porównać kolejne sesje i wykryć pogorszenie modelu.", "Otwórz raport", "open_report"),
]


class Wizard(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("piper-mat — kreator treningu dla Windows 11")
        self.geometry("1080x760")
        self.minsize(900, 640)
        self.parent_dir = StringVar(value=str(DEFAULT_PARENT))
        self.repo_dir = StringVar(value=str(DEFAULT_PARENT / REPO_NAME))
        self.current_step = 0
        self.running = False
        self.auto_continue = BooleanVar(value=False)
        self.log_queue: queue.Queue[str] = queue.Queue()
        self._configure_style()
        self._build_ui()
        self._show_step(0)
        self.after(100, self._drain_log_queue)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except Exception:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("Step.TLabel", font=("Segoe UI", 17, "bold"))
        style.configure("Body.TLabel", font=("Segoe UI", 11))
        style.configure("Big.TButton", font=("Segoe UI", 11, "bold"), padding=(14, 10))
        style.configure("Nav.TButton", padding=(10, 8))

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=18)
        outer.pack(fill=BOTH, expand=True)
        header = ttk.Frame(outer)
        header.pack(fill=X)
        ttk.Label(header, text="Kreator przygotowania i treningu", style="Title.TLabel").pack(side=LEFT)
        ttk.Label(header, text="Windows 11", style="Body.TLabel").pack(side=RIGHT)
        self.progress = ttk.Progressbar(outer, maximum=len(STEPS), value=1)
        self.progress.pack(fill=X, pady=(14, 16))
        main = ttk.Panedwindow(outer, orient="horizontal")
        main.pack(fill=BOTH, expand=True)
        left = ttk.Frame(main, padding=(0, 0, 14, 0))
        right = ttk.Frame(main, padding=(14, 0, 0, 0))
        main.add(left, weight=1)
        main.add(right, weight=3)
        ttk.Label(left, text="Kroki", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))
        for idx, step in enumerate(STEPS):
            ttk.Button(left, text=f"{step.number}. {step.title}", command=lambda i=idx: self._show_step(i), width=30).pack(fill=X, pady=2)
        self.step_counter = ttk.Label(right, text="", style="Body.TLabel")
        self.step_counter.pack(anchor="w")
        self.step_title = ttk.Label(right, text="", style="Step.TLabel")
        self.step_title.pack(anchor="w", pady=(4, 10))
        self.step_short = ttk.Label(right, text="", style="Body.TLabel", wraplength=680)
        self.step_short.pack(anchor="w", pady=(0, 8))
        explanation_box = ttk.LabelFrame(right, text="Co to znaczy?", padding=14)
        explanation_box.pack(fill=X, pady=(4, 12))
        self.step_explanation = ttk.Label(explanation_box, text="", style="Body.TLabel", wraplength=650, justify="left")
        self.step_explanation.pack(anchor="w")
        path_box = ttk.LabelFrame(right, text="Folder projektu", padding=10)
        path_box.pack(fill=X, pady=(0, 10))
        ttk.Label(path_box, textvariable=self.repo_dir, wraplength=650).pack(anchor="w")
        self.status = ttk.Label(right, text="Gotowe do wykonania kroku.", font=("Segoe UI", 11, "bold"))
        self.status.pack(anchor="w", pady=(4, 10))
        controls = ttk.Frame(right)
        controls.pack(fill=X, pady=(0, 12))
        self.action_button = ttk.Button(controls, text="", style="Big.TButton", command=self._run_current_step)
        self.action_button.pack(side=LEFT)
        ttk.Checkbutton(controls, text="Po sukcesie przejdź automatycznie do następnego kroku", variable=self.auto_continue).pack(side=LEFT, padx=14)
        nav = ttk.Frame(right)
        nav.pack(fill=X, pady=(0, 10))
        self.prev_button = ttk.Button(nav, text="← Poprzedni krok", style="Nav.TButton", command=lambda: self._show_step(self.current_step - 1))
        self.prev_button.pack(side=LEFT)
        self.next_button = ttk.Button(nav, text="Następny krok →", style="Nav.TButton", command=lambda: self._show_step(self.current_step + 1))
        self.next_button.pack(side=RIGHT)
        log_box = ttk.LabelFrame(right, text="Szczegóły techniczne — możesz je zignorować, jeśli wszystko działa", padding=8)
        log_box.pack(fill=BOTH, expand=True)
        self.log = ScrolledText(log_box, height=10, font=("Consolas", 9), state="disabled")
        self.log.pack(fill=BOTH, expand=True)

    def _show_step(self, index: int) -> None:
        if self.running:
            return
        self.current_step = max(0, min(index, len(STEPS) - 1))
        step = STEPS[self.current_step]
        self.progress["value"] = self.current_step + 1
        self.step_counter.config(text=f"Krok {step.number} z {len(STEPS)}")
        self.step_title.config(text=step.title)
        self.step_short.config(text=step.short)
        self.step_explanation.config(text=step.explanation)
        self.action_button.config(text=step.button)
        self.prev_button.config(state="normal" if self.current_step > 0 else "disabled")
        self.next_button.config(state="normal" if self.current_step < len(STEPS) - 1 else "disabled")
        self.status.config(text="Gotowe do wykonania kroku.")

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert(END, text.rstrip() + "\n")
        self.log.see(END)
        self.log.configure(state="disabled")

    def _drain_log_queue(self) -> None:
        while True:
            try:
                item = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self._append_log(item)
        self.after(100, self._drain_log_queue)

    def _repo_path(self) -> Path:
        return Path(self.repo_dir.get()).expanduser().resolve()

    def _venv_python(self) -> Path:
        return self._repo_path() / ".venv" / "Scripts" / "python.exe"

    def _run_command(self, command: list[str], cwd: Path | None = None) -> int:
        self.log_queue.put("> " + subprocess.list2cmdline(command))
        process = subprocess.Popen(command, cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        assert process.stdout is not None
        for line in process.stdout:
            self.log_queue.put(line.rstrip())
        return process.wait()

    def _run_current_step(self) -> None:
        if self.running:
            return
        step = STEPS[self.current_step]
        action = getattr(self, f"_action_{step.action}")
        if step.action == "choose_folder":
            action()
            return
        if step.action == "start_training" and not messagebox.askyesno("Uruchomić trening?", "Trening może trwać wiele godzin i mocno obciąży kartę graficzną.\n\nPo zakończeniu sesji program zapisze checkpoint i raport.\n\nCzy uruchomić następną sesję teraz?"):
            return
        self.running = True
        self.status.config(text="Pracuję... nie zamykaj programu.")
        self.action_button.config(state="disabled")
        self.prev_button.config(state="disabled")
        self.next_button.config(state="disabled")
        threading.Thread(target=self._execute_action, args=(action,), daemon=True).start()

    def _execute_action(self, action) -> None:
        try:
            ok, message = action()
        except Exception as exc:  # noqa: BLE001
            ok, message = False, f"Nie udało się wykonać kroku: {exc}"
            self.log_queue.put(f"BŁĄD: {exc!r}")
        self.after(0, lambda: self._finish_action(ok, message))

    def _finish_action(self, ok: bool, message: str) -> None:
        self.running = False
        self.status.config(text=("✓ " if ok else "✗ ") + message)
        self.action_button.config(state="normal")
        self.prev_button.config(state="normal" if self.current_step > 0 else "disabled")
        self.next_button.config(state="normal" if self.current_step < len(STEPS) - 1 else "disabled")
        if ok and self.auto_continue.get() and self.current_step < len(STEPS) - 1:
            self.after(700, lambda: self._show_step(self.current_step + 1))
        if not ok:
            messagebox.showerror("Ten krok wymaga uwagi", message + "\n\nSzczegóły są widoczne w dolnym polu programu.")

    def _action_choose_folder(self):
        selected = filedialog.askdirectory(initialdir=self.parent_dir.get(), title="Wybierz folder nadrzędny dla piper-mat")
        if selected:
            parent = Path(selected)
            self.parent_dir.set(str(parent))
            self.repo_dir.set(str(parent if parent.name.lower() == REPO_NAME else parent / REPO_NAME))
            self.status.config(text="✓ Folder wybrany. Możesz przejść dalej.")
        return True, "Folder wybrany."

    def _action_clone_or_update(self):
        repo = self._repo_path()
        if not shutil.which("git"):
            return False, "Nie znaleziono programu Git. Uruchom kreator przez START_PIPER_MAT_GUI.bat albo zainstaluj Git for Windows."
        if (repo / ".git").is_dir():
            rc = self._run_command(["git", "pull", "--ff-only"], cwd=repo)
            return rc == 0, "Repozytorium jest aktualne." if rc == 0 else "Git nie mógł zaktualizować repozytorium."
        if repo.exists() and any(repo.iterdir()):
            return False, f"Folder {repo} istnieje i nie jest pusty. Wybierz inny folder albo wskaż istniejące repozytorium."
        repo.parent.mkdir(parents=True, exist_ok=True)
        rc = self._run_command(["git", "clone", REPO_URL, str(repo)], cwd=repo.parent)
        return rc == 0, "Repozytorium zostało pobrane." if rc == 0 else "Nie udało się pobrać repozytorium."

    def _require_repo(self) -> tuple[bool, str]:
        return ((True, "") if (self._repo_path() / ".git").is_dir() else (False, "Najpierw wykonaj krok pobierania repozytorium."))

    def _action_git_lfs_pull(self):
        ok, msg = self._require_repo()
        if not ok:
            return ok, msg
        repo = self._repo_path()
        if self._run_command(["git", "lfs", "install"], cwd=repo) != 0:
            return False, "Git LFS nie działa. Zaktualizuj Git for Windows i spróbuj ponownie."
        rc = self._run_command(["git", "lfs", "pull"], cwd=repo)
        return rc == 0, "Duże pliki zostały pobrane." if rc == 0 else "Nie udało się pobrać plików Git LFS."

    def _action_create_venv(self):
        ok, msg = self._require_repo()
        if not ok:
            return ok, msg
        rc = self._run_command([sys.executable, "-m", "venv", ".venv"], cwd=self._repo_path())
        return (True, "Prywatne środowisko Pythona jest gotowe.") if rc == 0 and self._venv_python().is_file() else (False, "Nie udało się utworzyć środowiska .venv.")

    def _action_install_dependencies(self):
        ok, msg = self._require_repo()
        if not ok:
            return ok, msg
        py = self._venv_python()
        if not py.is_file():
            return False, "Najpierw utwórz środowisko .venv w poprzednim kroku."
        for command in ([str(py), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], [str(py), "-m", "pip", "install", "-e", ".[train]"]):
            if self._run_command(list(command), cwd=self._repo_path()) != 0:
                return False, "Instalacja bibliotek nie powiodła się. Sprawdź szczegóły na dole okna."
        return True, "Biblioteki do treningu są zainstalowane."

    def _action_build_extension(self):
        ok, msg = self._require_repo()
        if not ok:
            return ok, msg
        py = self._venv_python()
        if not py.is_file():
            return False, "Najpierw utwórz .venv i zainstaluj biblioteki."
        source_dir = self._repo_path() / "src" / "piper" / "train" / "vits" / "monotonic_align"
        target_dir = source_dir / "monotonic_align"
        target_dir.mkdir(exist_ok=True)
        for old in source_dir.glob("core*.pyd"):
            old.unlink(missing_ok=True)
        rc = self._run_command([str(py), "-m", "Cython.Build.Cythonize", "-i", "core.pyx"], cwd=source_dir)
        if rc != 0:
            self.log_queue.put("Najczęstsza przyczyna: brak Visual Studio 2022 Build Tools z pakietem 'Desktop development with C++'.")
            return False, "Nie udało się skompilować monotonic_align. Najprawdopodobniej brakuje narzędzi C++ dla Windows."
        built = list(source_dir.glob("core*.pyd"))
        if not built:
            return False, "Cython zakończył pracę, ale nie znaleziono pliku core*.pyd."
        for file in built:
            destination = target_dir / file.name
            if destination.exists():
                destination.unlink()
            shutil.move(str(file), destination)
        rc = self._run_command([str(py), "-c", "from piper.train.vits.monotonic_align import core; print('monotonic_align OK')"], cwd=self._repo_path())
        return rc == 0, "Moduł monotonic_align został zbudowany i działa." if rc == 0 else "Plik .pyd powstał, ale Python nie potrafi go zaimportować."

    def _action_validate_dataset(self):
        ok, msg = self._require_repo()
        if not ok:
            return ok, msg
        py = self._venv_python()
        if not py.is_file():
            return False, "Brak .venv. Wykonaj wcześniejsze kroki instalacji."
        rc = self._run_command([str(py), "scripts/validate_dataset.py", "--metadata", "dataset/metadata.csv", "--audio-dir", "dataset/wavs"], cwd=self._repo_path())
        return rc == 0, "Nagrania przeszły kontrolę." if rc == 0 else "Walidator znalazł problem z nagraniami lub metadanymi."

    def _action_check_ready(self):
        ok, msg = self._require_repo()
        if not ok:
            return ok, msg
        py = self._venv_python()
        if not py.is_file():
            return False, "Brak .venv. Wykonaj wcześniejsze kroki instalacji."
        rc = self._run_command([str(py), "scripts/check_training_ready.py"], cwd=self._repo_path())
        return rc == 0, "Komputer i projekt są gotowe do treningu." if rc == 0 else "Projekt nie jest jeszcze gotowy. Przeczytaj komunikaty w logu."

    def _action_training_status(self):
        ok, msg = self._require_repo()
        if not ok:
            return ok, msg
        py = self._venv_python()
        if not py.is_file():
            return False, "Brak .venv."
        rc = self._run_command([str(py), "scripts/train_sessions.py", "--status"], cwd=self._repo_path())
        return rc == 0, "Plan treningu został pokazany w szczegółach poniżej." if rc == 0 else "Nie udało się odczytać planu treningu."

    def _action_start_training(self):
        ok, msg = self._require_repo()
        if not ok:
            return ok, msg
        py = self._venv_python()
        if not py.is_file():
            return False, "Brak .venv. Wykonaj kroki przygotowania."
        repo = self._repo_path()
        if self._run_command([str(py), "scripts/check_training_ready.py"], cwd=repo) != 0:
            return False, "Kontrola gotowości nie przeszła. Trening nie został uruchomiony, żeby nie zmarnować czasu."
        rc = self._run_command([str(py), "scripts/train_sessions.py"], cwd=repo)
        return rc == 0, "Sesja treningu zakończona. Postęp i raport zostały zapisane." if rc == 0 else "Sesja została przerwana lub zakończyła się błędem. Poprzedni zapis postępu pozostaje bezpieczny."

    def _latest_report(self) -> Path | None:
        reports = self._repo_path() / "output" / "training_reports"
        matches = list(reports.glob("session_*/REPORT.md")) if reports.is_dir() else []
        return max(matches, key=lambda p: p.stat().st_mtime_ns) if matches else None

    def _action_open_report(self):
        report = self._latest_report()
        if report is None:
            return False, "Nie ma jeszcze raportu. Najpierw zakończ co najmniej jedną sesję treningu."
        os.startfile(report)  # type: ignore[attr-defined]
        self.log_queue.put(f"Raport: {report}")
        self.log_queue.put(f"Wykresy: {report.parent}")
        return True, "Otwarto raport z ostatniej sesji."


def main() -> int:
    if os.name != "nt":
        print("Ten kreator jest przeznaczony dla Windows 11.")
        return 2
    Wizard().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
