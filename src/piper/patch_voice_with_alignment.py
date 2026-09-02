"""Expose phoneme-width alignment data from a Piper ONNX voice model.

This module requires the ``onnx`` package, not only ``onnxruntime``.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Set

import onnx

_LOGGER = logging.getLogger(__name__)


def add_alignment_output(
    model: onnx.ModelProto, tensor_name: Optional[str] = None
) -> str:
    """Mark the model's phoneme-width ``Ceil`` tensor as a graph output.

    The model is modified in place. The exposed tensor contains the values used
    to derive the number of audio samples assigned to individual phoneme IDs.

    :param model: ONNX model to modify in place.
    :param tensor_name: Explicit tensor name, or ``None`` for autodetection.
    :return: Name of the tensor marked as an output.
    :raises ValueError: If autodetection is ambiguous or the output already exists.
    """
    if tensor_name:
        ceil_tensor_name = tensor_name
    else:
        ceil_tensor_names: Set[str] = set()
        for node in model.graph.node:
            if node.op_type == "Ceil":
                ceil_tensor_names.update(node.output)

        if not ceil_tensor_names:
            raise ValueError(
                "No Ceil tensor was detected. Provide --tensor-name explicitly."
            )
        if len(ceil_tensor_names) > 1:
            candidates = ", ".join(sorted(ceil_tensor_names))
            raise ValueError(
                "Multiple Ceil tensors were detected. Provide --tensor-name "
                f"explicitly. Candidates: {candidates}"
            )

        ceil_tensor_name = next(iter(ceil_tensor_names))
        _LOGGER.debug("Detected alignment tensor: %s", ceil_tensor_name)

    if any(output.name == ceil_tensor_name for output in model.graph.output):
        raise ValueError(f"Tensor is already a graph output: {ceil_tensor_name}")

    ceil_value_info = onnx.helper.ValueInfoProto()
    ceil_value_info.name = ceil_tensor_name
    model.graph.output.append(ceil_value_info)
    return ceil_tensor_name


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Expose phoneme alignment data in a Piper ONNX voice model."
    )
    parser.add_argument("model", type=Path, help="Path to the ONNX voice model")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output model path. The input model is overwritten when omitted.",
    )
    parser.add_argument(
        "--tensor-name",
        help="Tensor to expose. By default the Ceil tensor is autodetected.",
    )
    return parser.parse_args()


def main() -> int:
    """Patch an ONNX voice model and return a process exit code."""
    args = parse_args()
    logging.basicConfig(level=logging.INFO)

    if not args.model.is_file():
        _LOGGER.error("Model does not exist: %s", args.model)
        return 2

    output_path = args.output or args.model

    try:
        model = onnx.load(str(args.model))
    except (OSError, ValueError) as exc:
        _LOGGER.error("Could not load ONNX model %s: %s", args.model, exc)
        return 2

    try:
        tensor_name = add_alignment_output(model, args.tensor_name)
    except ValueError as exc:
        _LOGGER.error("Could not expose alignment output: %s", exc)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        onnx.save(model, str(output_path))
    except OSError as exc:
        _LOGGER.error("Could not write ONNX model %s: %s", output_path, exc)
        return 2

    _LOGGER.info("Exposed alignment tensor: %s", tensor_name)
    _LOGGER.info("Wrote patched model: %s", output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
