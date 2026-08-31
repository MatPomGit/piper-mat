#!/usr/bin/env python3
"""Odporny na typowe błędy kreator piper-mat dla Windows 11."""
from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, X, BooleanVar, StringVar, Tk, filedialog, messagebox
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

REPO_URL = "https://github.com/MatPomGit/piper-mat.git"
REPO_NAME = "piper-mat"
DEFAULT_PARENT = Path.home() / "Documents"

@dataclass(frozen=True)
class Step:
    n: int; title: str; short: str; explanation: str; button: str; action: str

STEPS = [
    Step(1,"Wybierz miejsce na projekt","Wskaż folder dla piper-mat.","Najprościej zostawić Dokumenty. Nie wybieraj pendrive'a ani katalogu synchronizowanego w chmurze, jeśli możesz tego uniknąć.","Wybierz folder","choose_folder"),
    Step(2,"Pobierz albo zaktualizuj projekt","Program pobierze kod z GitHub.","Jeżeli projekt już istnieje, program bezpiecznie pobierze aktualizacje. Nie usuwa lokalnych wyników treningu.","Pobierz / zaktualizuj","clone_or_update"),
    Step(3,"Pobierz duże pliki","Git LFS pobierze WAV i checkpoint.","Duże pliki są przechowywane osobno. Bez tego trening nie ruszy. Zerwane pobieranie można uruchomić ponownie.","Pobierz duże pliki","git_lfs_pull"),
    Step(4,"Przygotuj środowisko Pythona","Powstanie prywatny folder .venv.","Jeśli stare .venv jest uszkodzone, program zachowa je jako kopię i utworzy nowe.","Przygotuj .venv","create_venv"),
    Step(5,"Zainstaluj biblioteki","Program doinstaluje składniki treningowe.","Pobieranie może być duże. Przy chwilowym błędzie Internetu program spróbuje ponownie.","Zainstaluj biblioteki","install_dependencies"),
    Step(6,"Zbuduj moduł treningowy","Powstanie monotonic_align.","To element wymagający kompilatora C++. Jeśli go brakuje, dostaniesz prostą instrukcję instalacji Visual Studio Build Tools.","Zbuduj moduł","build_extension"),
    Step(7,"Sprawdź nagrania","Walidator przejrzy WAV i opisy.","Sprawdza brakujące pliki, format, ciszę i przesterowania. Niczego nie usuwa.","Sprawdź nagrania","validate_dataset"),
    Step(8,"Sprawdź cały komputer","Uruchomiona zostanie pełna diagnostyka.","Sprawdzane są Git LFS, Python, biblioteki, CUDA, checkpoint, WAV, miejsce na dysku i monotonic_align.","Sprawdź gotowość","check_ready"),
    Step(9,"Sprawdź plan treningu","Zobaczysz liczbę sesji i postęp.","Po każdej sesji można wyłączyć komputer i wrócić do pracy później.","Pokaż plan","training_status"),
    Step(10,"Uruchom następną sesję","Program najpierw ponownie sprawdzi gotowość.","Trening ruszy tylko wtedy, gdy kontrola bezpieczeństwa przejdzie. Poprzedni checkpoint pozostaje bezpieczny przy błędzie.","START następnej sesji","start_training"),
    Step(11,"Otwórz raport","Otwórz wyniki ostatniej sesji.","Raport zawiera metryki i wykresy. Możesz porównywać kolejne podejścia.","Otwórz raport","open_report"),
]

