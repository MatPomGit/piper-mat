"""Testy kontroli rekordu oceny kandydata do wydania."""

import json

import pytest

from scripts.check_release_readiness import check_evaluation


def _check_record(tmp_path, metrics):
    """Zapisać metryki i zwrócić błędy kontroli rekordu."""
    evaluation_path = tmp_path / "evaluation.json"
    evaluation_path.write_text(
        json.dumps({"metrics": metrics}),
        encoding="utf-8",
    )
    errors = []

    check_evaluation(evaluation_path, errors)

    return errors


@pytest.mark.parametrize("metric", ["wer", "cer"])
def test_check_evaluation_rejects_missing_required_metric(tmp_path, metric):
    """Odrzucić rekord bez wymaganej metryki."""
    metrics = {"wer": 0.1, "cer": 0.05}
    del metrics[metric]

    errors = _check_record(tmp_path, metrics)

    assert any(metric.upper() in error for error in errors)


@pytest.mark.parametrize(
    "invalid_value",
    [None, "0.1", True, -0.1, float("nan"), float("inf"), -float("inf")],
)
@pytest.mark.parametrize("metric", ["wer", "cer"])
def test_check_evaluation_rejects_invalid_error_rate(
    tmp_path,
    metric,
    invalid_value,
):
    """Odrzucić metrykę, która nie jest skończoną nieujemną liczbą."""
    metrics = {"wer": 0.1, "cer": 0.05}
    metrics[metric] = invalid_value

    errors = _check_record(tmp_path, metrics)

    assert any(metric.upper() in error for error in errors)


def test_check_evaluation_allows_error_rate_greater_than_one(tmp_path):
    """Zaakceptować współczynnik błędów większy niż jeden."""
    assert _check_record(tmp_path, {"wer": 1.5, "cer": 2}) == []


@pytest.mark.parametrize(
    ("counter", "invalid_value"),
    [
        ("utterances", 0),
        ("reference_words", -1),
        ("reference_characters", True),
        ("word_errors", -1),
        ("character_errors", 1.5),
    ],
)
def test_check_evaluation_rejects_invalid_optional_counter(
    tmp_path,
    counter,
    invalid_value,
):
    """Odrzucić niepoprawny opcjonalny licznik oceny."""
    metrics = {"wer": 0.1, "cer": 0.05, counter: invalid_value}

    errors = _check_record(tmp_path, metrics)

    assert any(counter in error for error in errors)


def test_check_evaluation_accepts_complete_valid_record(tmp_path):
    """Zaakceptować kompletny poprawny rekord oceny."""
    metrics = {
        "utterances": 3,
        "word_errors": 0,
        "reference_words": 9,
        "wer": 0,
        "character_errors": 2,
        "reference_characters": 30,
        "cer": 2 / 30,
    }

    assert _check_record(tmp_path, metrics) == []
