#!/usr/bin/env python3
"""Provide a resilient Windows 11 setup wizard for piper-mat."""

from __future__ import annotations

import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import (
    BOTH,
    END,
    LEFT,
    RIGHT,
    X,
    BooleanVar,
    StringVar,
    Tk,
    filedialog,
    messagebox,
)
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

REPO_URL = "https://github.com/MatPomGit/piper-mat.git"
REPO_NAME = "piper-mat"
DEFAULT_PARENT = Path.home() / "Documents"
COMMAND_FAILURE = 999
COMMAND_RETRY_DELAY_SECONDS = 4
DOCTOR_TIMEOUT_SECONDS = 3700

ActionResult = tuple[bool, str]
Action = Callable[[], ActionResult]


@dataclass(frozen=True)
class Step:
    """Describe one visible wizard step."""

    number: int
    title: str
    summary: str
    explanation: str
    button_text: str
    action_name: str


STEPS = (
    Step(
        1,
        "Wybierz miejsce na projekt",
        "Wskaż folder dla piper-mat.",
        "Najprościej zostawić Dokumenty. Nie wybieraj pendrive'a ani katalogu "
        "synchronizowanego w chmurze, jeśli możesz tego uniknąć.",
        "Wybierz folder",
        "choose_folder",
    ),
    Step(
        2,
        "Pobierz albo zaktualizuj projekt",
        "Program pobierze kod z GitHub.",
        "Jeżeli projekt już istnieje, program bezpiecznie pobierze aktualizacje. "
        "Nie usuwa lokalnych wyników trenowania.",
        "Pobierz / zaktualizuj",
        "clone_or_update",
    ),
    Step(
        3,
        "Pobierz duże pliki",
        "Git LFS pobierze WAV i punkt kontrolny.",
        "Duże pliki są przechowywane osobno. Bez nich trenowanie nie ruszy. "
        "Przerwane pobieranie można uruchomić ponownie.",
        "Pobierz duże pliki",
        "git_lfs_pull",
    ),
    Step(
        4,
        "Przygotuj środowisko Pythona",
        "Powstanie prywatny folder .venv.",
        "Jeśli stare .venv jest uszkodzone, program zachowa je jako kopię i "
        "utworzy nowe.",
        "Przygotuj .venv",
        "create_venv",
    ),
    Step(
        5,
        "Zainstaluj biblioteki",
        "Program doinstaluje składniki trenowania.",
        "Pobieranie może być duże. Przy chwilowym błędzie sieci program spróbuje "
        "ponownie.",
        "Zainstaluj biblioteki",
        "install_dependencies",
    ),
    Step(
        6,
        "Zbuduj moduł treningowy",
        "Powstanie monotonic_align.",
        "Ten element wymaga kompilatora C++. Jeśli go brakuje, program wskaże "
        "potrzebny składnik Visual Studio Build Tools.",
        "Zbuduj moduł",
        "build_extension",
    ),
    Step(
        7,
        "Sprawdź nagrania",
        "Walidator przejrzy WAV i opisy.",
        "Sprawdza brakujące pliki, format, ciszę i przesterowania. Niczego nie "
        "usuwa.",
        "Sprawdź nagrania",
        "validate_dataset",
    ),
    Step(
        8,
        "Sprawdź cały komputer",
        "Uruchomiona zostanie pełna diagnostyka.",
        "Sprawdzane są Git LFS, Python, biblioteki, CUDA, punkt kontrolny, WAV, "
        "miejsce na dysku i monotonic_align.",
        "Sprawdź gotowość",
        "check_ready",
    ),
    Step(
        9,
        "Sprawdź plan trenowania",
        "Zobaczysz liczbę sesji i postęp.",
        "Po każdej sesji można wyłączyć komputer i wrócić do pracy później.",
        "Pokaż plan",
        "training_status",
    ),
    Step(
        10,
        "Uruchom następną sesję",
        "Program najpierw ponownie sprawdzi gotowość.",
        "Trenowanie ruszy tylko wtedy, gdy kontrola bezpieczeństwa przejdzie. "
        "Poprzedni punkt kontrolny pozostaje bezpieczny przy błędzie.",
        "START następnej sesji",
        "start_training",
    ),
    Step(
        11,
        "Otwórz raport",
        "Otwórz wyniki ostatniej sesji.",
        "Raport zawiera metryki i wykresy umożliwiające porównanie kolejnych "
        "sesji.",
        "Otwórz raport",
        "open_report",
    ),
)