class Wizard(Tk):
    def __init__(self):
        super().__init__(); self.title("piper-mat — kreator dla Windows 11"); self.geometry("1180x800"); self.minsize(980,680)
        self.parent_dir=StringVar(value=str(DEFAULT_PARENT)); self.repo_dir=StringVar(value=str(DEFAULT_PARENT/REPO_NAME)); self.current=0; self.running=False
        self.auto_continue=BooleanVar(value=False); self.q: queue.Queue[str]=queue.Queue(); self._style(); self._ui(); self._show(0); self.after(100,self._drain)
    def _style(self):
        s=ttk.Style(self)
        try:s.theme_use("vista")
        except Exception:pass
        s.configure("Title.TLabel",font=("Segoe UI",22,"bold")); s.configure("Step.TLabel",font=("Segoe UI",17,"bold")); s.configure("Big.TButton",font=("Segoe UI",11,"bold"),padding=(14,9))
    def _ui(self):
        outer=ttk.Frame(self,padding=16); outer.pack(fill=BOTH,expand=True)
        h=ttk.Frame(outer); h.pack(fill=X); ttk.Label(h,text="Kreator przygotowania i treningu",style="Title.TLabel").pack(side=LEFT)
        tools=ttk.Frame(h); tools.pack(side=RIGHT)
        ttk.Button(tools,text="Sprawdź system",command=lambda:self._background(self._diagnose)).pack(side=LEFT,padx=3)
        ttk.Button(tools,text="Napraw bezpiecznie",command=self._ask_repair).pack(side=LEFT,padx=3)
        ttk.Button(tools,text="Otwórz folder",command=self._open_folder).pack(side=LEFT,padx=3)
        self.progress=ttk.Progressbar(outer,maximum=len(STEPS),value=1); self.progress.pack(fill=X,pady=(12,14))
        p=ttk.Panedwindow(outer,orient="horizontal"); p.pack(fill=BOTH,expand=True); left=ttk.Frame(p,padding=(0,0,12,0)); right=ttk.Frame(p,padding=(12,0,0,0)); p.add(left,weight=1); p.add(right,weight=3)
        ttk.Label(left,text="Kroki",font=("Segoe UI",12,"bold")).pack(anchor="w")
        self.step_buttons=[]
        for i,st in enumerate(STEPS):
            b=ttk.Button(left,text=f"{st.n}. {st.title}",command=lambda x=i:self._show(x)); b.pack(fill=X,pady=2); self.step_buttons.append(b)
        ttk.Separator(left).pack(fill=X,pady=10)
        ttk.Label(left,text="Szybka pomoc",font=("Segoe UI",11,"bold")).pack(anchor="w")
        ttk.Button(left,text="Powtórz bieżący krok",command=self._run_current).pack(fill=X,pady=3)
        ttk.Button(left,text="Pełna diagnoza",command=lambda:self._background(self._diagnose)).pack(fill=X,pady=3)
        self.counter=ttk.Label(right); self.counter.pack(anchor="w"); self.title_lbl=ttk.Label(right,style="Step.TLabel"); self.title_lbl.pack(anchor="w",pady=(3,8)); self.short=ttk.Label(right,wraplength=720); self.short.pack(anchor="w")
        box=ttk.LabelFrame(right,text="Co to znaczy?",padding=12); box.pack(fill=X,pady=10); self.explain=ttk.Label(box,wraplength=700,justify="left"); self.explain.pack(anchor="w")
        pb=ttk.LabelFrame(right,text="Folder projektu",padding=8); pb.pack(fill=X); ttk.Label(pb,textvariable=self.repo_dir,wraplength=700).pack(anchor="w")
        self.status=ttk.Label(right,text="Gotowe.",font=("Segoe UI",11,"bold")); self.status.pack(anchor="w",pady=10)
        ctr=ttk.Frame(right); ctr.pack(fill=X); self.action=ttk.Button(ctr,style="Big.TButton",command=self._run_current); self.action.pack(side=LEFT); ttk.Checkbutton(ctr,text="Po sukcesie przejdź dalej",variable=self.auto_continue).pack(side=LEFT,padx=12)
        nav=ttk.Frame(right); nav.pack(fill=X,pady=8); self.prev=ttk.Button(nav,text="← Poprzedni",command=lambda:self._show(self.current-1)); self.prev.pack(side=LEFT); self.next=ttk.Button(nav,text="Następny →",command=lambda:self._show(self.current+1)); self.next.pack(side=RIGHT)
        logbox=ttk.LabelFrame(right,text="Szczegóły techniczne",padding=6); logbox.pack(fill=BOTH,expand=True); self.log=ScrolledText(logbox,height=12,font=("Consolas",9),state="disabled"); self.log.pack(fill=BOTH,expand=True)
    def _show(self,i):
        if self.running:return
        self.current=max(0,min(i,len(STEPS)-1)); st=STEPS[self.current]; self.progress["value"]=self.current+1; self.counter.config(text=f"Krok {st.n} z {len(STEPS)}"); self.title_lbl.config(text=st.title); self.short.config(text=st.short); self.explain.config(text=st.explanation); self.action.config(text=st.button); self.prev.config(state="normal" if self.current else "disabled"); self.next.config(state="normal" if self.current<len(STEPS)-1 else "disabled"); self.status.config(text="Gotowe do wykonania kroku.")
    def _append(self,t): self.log.config(state="normal"); self.log.insert(END,t.rstrip()+"\n"); self.log.see(END); self.log.config(state="disabled")
    def _drain(self):
        try:
            while True:self._append(self.q.get_nowait())
        except queue.Empty:pass
        self.after(100,self._drain)
    def _repo(self): return Path(self.repo_dir.get()).expanduser().resolve()
    def _py(self): return self._repo()/".venv"/"Scripts"/"python.exe"
    def _cmd(self,cmd,cwd=None,retries=0,timeout=None):
        for attempt in range(retries+1):
            self.q.put("> "+subprocess.list2cmdline([str(x) for x in cmd]))
            try:
                p=subprocess.Popen([str(x) for x in cmd],cwd=str(cwd) if cwd else None,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
                assert p.stdout
                for line in p.stdout:self.q.put(line.rstrip())
                rc=p.wait(timeout=timeout)
            except (OSError,subprocess.TimeoutExpired) as e:
                self.q.put(f"BŁĄD: {e}"); rc=999
                try:p.kill()
                except Exception:pass
            if rc==0:return 0
            if attempt<retries:self.q.put(f"Próba {attempt+1} nie powiodła się. Ponawiam za 4 sekundy..."); time.sleep(4)
        return rc
    def _background(self,fn):
        if self.running:return
        self.running=True; self.status.config(text="Pracuję... nie zamykaj programu."); self.action.config(state="disabled"); threading.Thread(target=self._worker,args=(fn,),daemon=True).start()
    def _worker(self,fn):
        try:ok,msg=fn()
        except Exception as e:ok,msg=False,f"Nieoczekiwany błąd: {e}"; self.q.put(repr(e))
        self.after(0,lambda:self._finish(ok,msg))
    def _finish(self,ok,msg):
        self.running=False; self.action.config(state="normal"); self.status.config(text=("✓ " if ok else "✗ ")+msg)
        if not ok:messagebox.showerror("Problem",msg+"\n\nKliknij „Napraw bezpiecznie” albo przeczytaj log na dole.")
        elif self.auto_continue.get() and self.current<len(STEPS)-1:self.after(600,lambda:self._show(self.current+1))
    def _run_current(self):
        if self.running:return
        st=STEPS[self.current]
        if st.action=="choose_folder":return self._action_choose_folder()
        if st.action=="start_training" and not messagebox.askyesno("Uruchomić trening?","Trening może trwać wiele godzin. Przed startem program wykona jeszcze kontrolę bezpieczeństwa. Kontynuować?"):return
        self._background(getattr(self,"_action_"+st.action))
    def _ask_repair(self):
        if messagebox.askyesno("Bezpieczna naprawa","Program spróbuje naprawić Git LFS, .venv i biblioteki. Nie usunie nagrań, checkpointów ani wyników treningu. Kontynuować?"):self._background(self._repair)
    def _doctor(self,repair=False):
        repo=self._repo(); script=repo/"tools"/"windows_doctor.py"
        if not script.is_file():return False,"Najpierw pobierz lub zaktualizuj repozytorium."
        cmd=[sys.executable,str(script),"--json"]+(["--repair"] if repair else []); rc=self._cmd(cmd,cwd=repo,timeout=3700)
        if rc not in (0,2):return False,"Nie udało się uruchomić diagnostyki."
        # Uruchom ponownie bez JSON, aby czytelny raport trafił do logu.
        rc2=self._cmd([sys.executable,str(script)]+(["--repair"] if repair else []),cwd=repo,timeout=3700)
        return rc2==0,("System jest gotowy." if rc2==0 else "Pozostały problemy wymagające uwagi. Zobacz log.")
    def _diagnose(self):return self._doctor(False)
    def _repair(self):return self._doctor(True)
    def _open_folder(self):
        p=self._repo() if self._repo().exists() else Path(self.parent_dir.get()); os.startfile(p) if p.exists() else None
    def _action_choose_folder(self):
        s=filedialog.askdirectory(initialdir=self.parent_dir.get(),title="Wybierz folder nadrzędny")
        if not s:return True,"Nie zmieniono folderu."
        p=Path(s); self.parent_dir.set(str(p)); self.repo_dir.set(str(p if p.name.lower()==REPO_NAME else p/REPO_NAME)); self.status.config(text="✓ Folder wybrany."); return True,"Folder wybrany."
    def _action_clone_or_update(self):
        repo=self._repo(); git=shutil.which("git")
        if not git:return False,"Brak Git. Uruchom program ponownie przez START_PIPER_MAT_GUI.bat."
        if (repo/".git").is_dir():
            self._cmd([git,"config","--local","core.longpaths","true"],cwd=repo)
            if self._cmd([git,"status","--porcelain"],cwd=repo)!=0:return False,"Repozytorium Git jest uszkodzone lub niedostępne."
            rc=self._cmd([git,"fetch","--prune","origin"],cwd=repo,retries=2,timeout=300)
            if rc!=0:return False,"Nie udało się połączyć z GitHub. Sprawdź Internet/VPN i spróbuj ponownie."
            # pull --ff-only nie nadpisuje lokalnych zmian ani historii
            rc=self._cmd([git,"pull","--ff-only"],cwd=repo,retries=1,timeout=300)
            return rc==0,("Repozytorium jest aktualne." if rc==0 else "Nie można bezpiecznie scalić aktualizacji. Lokalne pliki nie zostały nadpisane.")
        if repo.exists() and any(repo.iterdir()):return False,f"Folder {repo} nie jest pusty i nie jest repozytorium. Wybierz inne miejsce."
        repo.parent.mkdir(parents=True,exist_ok=True); rc=self._cmd([git,"clone",REPO_URL,str(repo)],cwd=repo.parent,retries=2,timeout=900); return rc==0,("Projekt pobrany." if rc==0 else "Nie udało się pobrać projektu po kilku próbach.")
    def _require_repo(self):return ((repo:=self._repo())/".git").is_dir(),("" if (repo/".git").is_dir() else "Najpierw pobierz repozytorium.")
    def _action_git_lfs_pull(self):
        ok,msg=self._require_repo();
        if not ok:return ok,msg
        git=shutil.which("git"); repo=self._repo()
        if not git:return False,"Brak Git."
        if self._cmd([git,"lfs","version"],cwd=repo)!=0:return False,"Brakuje Git LFS. Zamknij GUI i uruchom START_PIPER_MAT_GUI.bat ponownie, aby zaproponować instalację."
        self._cmd([git,"lfs","install","--local"],cwd=repo); rc=self._cmd([git,"lfs","pull"],cwd=repo,retries=3,timeout=3600); return rc==0,("Duże pliki pobrane." if rc==0 else "Git LFS nadal nie może pobrać plików. Sprawdź Internet i wolne miejsce.")
    def _action_create_venv(self):
        ok,msg=self._require_repo();
        if not ok:return ok,msg
        py=self._py(); repo=self._repo()
        if py.is_file() and self._cmd([str(py),"-c","import sys,pip; print(sys.version)"],cwd=repo)==0:return True,"Istniejące .venv działa poprawnie."
        v=repo/".venv"
        if v.exists():
            backup=repo/f".venv_broken_{datetime.now():%Y%m%d_%H%M%S}"; v.rename(backup); self.q.put(f"Uszkodzone środowisko zachowano jako {backup.name}")
        rc=self._cmd([sys.executable,"-m","venv",".venv"],cwd=repo,timeout=240); return rc==0 and self._py().is_file(),("Środowisko .venv jest gotowe." if rc==0 else "Nie udało się utworzyć .venv.")
    def _action_install_dependencies(self):
        ok,msg=self._require_repo();
        if not ok:return ok,msg
        py=self._py(); repo=self._repo()
        if not py.is_file():return False,"Najpierw przygotuj .venv."
        for cmd in ([str(py),"-m","pip","install","--upgrade","pip","setuptools","wheel"],[str(py),"-m","pip","install","-e",".[train]"]):
            if self._cmd(list(cmd),cwd=repo,retries=2,timeout=3600)!=0:return False,"Instalacja bibliotek nie powiodła się po kilku próbach."
        return True,"Biblioteki są zainstalowane."
    def _action_build_extension(self):
        ok,msg=self._require_repo();
        if not ok:return ok,msg
        py=self._py(); repo=self._repo(); src=repo/"src/piper/train/vits/monotonic_align"; target=src/"monotonic_align"; target.mkdir(exist_ok=True)
        if not py.is_file():return False,"Brak .venv."
        if self._cmd([str(py),"-m","Cython.Build.Cythonize","-i","core.pyx"],cwd=src,timeout=600)!=0:return False,"Nie udało się zbudować modułu. Zainstaluj Visual Studio 2022 Build Tools z „Desktop development with C++”, uruchom ponownie Windows i ponów krok."
        built=list(src.glob("core*.pyd"))
        for f in built:shutil.move(str(f),str(target/f.name))
        rc=self._cmd([str(py),"-c","from piper.train.vits.monotonic_align import core; print('OK')"],cwd=repo); return rc==0,("monotonic_align działa." if rc==0 else "Moduł powstał, ale Python nie może go zaimportować.")
    def _action_validate_dataset(self):
        ok,msg=self._require_repo();
        if not ok:return ok,msg
        py=self._py(); rc=self._cmd([str(py),"scripts/validate_dataset.py","--metadata","dataset/metadata.csv","--audio-dir","dataset/wavs"],cwd=self._repo(),timeout=3600) if py.is_file() else 999; return rc==0,("Nagrania są poprawne." if rc==0 else "Walidator wykrył problem. Zobacz log.")
    def _action_check_ready(self):return self._diagnose()
    def _action_training_status(self):
        py=self._py(); rc=self._cmd([str(py),"scripts/train_sessions.py","--status"],cwd=self._repo()) if py.is_file() else 999; return rc==0,("Plan pokazano w logu." if rc==0 else "Nie udało się odczytać planu.")
    def _action_start_training(self):
        ok,msg=self._diagnose()
        if not ok:return False,"Diagnostyka wykryła problem. Trening nie został uruchomiony."
        py=self._py(); rc=self._cmd([str(py),"scripts/train_sessions.py"],cwd=self._repo()); return rc==0,("Sesja zakończona i zapisana." if rc==0 else "Sesja zakończyła się błędem. Poprzedni checkpoint pozostaje bezpieczny.")
    def _latest_report(self):
        d=self._repo()/"output/training_reports"; m=list(d.glob("session_*/REPORT.md")) if d.is_dir() else []; return max(m,key=lambda p:p.stat().st_mtime_ns) if m else None
    def _action_open_report(self):
        p=self._latest_report();
        if not p:return False,"Nie ma jeszcze raportu."
        os.startfile(p); return True,"Otwarto ostatni raport."

def main():
    if os.name!="nt":print("Ten kreator jest przeznaczony dla Windows 11."); return 2
    Wizard().mainloop(); return 0
if __name__=="__main__":raise SystemExit(main())
