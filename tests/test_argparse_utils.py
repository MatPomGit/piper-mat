"""Tests for shared ``argparse`` value parsers."""

import argparse

import pytest

from piper.argparse_utils import nonnegative_finite_float, positive_finite_float


@pytest.mark.parametrize(
    ("value", "expected"),
    [("0", 0.0), ("0.25", 0.25), ("1", 1.0)],
)
def test_nonnegative_finite_float_accepts_valid_values(
    value: str, expected: float
) -> None:
    """Accept finite floating-point values greater than or equal to zero."""
    assert nonnegative_finite_float(value) == expected


@pytest.mark.parametrize("value", ["-1", "nan", "inf", "-inf"])
def test_nonnegative_finite_float_rejects_invalid_values(value: str) -> None:
    """Reject negative and non-finite floating-point values."""
    with pytest.raises(argparse.ArgumentTypeError):
        nonnegative_finite_float(value)


def test_nonnegative_finite_float_rejects_non_number() -> None:
    """Reject text that cannot be converted to a floating-point value."""
    with pytest.raises(ValueError):
        nonnegative_finite_float("not-a-number")


@pytest.mark.parametrize("value", ["0.25", "1"])
def test_positive_finite_float_accepts_valid_values(value: str) -> None:
    """Accept finite floating-point values greater than zero."""
    assert positive_finite_float(value) == float(value)


@pytest.mark.parametrize("value", ["-1", "0", "nan", "inf", "-inf"])
def test_positive_finite_float_rejects_invalid_values(value: str) -> None:
    """Reject non-positive and non-finite floating-point values."""
    with pytest.raises(argparse.ArgumentTypeError):
        positive_finite_float(value)