class WindowsSetupWizard(Tk):
    """Guide the user through Windows setup and staged voice training."""

    def __init__(self) -> None:
        """Initialize wizard state and build the user interface."""
        super().__init__()
        self.title("piper-mat - kreator dla Windows 11")
        self.geometry("1180x800")
        self.minsize(980, 680)

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
        """Configure Tk styles without failing when a theme is unavailable."""
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except Exception:  # Tk may reject a theme unavailable on a given system.
            pass

        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("Step.TLabel", font=("Segoe UI", 17, "bold"))
        style.configure(
            "Big.TButton",
            font=("Segoe UI", 11, "bold"),
            padding=(14, 9),
        )

    def _build_ui(self) -> None:
        """Create all visible controls."""
        outer = ttk.Frame(self, padding=16)
        outer.pack(fill=BOTH, expand=True)

        header = ttk.Frame(outer)
        header.pack(fill=X)
        ttk.Label(
            header,
            text="Kreator przygotowania i trenowania",
            style="Title.TLabel",
        ).pack(side=LEFT)

        tools = ttk.Frame(header)
        tools.pack(side=RIGHT)
        ttk.Button(
            tools,
            text="Sprawdź system",
            command=lambda: self._run_in_background(self._diagnose),
        ).pack(side=LEFT, padx=3)
        ttk.Button(
            tools,
            text="Napraw bezpiecznie",
            command=self._ask_repair,
        ).pack(side=LEFT, padx=3)
        ttk.Button(
            tools,
            text="Otwórz folder",
            command=self._open_project_folder,
        ).pack(side=LEFT, padx=3)

        self.progress = ttk.Progressbar(
            outer,
            maximum=len(STEPS),
            value=1,
        )
        self.progress.pack(fill=X, pady=(12, 14))

        panes = ttk.Panedwindow(outer, orient="horizontal")
        panes.pack(fill=BOTH, expand=True)
        left = ttk.Frame(panes, padding=(0, 0, 12, 0))
        right = ttk.Frame(panes, padding=(12, 0, 0, 0))
        panes.add(left, weight=1)
        panes.add(right, weight=3)

        self._build_step_navigation(left)
        self._build_step_panel(right)

    def _build_step_navigation(self, parent: ttk.Frame) -> None:
        """Create the left navigation panel."""
        ttk.Label(parent, text="Kroki", font=("Segoe UI", 12, "bold")).pack(
            anchor="w"
        )

        self.step_buttons: list[ttk.Button] = []
        for index, step in enumerate(STEPS):
            button = ttk.Button(
                parent,
                text=f"{step.number}. {step.title}",
                command=lambda selected=index: self._show_step(selected),
            )
            button.pack(fill=X, pady=2)
            self.step_buttons.append(button)

        ttk.Separator(parent).pack(fill=X, pady=10)
        ttk.Label(
            parent,
            text="Szybka pomoc",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")
        ttk.Button(
            parent,
            text="Powtórz bieżący krok",
            command=self._run_current_step,
        ).pack(fill=X, pady=3)
        ttk.Button(
            parent,
            text="Pełna diagnoza",
            command=lambda: self._run_in_background(self._diagnose),
        ).pack(fill=X, pady=3)

    def _build_step_panel(self, parent: ttk.Frame) -> None:
        """Create the main step panel and technical log."""
        self.counter_label = ttk.Label(parent)
        self.counter_label.pack(anchor="w")

        self.step_title_label = ttk.Label(parent, style="Step.TLabel")
        self.step_title_label.pack(anchor="w", pady=(3, 8))

        self.summary_label = ttk.Label(parent, wraplength=720)
        self.summary_label.pack(anchor="w")

        explanation_box = ttk.LabelFrame(
            parent,
            text="Co to znaczy?",
            padding=12,
        )
        explanation_box.pack(fill=X, pady=10)
        self.explanation_label = ttk.Label(
            explanation_box,
            wraplength=700,
            justify="left",
        )
        self.explanation_label.pack(anchor="w")

        project_box = ttk.LabelFrame(parent, text="Folder projektu", padding=8)
        project_box.pack(fill=X)
        ttk.Label(
            project_box,
            textvariable=self.repo_dir,
            wraplength=700,
        ).pack(anchor="w")

        self.status_label = ttk.Label(
            parent,
            text="Gotowe.",
            font=("Segoe UI", 11, "bold"),
        )
        self.status_label.pack(anchor="w", pady=10)

        controls = ttk.Frame(parent)
        controls.pack(fill=X)
        self.action_button = ttk.Button(
            controls,
            style="Big.TButton",
            command=self._run_current_step,
        )
        self.action_button.pack(side=LEFT)
        ttk.Checkbutton(
            controls,
            text="Po sukcesie przejdź dalej",
            variable=self.auto_continue,
        ).pack(side=LEFT, padx=12)

        navigation = ttk.Frame(parent)
        navigation.pack(fill=X, pady=8)
        self.previous_button = ttk.Button(
            navigation,
            text="← Poprzedni",
            command=lambda: self._show_step(self.current_step - 1),
        )
        self.previous_button.pack(side=LEFT)
        self.next_button = ttk.Button(
            navigation,
            text="Następny →",
            command=lambda: self._show_step(self.current_step + 1),
        )
        self.next_button.pack(side=RIGHT)

        log_box = ttk.LabelFrame(parent, text="Szczegóły techniczne", padding=6)
        log_box.pack(fill=BOTH, expand=True)
        self.log = ScrolledText(
            log_box,
            height=12,
            font=("Consolas", 9),
            state="disabled",
        )
        self.log.pack(fill=BOTH, expand=True)

    def _show_step(self, index: int) -> None:
        """Display the selected step unless another action is running."""
        if self.running:
            return

        self.current_step = max(0, min(index, len(STEPS) - 1))
        step = STEPS[self.current_step]

        self.progress["value"] = self.current_step + 1
        self.counter_label.config(
            text=f"Krok {step.number} z {len(STEPS)}"
        )
        self.step_title_label.config(text=step.title)
        self.summary_label.config(text=step.summary)
        self.explanation_label.config(text=step.explanation)
        self.action_button.config(text=step.button_text)
        self.previous_button.config(
            state="normal" if self.current_step else "disabled"
        )
        self.next_button.config(
            state=(
                "normal"
                if self.current_step < len(STEPS) - 1
                else "disabled"
            )
        )
        self.status_label.config(text="Gotowe do wykonania kroku.")

    def _append_log(self, text: str) -> None:
        """Append one message to the technical log."""
        self.log.config(state="normal")
        self.log.insert(END, text.rstrip() + "\n")
        self.log.see(END)
        self.log.config(state="disabled")

    def _drain_log_queue(self) -> None:
        """Move queued messages from worker threads to the Tk text widget."""
        try:
            while True:
                self._append_log(self.log_queue.get_nowait())
        except queue.Empty:
            pass

        self.after(100, self._drain_log_queue)

    def _repo_path(self) -> Path:
        """Return the normalized repository path selected by the user."""
        return Path(self.repo_dir.get()).expanduser().resolve()

    def _venv_python(self) -> Path:
        """Return the Python executable expected inside the project venv."""
        return self._repo_path() / ".venv" / "Scripts" / "python.exe"

    def _run_command(
        self,
        command: list[str],
        cwd: Path | None = None,
        retries: int = 0,
        timeout: int | None = None,
    ) -> int:
        """Run a command, stream output to the GUI, and optionally retry."""
        return_code = COMMAND_FAILURE

        for attempt in range(retries + 1):
            display_command = subprocess.list2cmdline(
                [str(item) for item in command]
            )
            self.log_queue.put(f"> {display_command}")
            process: subprocess.Popen[str] | None = None

            try:
                process = subprocess.Popen(
                    [str(item) for item in command],
                    cwd=str(cwd) if cwd else None,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=getattr(
                        subprocess,
                        "CREATE_NO_WINDOW",
                        0,
                    ),
                )
                if process.stdout is None:
                    raise RuntimeError("Nie można odczytać wyjścia procesu.")

                for line in process.stdout:
                    self.log_queue.put(line.rstrip())
                return_code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                self.log_queue.put(f"BŁĄD: przekroczono limit czasu: {exc}")
                return_code = COMMAND_FAILURE
                if process is not None:
                    process.kill()
                    process.wait()
            except (OSError, RuntimeError) as exc:
                self.log_queue.put(f"BŁĄD: {exc}")
                return_code = COMMAND_FAILURE
                if process is not None and process.poll() is None:
                    process.kill()
                    process.wait()

            if return_code == 0:
                return 0

            if attempt < retries:
                self.log_queue.put(
                    f"Próba {attempt + 1} nie powiodła się. "
                    f"Ponawiam za {COMMAND_RETRY_DELAY_SECONDS} sekundy..."
                )
                time.sleep(COMMAND_RETRY_DELAY_SECONDS)

        return return_code

    def _run_in_background(self, action: Action) -> None:
        """Execute a long action on a worker thread."""
        if self.running:
            return

        self.running = True
        self.status_label.config(text="Pracuję... nie zamykaj programu.")
        self.action_button.config(state="disabled")
        worker = threading.Thread(
            target=self._background_worker,
            args=(action,),
            daemon=True,
        )
        worker.start()

    def _background_worker(self, action: Action) -> None:
        """Run an action and marshal its result back to the Tk thread."""
        try:
            success, message = action()
        except Exception as exc:  # Guard the GUI boundary against worker failure.
            success = False
            message = f"Nieoczekiwany błąd: {exc}"
            self.log_queue.put(repr(exc))

        self.after(
            0,
            lambda: self._finish_action(success, message),
        )

    def _finish_action(self, success: bool, message: str) -> None:
        """Restore controls and present the result of a completed action."""
        self.running = False
        self.action_button.config(state="normal")
        prefix = "✓ " if success else "✗ "
        self.status_label.config(text=prefix + message)

        if not success:
            messagebox.showerror(
                "Problem",
                message
                + "\n\nKliknij „Napraw bezpiecznie” albo przeczytaj log na dole.",
            )
            return

        if self.auto_continue.get() and self.current_step < len(STEPS) - 1:
            self.after(600, lambda: self._show_step(self.current_step + 1))

    def _run_current_step(self) -> None:
        """Run the action associated with the currently displayed step."""
        if self.running:
            return

        step = STEPS[self.current_step]
        if step.action_name == "choose_folder":
            self._action_choose_folder()
            return

        if step.action_name == "start_training":
            confirmed = messagebox.askyesno(
                "Uruchomić trenowanie?",
                "Trenowanie może trwać wiele godzin. Przed startem program "
                "wykona jeszcze kontrolę bezpieczeństwa. Kontynuować?",
            )
            if not confirmed:
                return

        action = getattr(self, f"_action_{step.action_name}")
        self._run_in_background(action)

    def _ask_repair(self) -> None:
        """Ask for confirmation before running safe repair operations."""
        confirmed = messagebox.askyesno(
            "Bezpieczna naprawa",
            "Program spróbuje naprawić Git LFS, .venv i biblioteki. Nie usunie "
            "nagrań, punktów kontrolnych ani wyników trenowania. Kontynuować?",
        )
        if confirmed:
            self._run_in_background(self._repair)

    def _run_doctor(self, repair: bool = False) -> ActionResult:
        """Run windows_doctor.py in diagnostic or repair mode."""
        repo = self._repo_path()
        script = repo / "tools" / "windows_doctor.py"
        if not script.is_file():
            return False, "Najpierw pobierz lub zaktualizuj repozytorium."

        command = [sys.executable, str(script)]
        if repair:
            command.append("--repair")

        return_code = self._run_command(
            command,
            cwd=repo,
            timeout=DOCTOR_TIMEOUT_SECONDS,
        )
        if return_code not in (0, 2):
            return False, "Nie udało się uruchomić diagnostyki."
        if return_code == 0:
            return True, "System jest gotowy."
        return False, "Pozostały problemy wymagające uwagi. Zobacz log."

    def _diagnose(self) -> ActionResult:
        """Run system diagnostics."""
        return self._run_doctor(False)

    def _repair(self) -> ActionResult:
        """Run safe system repairs followed by diagnostics."""
        return self._run_doctor(True)

    def _open_project_folder(self) -> None:
        """Open the repository or selected parent directory in Explorer."""
        repo = self._repo_path()
        path = repo if repo.exists() else Path(self.parent_dir.get())
        if path.exists():
            os.startfile(path)

    def _action_choose_folder(self) -> ActionResult:
        """Select a parent directory and update the repository path."""
        selected = filedialog.askdirectory(
            initialdir=self.parent_dir.get(),
            title="Wybierz folder nadrzędny",
        )
        if not selected:
            return True, "Nie zmieniono folderu."

        parent = Path(selected)
        repo = parent if parent.name.lower() == REPO_NAME else parent / REPO_NAME
        self.parent_dir.set(str(parent))
        self.repo_dir.set(str(repo))
        self.status_label.config(text="✓ Folder wybrany.")
        return True, "Folder wybrany."

    def _action_clone_or_update(self) -> ActionResult:
        """Clone piper-mat or safely fast-forward an existing checkout."""
        repo = self._repo_path()
        git = shutil.which("git")
        if not git:
            return (
                False,
                "Brak Git. Uruchom program ponownie przez "
                "START_PIPER_MAT_GUI.bat.",
            )

        if (repo / ".git").is_dir():
            self._run_command(
                [git, "config", "--local", "core.longpaths", "true"],
                cwd=repo,
            )
            if self._run_command(
                [git, "status", "--porcelain"],
                cwd=repo,
            ) != 0:
                return False, "Repozytorium Git jest uszkodzone lub niedostępne."

            if self._run_command(
                [git, "fetch", "--prune", "origin"],
                cwd=repo,
                retries=2,
                timeout=300,
            ) != 0:
                return (
                    False,
                    "Nie udało się połączyć z GitHub. Sprawdź połączenie i "
                    "spróbuj ponownie.",
                )

            return_code = self._run_command(
                [git, "pull", "--ff-only"],
                cwd=repo,
                retries=1,
                timeout=300,
            )
            if return_code == 0:
                return True, "Repozytorium jest aktualne."
            return (
                False,
                "Nie można bezpiecznie scalić aktualizacji. Lokalne pliki nie "
                "zostały nadpisane.",
            )

        if repo.exists() and any(repo.iterdir()):
            return (
                False,
                f"Folder {repo} nie jest pusty i nie jest repozytorium. "
                "Wybierz inne miejsce.",
            )

        repo.parent.mkdir(parents=True, exist_ok=True)
        return_code = self._run_command(
            [git, "clone", REPO_URL, str(repo)],
            cwd=repo.parent,
            retries=2,
            timeout=900,
        )
        if return_code == 0:
            return True, "Projekt pobrany."
        return False, "Nie udało się pobrać projektu po kilku próbach."

    def _require_repo(self) -> ActionResult:
        """Verify that the selected folder contains a Git repository."""
        repo = self._repo_path()
        if (repo / ".git").is_dir():
            return True, ""
        return False, "Najpierw pobierz repozytorium."

    def _action_git_lfs_pull(self) -> ActionResult:
        """Initialize Git LFS locally and download large project files."""
        ready, message = self._require_repo()
        if not ready:
            return ready, message

        git = shutil.which("git")
        if not git:
            return False, "Brak Git."

        repo = self._repo_path()
        if self._run_command([git, "lfs", "version"], cwd=repo) != 0:
            return (
                False,
                "Brakuje Git LFS. Zamknij GUI i uruchom "
                "START_PIPER_MAT_GUI.bat ponownie.",
            )

        self._run_command(
            [git, "lfs", "install", "--local"],
            cwd=repo,
        )
        return_code = self._run_command(
            [git, "lfs", "pull"],
            cwd=repo,
            retries=3,
            timeout=3600,
        )
        if return_code == 0:
            return True, "Duże pliki pobrane."
        return (
            False,
            "Git LFS nadal nie może pobrać plików. Sprawdź połączenie i wolne "
            "miejsce na dysku.",
        )

    def _action_create_venv(self) -> ActionResult:
        """Create or safely replace the project virtual environment."""
        ready, message = self._require_repo()
        if not ready:
            return ready, message

        repo = self._repo_path()
        python = self._venv_python()
        if python.is_file():
            return_code = self._run_command(
                [str(python), "-c", "import sys, pip; print(sys.version)"],
                cwd=repo,
            )
            if return_code == 0:
                return True, "Istniejące .venv działa poprawnie."

        venv = repo / ".venv"
        if venv.exists():
            backup = repo / f".venv_broken_{datetime.now():%Y%m%d_%H%M%S}"
            venv.rename(backup)
            self.log_queue.put(
                f"Uszkodzone środowisko zachowano jako {backup.name}"
            )

        return_code = self._run_command(
            [sys.executable, "-m", "venv", ".venv"],
            cwd=repo,
            timeout=240,
        )
        if return_code == 0 and self._venv_python().is_file():
            return True, "Środowisko .venv jest gotowe."
        return False, "Nie udało się utworzyć .venv."

    def _action_install_dependencies(self) -> ActionResult:
        """Install or update the Python dependencies required for training."""
        ready, message = self._require_repo()
        if not ready:
            return ready, message

        python = self._venv_python()
        repo = self._repo_path()
        if not python.is_file():
            return False, "Najpierw przygotuj .venv."

        commands = (
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip",
                "setuptools",
                "wheel",
            ],
            [str(python), "-m", "pip", "install", "-e", ".[train]"],
        )
        for command in commands:
            if self._run_command(
                command,
                cwd=repo,
                retries=2,
                timeout=3600,
            ) != 0:
                return (
                    False,
                    "Instalacja bibliotek nie powiodła się po kilku próbach.",
                )

        return True, "Biblioteki są zainstalowane."

    def _action_build_extension(self) -> ActionResult:
        """Build and verify the monotonic_align Cython extension."""
        ready, message = self._require_repo()
        if not ready:
            return ready, message

        python = self._venv_python()
        repo = self._repo_path()
        source = repo / "src" / "piper" / "train" / "vits" / "monotonic_align"
        target = source / "monotonic_align"
        target.mkdir(exist_ok=True)

        if not python.is_file():
            return False, "Brak .venv."

        return_code = self._run_command(
            [str(python), "-m", "Cython.Build.Cythonize", "-i", "core.pyx"],
            cwd=source,
            timeout=600,
        )
        if return_code != 0:
            return (
                False,
                "Nie udało się zbudować modułu. Zainstaluj Visual Studio 2022 "
                "Build Tools z komponentem Desktop development with C++, "
                "uruchom ponownie Windows i ponów krok.",
            )

        for built in source.glob("core*.pyd"):
            destination = target / built.name
            if destination.exists():
                destination.unlink()
            shutil.move(str(built), str(destination))

        return_code = self._run_command(
            [
                str(python),
                "-c",
                "from piper.train.vits.monotonic_align import core; print('OK')",
            ],
            cwd=repo,
        )
        if return_code == 0:
            return True, "monotonic_align działa."
        return False, "Moduł powstał, ale Python nie może go zaimportować."

    def _action_validate_dataset(self) -> ActionResult:
        """Run the project's full dataset validator."""
        ready, message = self._require_repo()
        if not ready:
            return ready, message

        python = self._venv_python()
        if not python.is_file():
            return False, "Najpierw przygotuj .venv."

        return_code = self._run_command(
            [
                str(python),
                "scripts/validate_dataset.py",
                "--metadata",
                "dataset/metadata.csv",
                "--audio-dir",
                "dataset/wavs",
            ],
            cwd=self._repo_path(),
            timeout=3600,
        )
        if return_code == 0:
            return True, "Nagrania są poprawne."
        return False, "Walidator wykrył problem. Zobacz log."

    def _action_check_ready(self) -> ActionResult:
        """Run the full readiness diagnostic."""
        return self._diagnose()

    def _action_training_status(self) -> ActionResult:
        """Display the staged training plan and current progress."""
        python = self._venv_python()
        if not python.is_file():
            return False, "Najpierw przygotuj .venv."

        return_code = self._run_command(
            [str(python), "scripts/train_sessions.py", "--status"],
            cwd=self._repo_path(),
        )
        if return_code == 0:
            return True, "Plan pokazano w logu."
        return False, "Nie udało się odczytać planu."

    def _action_start_training(self) -> ActionResult:
        """Validate readiness and start the next staged training session."""
        ready, _ = self._diagnose()
        if not ready:
            return (
                False,
                "Diagnostyka wykryła problem. Trenowanie nie zostało uruchomione.",
            )

        python = self._venv_python()
        return_code = self._run_command(
            [str(python), "scripts/train_sessions.py"],
            cwd=self._repo_path(),
        )
        if return_code == 0:
            return True, "Sesja zakończona i zapisana."
        return (
            False,
            "Sesja zakończyła się błędem. Poprzedni punkt kontrolny pozostaje "
            "bezpieczny.",
        )

    def _latest_report(self) -> Path | None:
        """Return the newest staged-training report, if one exists."""
        reports_dir = self._repo_path() / "output" / "training_reports"
        if not reports_dir.is_dir():
            return None

        reports = list(reports_dir.glob("session_*/REPORT.md"))
        if not reports:
            return None
        return max(reports, key=lambda path: path.stat().st_mtime_ns)

    def _action_open_report(self) -> ActionResult:
        """Open the newest training report in the associated application."""
        report = self._latest_report()
        if report is None:
            return False, "Nie ma jeszcze raportu."

        os.startfile(report)
        return True, "Otwarto ostatni raport."


def main() -> int:
    """Start the Windows setup wizard."""
    if os.name != "nt":
        print("Ten kreator jest przeznaczony dla Windows 11.")
        return 2

    WindowsSetupWizard().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
