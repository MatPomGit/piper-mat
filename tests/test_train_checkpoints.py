"""Testy punktów kontrolnych tworzonych podczas trenowania."""

from pathlib import Path

import pytest

L = pytest.importorskip("lightning")
torch = pytest.importorskip("torch")
from torch.utils.data import DataLoader, TensorDataset  # noqa: E402

from piper.train.__main__ import (  # noqa: E402
    AtomicModelCheckpoint,
    OptionalMetricCheckpoint,
)


class ValidationModel(L.LightningModule):
    """Minimalny model emitujący `val_mel`, ale nie `val_mos`."""

    def __init__(self) -> None:
        """Utwórz pojedynczy trenowalny parametr bez predyktora MOS."""
        super().__init__()
        self.weight = torch.nn.Parameter(torch.ones(()))
        self._mos_predictor = None

    def training_step(self, batch, batch_idx):
        """Zwróć prostą funkcję straty dla partii treningowej."""
        del batch, batch_idx
        return self.weight.square()

    def validation_step(self, batch, batch_idx):
        """Zaloguj wyłącznie metrykę niezależną od UTMOS."""
        del batch, batch_idx
        self.log("val_mel", self.weight.detach())

    def configure_optimizers(self):
        """Skonfiguruj optymalizator wymagany przez pełną pętlę `fit`."""
        return torch.optim.SGD(self.parameters(), lr=0.1)


def _data_loader() -> DataLoader:
    """Utwórz najmniejszy mechanizm wczytywania danych do testu."""
    return DataLoader(TensorDataset(torch.ones(1, 1)), batch_size=1)


def test_validation_epoch_without_mos_still_saves_last_checkpoint(
    tmp_path: Path,
) -> None:
    """Brak `val_mos` nie przerywa epoki ani zapisu ostatniego stanu."""
    mel_checkpoint = AtomicModelCheckpoint(
        dirpath=tmp_path,
        monitor="val_mel",
        mode="min",
        save_top_k=1,
        save_last=True,
        filename="best_val_mel",
    )
    mos_checkpoint = OptionalMetricCheckpoint(
        dirpath=tmp_path,
        monitor="val_mos",
        mode="max",
        save_top_k=1,
        save_last=False,
        filename="best_val_mos",
    )
    trainer = L.Trainer(
        accelerator="cpu",
        callbacks=[mel_checkpoint, mos_checkpoint],
        default_root_dir=tmp_path,
        enable_model_summary=False,
        enable_progress_bar=False,
        logger=False,
        max_epochs=1,
        num_sanity_val_steps=0,
    )

    trainer.fit(
        ValidationModel(),
        train_dataloaders=_data_loader(),
        val_dataloaders=_data_loader(),
    )

    assert (tmp_path / "last.ckpt").is_file()
    assert (tmp_path / "best_val_mel.ckpt").is_file()
    assert not (tmp_path / "best_val_mos.ckpt").exists()


def test_atomic_checkpoint_preserves_previous_after_interrupted_write(
    tmp_path: Path,
) -> None:
    """Częściowy zapis nie może uszkodzić wcześniejszego checkpointu."""
    previous = tmp_path / "last.ckpt"
    torch.save({"epoch": 4}, previous)
    original_bytes = previous.read_bytes()

    class Strategy:
        """Atrapa lokalnej strategii zapisu."""

        def broadcast(self, name):
            """Zachowaj nazwę tymczasowego pliku."""
            return name

        def barrier(self, *args):
            """Nie wykonuj synchronizacji między procesami."""

    class InterruptedTrainer:
        """Symuluj przerwanie zapisu checkpointu."""

        is_global_zero = True
        strategy = Strategy()
        global_step = 9
        loggers = []

        def save_checkpoint(self, path, weights_only):
            """Zapisz fragment i przerwij operację."""
            Path(path).write_bytes(b"PARTIAL CHECKPOINT")
            raise OSError("przerwany zapis")

    callback = AtomicModelCheckpoint(save_last=True)
    with pytest.raises(OSError, match="przerwany zapis"):
        callback._save_checkpoint(InterruptedTrainer(), str(previous))

    assert previous.read_bytes() == original_bytes
    assert not list(tmp_path.glob("*.tmp"))


def test_atomic_checkpoint_can_resume_full_training_on_cpu(
    tmp_path: Path,
) -> None:
    """Odczytaj pełny stan optymalizatora i wznów trenowanie od checkpointu."""
    first = L.Trainer(
        accelerator="cpu",
        max_epochs=2,
        default_root_dir=tmp_path,
        callbacks=[AtomicModelCheckpoint(
            dirpath=tmp_path,
            monitor="val_mel",
            mode="min",
            save_top_k=1,
            save_last=True,
        )],
        enable_model_summary=False,
        enable_progress_bar=False,
        logger=False,
        num_sanity_val_steps=0,
    )
    first.fit(
        ValidationModel(),
        train_dataloaders=_data_loader(),
        val_dataloaders=_data_loader(),
    )
    saved = tmp_path / "last.ckpt"
    assert saved.is_file()
    checkpoint = torch.load(saved, map_location="cpu", weights_only=False)
    assert checkpoint["epoch"] == 1
    assert checkpoint["optimizer_states"]
    assert checkpoint["state_dict"]
    assert checkpoint["loops"]
    assert not list(tmp_path.glob("*.tmp"))

    resumed = L.Trainer(
        accelerator="cpu",
        max_epochs=3,
        default_root_dir=tmp_path / "resume",
        logger=False,
        enable_checkpointing=False,
        enable_model_summary=False,
        enable_progress_bar=False,
        num_sanity_val_steps=0,
    )
    resumed.fit(
        ValidationModel(),
        train_dataloaders=_data_loader(),
        val_dataloaders=_data_loader(),
        ckpt_path=saved,
    )
    assert resumed.current_epoch == 3
