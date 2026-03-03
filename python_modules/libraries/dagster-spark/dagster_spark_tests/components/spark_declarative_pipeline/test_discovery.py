"""Tests for Spark Declarative Pipeline discovery (dry-run parsing and discover_datasets_fn)."""

import json
from unittest.mock import MagicMock, patch

import pytest
from dagster_spark.components.spark_declarative_pipeline.discovery import (
    DiscoveredDataset,
    SparkPipelinesDryRunError,
    discover_datasets_fn,
    discover_datasets_via_dry_run,
    extract_report,
    parse_dry_run_output_to_datasets,
)


def test_parse_dry_run_output_to_datasets_parses_json_report() -> None:
    """discover_datasets_fn / parse correctly parses a mock JSON report into DiscoveredDataset records."""
    mock_report = {
        "datasets": [
            {"name": "dataset_a", "type": "table"},
            {"name": "dataset_b", "id": "ds_b"},
        ],
    }
    stdout = json.dumps(mock_report)
    datasets = parse_dry_run_output_to_datasets(stdout)
    assert len(datasets) == 2
    assert datasets[0].name == "dataset_a"
    assert datasets[0].attributes.get("type") == "table"
    assert datasets[1].name == "dataset_b"


def test_extract_report_returns_dry_run_report() -> None:
    """extract_report returns a DryRunReport from valid JSON stdout."""
    stdout = json.dumps({"datasets": [{"name": "foo"}]})
    report = extract_report(stdout)
    assert report is not None
    assert len(report.datasets) == 1
    assert report.datasets[0].name == "foo"


def test_discover_datasets_fn_dry_run_only_raises_on_failure() -> None:
    """SparkPipelinesDryRunError is raised when dry-run fails in dry_run_only mode."""
    with patch(
        "dagster_spark.components.spark_declarative_pipeline.discovery.subprocess.run"
    ) as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="error", stdout="")
        with pytest.raises(SparkPipelinesDryRunError) as exc_info:
            discover_datasets_fn(
                pipeline_spec_path="/path/to/spec.yaml",
                discovery_mode="dry_run_only",
            )
        assert exc_info.value.returncode == 1
        assert "error" in (exc_info.value.stderr or "")


def test_discover_datasets_fn_dry_run_with_fallback_uses_source_on_failure() -> None:
    """In dry_run_with_fallback mode, source_only_datasets are returned when dry-run fails."""
    fallback = [DiscoveredDataset(name="fallback_ds", attributes={})]
    with patch(
        "dagster_spark.components.spark_declarative_pipeline.discovery.subprocess.run"
    ) as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="err", stdout="")
        result = discover_datasets_fn(
            pipeline_spec_path="/path/to/spec.yaml",
            discovery_mode="dry_run_with_fallback",
            source_only_datasets=fallback,
        )
    assert result == fallback


def test_discover_datasets_fn_source_only_returns_source_list() -> None:
    """In source_only mode, discover_datasets_fn returns source_only_datasets without running dry-run."""
    source = [
        DiscoveredDataset(name="a", attributes={}),
        DiscoveredDataset(name="b", attributes={}),
    ]
    result = discover_datasets_fn(
        pipeline_spec_path="/any/path",
        discovery_mode="source_only",
        source_only_datasets=source,
    )
    assert result == source


def test_discover_datasets_via_dry_run_raises_on_nonzero_exit() -> None:
    """discover_datasets_via_dry_run raises SparkPipelinesDryRunError when returncode != 0."""
    with patch(
        "dagster_spark.components.spark_declarative_pipeline.discovery.subprocess.run"
    ) as mock_run:
        mock_run.return_value = MagicMock(
            returncode=2,
            stderr="stderr output",
            stdout="",
        )
        with pytest.raises(SparkPipelinesDryRunError) as exc_info:
            discover_datasets_via_dry_run("/path/to/spec.yaml")
        assert exc_info.value.returncode == 2
        assert exc_info.value.stderr == "stderr output"


def test_discover_datasets_via_dry_run_returns_stdout_on_success() -> None:
    """discover_datasets_via_dry_run returns stdout when subprocess succeeds."""
    with patch(
        "dagster_spark.components.spark_declarative_pipeline.discovery.subprocess.run"
    ) as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stderr="",
            stdout='{"datasets":[{"name":"x"}]}',
        )
        out = discover_datasets_via_dry_run("/path/to/spec.yaml")
        assert "datasets" in out
        assert "x" in out
