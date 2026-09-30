"""Shared argument parsers for Piper command-line interfaces."""

import argparse
import math


def nonnegative_finite_float(value: str) -> float:
    """Parse a finite, nonnegative floating-point command-line value."""
    parsed_value = float(value)
    if not math.isfinite(parsed_value) or parsed_value < 0:
        raise argparse.ArgumentTypeError("must be a finite, nonnegative number")

    return parsed_value


def positive_finite_float(value: str) -> float:
    """Parse a finite, positive floating-point command-line value."""
    parsed_value = float(value)
    if not math.isfinite(parsed_value) or parsed_value <= 0:
        raise argparse.ArgumentTypeError("must be a finite, positive number")

    return parsed_value
