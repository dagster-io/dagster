import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest
from automation.eval.cli import Metric, evaluate_sessions, load_config, load_sessions
from dagster_shared.utils import environ


@pytest.fixture(autouse=True, scope="session")
def blank_openapi_key():
    with environ({"OPENAI_API_KEY": "..."}):
        yield


def test_metric_hash_generation():
    metric1 = Metric(name="Test Metric", criteria="How good is this?")
    metric2 = Metric(name="Test Metric", criteria="How good is this?")
    metric3 = Metric(name="Test Metric", criteria="Different criteria")

    assert metric1.get_hash() == metric2.get_hash()
    assert metric1.get_hash() != metric3.get_hash()

    metric_with_steps = Metric(
        name="Test Metric", criteria="How good is this?", evaluation_steps=["Step 1", "Step 2"]
    )
    assert metric_with_steps.get_hash() != metric1.get_hash()


def test_load_config_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        eval_dir = Path(tmpdir)
        config_file = eval_dir / "eval.yaml"

        # Write YAML content that load_config expects
        yaml_content = """
metrics:
  - name: Accuracy
    criteria: Is it accurate?
  - name: Completeness
    criteria: Is it complete?
    evaluation_steps:
      - Check all parts
"""

        with open(config_file, "w") as f:
            f.write(yaml_content)

        # Test that load_config properly parses and creates the config
        config = load_config(eval_dir)

        assert len(config.metrics) == 2
        assert config.metrics[0].name == "Accuracy"
        assert config.metrics[0].criteria == "Is it accurate?"
        assert config.metrics[1].name == "Completeness"
        assert config.metrics[1].evaluation_steps == ["Check all parts"]


def test_load_config_missing_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        eval_dir = Path(tmpdir)

        with pytest.raises(click.UsageError, match=r"Configuration file .* not found"):
            load_config(eval_dir)


def test_load_sessions_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        eval_dir = Path(tmpdir)

        session1 = {"input": "What is 2+2?", "output": "4", "timestamp": "2024-01-01T10:00:00"}
        session2 = {
            "input": "What is the capital of France?",
            "output": "Paris",
            "timestamp": "2024-01-01T11:00:00",
            "extra_field": "Extra data",
        }

        with open(eval_dir / "session1.json", "w") as f:
            json.dump(session1, f)
        with open(eval_dir / "session2.json", "w") as f:
            json.dump(session2, f)

        sessions = load_sessions(eval_dir)

        assert len(sessions) == 2
        assert sessions["session1"]["input"] == "What is 2+2?"
        assert sessions["session2"]["extra_field"] == "Extra data"


def test_load_sessions_invalid_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        eval_dir = Path(tmpdir)

        with open(eval_dir / "invalid.json", "w") as f:
            json.dump({"missing": "required fields"}, f)

        with pytest.raises(click.UsageError, match="missing required fields"):
            load_sessions(eval_dir)


def test_load_sessions_ignores_cache_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        eval_dir = Path(tmpdir)

        session = {"input": "Test", "output": "Response", "timestamp": "2024-01-01T10:00:00"}
        cache = {"session1": {"score": 0.9}}

        with open(eval_dir / "session1.json", "w") as f:
            json.dump(session, f)
        with open(eval_dir / "metric-abc123.json", "w") as f:
            json.dump(cache, f)

        sessions = load_sessions(eval_dir)

        assert len(sessions) == 1
        assert "metric-abc123" not in sessions


@patch("automation.eval.cli.evaluate")
def test_evaluate_sessions_with_cache(mock_evaluate):
    metric = Metric(name="Test", criteria="Is it good?")

    sessions = {
        "session1": {"input": "Q1", "output": "A1"},
        "session2": {"input": "Q2", "output": "A2"},
        "session3": {"input": "Q3", "output": "A3"},
    }

    cached_results = {
        "session1": {"score": 0.8, "reason": "Good", "evaluated_at": "2024-01-01T10:00:00"}
    }

    mock_result = MagicMock()
    mock_result.test_results = [
        MagicMock(metrics_data=[MagicMock(score=0.7, reason="Okay")]),
        MagicMock(metrics_data=[MagicMock(score=0.9, reason="Great")]),
    ]
    mock_evaluate.return_value = mock_result

    results = evaluate_sessions(sessions, metric, cached_results)

    assert len(results) == 3
    assert results["session1"]["score"] == 0.8
    assert results["session2"]["score"] == 0.7
    assert results["session3"]["score"] == 0.9

    mock_evaluate.assert_called_once()
    assert len(mock_evaluate.call_args[1]["test_cases"]) == 2
