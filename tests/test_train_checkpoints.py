"""Testy punktów kontrolnych tworzonych podczas trenowania."""

from pathlib import Path

import pytest

L = pytest.importorskip("lightning")
torch = pytest.importorskip("torch")
from torch.utils.data import DataLoader, TensorDataset  # noqa: E402

from piper.train.__main__ import OptionalMetricCheckpoint  # noqa: E402


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
    mel_checkpoint = L.pytorch.callbacks.ModelCheckpoint(
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
