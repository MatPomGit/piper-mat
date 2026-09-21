"""Testy obliczania metryk dla transkrypcji."""

import json

import pytest

from scripts.evaluate_transcripts import evaluate_pairs, load_pairs


@pytest.mark.parametrize("field_name", ["reference", "hypothesis"])
@pytest.mark.parametrize("invalid_value", [None, 42, ["tekst"], {"tekst": "wartość"}])
def test_load_pairs_rejects_non_string_fields(
    tmp_path,
    field_name,
    invalid_value,
):
    """Odrzucić pole transkrypcji, które nie jest napisem."""
    row = {"reference": "Tekst wzorcowy", "hypothesis": "Rozpoznany tekst"}
    row[field_name] = invalid_value
    input_path = tmp_path / "transcripts.jsonl"
    input_path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match=rf"wiersz 1: pole {field_name}: oczekiwano typu str",
    ):
        load_pairs(input_path)


@pytest.mark.parametrize("reference", ["", "?!..."])
def test_load_pairs_rejects_reference_empty_after_normalization(
    tmp_path,
    reference,
):
    """Odrzucić referencję pustą po normalizacji."""
    input_path = tmp_path / "transcripts.jsonl"
    row = {"reference": reference, "hypothesis": "Rozpoznany tekst"}
    input_path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match=r"wiersz 1: pole reference: tekst jest pusty po normalizacji",
    ):
        load_pairs(input_path)


def test_load_pairs_allows_empty_hypothesis_as_complete_error(tmp_path):
    """Uznać pustą hipotezę za całkowicie błędne rozpoznanie."""
    input_path = tmp_path / "transcripts.jsonl"
    row = {"reference": "Ala ma kota", "hypothesis": "?!..."}
    input_path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    pairs = load_pairs(input_path)

    assert pairs == [("ala ma kota", "")]
    assert evaluate_pairs(pairs)["wer"] == 1.0
    assert evaluate_pairs(pairs)["cer"] == 1.0


def test_load_pairs_normalizes_valid_text_pair(tmp_path):
    """Wczytać i znormalizować prawidłową parę napisów."""
    input_path = tmp_path / "transcripts.jsonl"
    row = {"reference": "Zażółć GĘŚLĄ!", "hypothesis": "Zażółć gęślą."}
    input_path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    assert load_pairs(input_path) == [("zażółć gęślą", "zażółć gęślą")]
