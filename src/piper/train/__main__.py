import logging

import torch
from lightning.pytorch.callbacks import ModelCheckpoint
from lightning.pytorch.cli import LightningCLI

from .vits.dataset import VitsDataModule
from .vits.lightning import VitsModel

_LOGGER = logging.getLogger(__package__)

# Checkpoint-selection signal. The raw mel L1 ("val_mel") tracks reconstruction
# fidelity and trends down as the model improves, so it is a reasonable key for
# keeping the best checkpoints. It is NOT, however, used to stop training: mel
# L1 saturates early in VITS while the adversarial (GAN) losses keep removing
# audible artifacts, so an early-stop on val_mel fires well before the audio is
# clean. Instead we train on a fixed/open-ended schedule and let the user pick a
# final checkpoint by listening (and/or by "val_mos"). Override from the
# LightningCLI config if you want different behavior.
_MONITOR = "val_mel"


class OptionalMetricCheckpoint(ModelCheckpoint):
    """Save top checkpoints only when the monitored metric is available."""

    def on_validation_end(self, trainer, pl_module) -> None:
        """Skip this validation epoch when its optional metric was not logged."""
        if self.monitor not in trainer.callback_metrics:
            return

        super().on_validation_end(trainer, pl_module)


_DEFAULT_CALLBACKS = [
    ModelCheckpoint(
        monitor=_MONITOR,
        mode="min",
        save_top_k=5,
        save_last=True,
        filename="epoch={epoch}-val_mel={val_mel:.4f}",
        auto_insert_metric_name=False,
    ),
    # Keep perceptual-quality checkpoints only for epochs in which UTMOS
    # actually produced val_mos. The optional callback deliberately skips a
    # missing metric, leaving val_mel and last.ckpt independent from UTMOS.
    # No save_last here, so this callback cannot clobber last.ckpt.
    OptionalMetricCheckpoint(
        monitor="val_mos",
        mode="max",
        save_top_k=5,
        save_last=False,
        filename="epoch={epoch}-val_mos={val_mos:.4f}",
        auto_insert_metric_name=False,
    ),
]


class VitsLightningCLI(LightningCLI):
    def add_arguments_to_parser(self, parser):
        parser.link_arguments("data.batch_size", "model.batch_size")
        parser.link_arguments("data.num_symbols", "model.num_symbols")
        parser.link_arguments("model.num_speakers", "data.num_speakers")
        parser.link_arguments("model.sample_rate", "data.sample_rate")
        parser.link_arguments("model.filter_length", "data.filter_length")
        parser.link_arguments("model.hop_length", "data.hop_length")
        parser.link_arguments("model.win_length", "data.win_length")
        parser.link_arguments("model.segment_size", "data.segment_size")


def main():
    logging.basicConfig(level=logging.INFO)
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.backends.cudnn.deterministic = False
    _cli = VitsLightningCLI(  # noqa: ignore=F841
        VitsModel,
        VitsDataModule,
        trainer_defaults={"max_epochs": -1, "callbacks": _DEFAULT_CALLBACKS},
    )


# -----------------------------------------------------------------------------


if __name__ == "__main__":
    main()
