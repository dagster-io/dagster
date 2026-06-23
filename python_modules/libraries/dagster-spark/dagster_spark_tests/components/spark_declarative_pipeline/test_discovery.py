"""Tests for Spark Declarative Pipeline discovery (dry-run parsing and discover_datasets_fn)."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from dagster_spark.components.spark_declarative_pipeline.discovery import (
    DiscoveredDataset,
    DuplicateDatasetNamesError,
    SparkPipelinesDryRunError,
    discover_datasets_fn,
    discover_datasets_from_sources,
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
    assert datasets[0].dataset_type == "table"
    assert datasets[1].name == "dataset_b"


def test_parse_dry_run_output_to_datasets_filters_empty_inferred_deps() -> None:
    """Empty or whitespace-only dependency names are excluded from inferred_deps to avoid empty AssetKey path components."""
    mock_report = {
        "datasets": [
            {
                "name": "dataset_a",
                "type": "table",
                "deps": ["valid_dep", "", "  ", "\t", "another_valid"],
            },
        ],
    }
    stdout = json.dumps(mock_report)
    datasets = parse_dry_run_output_to_datasets(stdout)
    assert len(datasets) == 1
    assert datasets[0].inferred_deps == ["valid_dep", "another_valid"]


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


def _discovered(name: str) -> DiscoveredDataset:
    return DiscoveredDataset(
        name=name,
        dataset_type="table",
        source_file=None,
        source_line=None,
        inferred_deps=[],
        discovery_method="source_fallback",
    )


def test_discover_datasets_fn_dry_run_with_fallback_uses_source_on_failure() -> None:
    """In dry_run_with_fallback mode, source_only_datasets are returned when dry-run fails."""
    fallback = [_discovered("fallback_ds")]
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
    source = [_discovered("a"), _discovered("b")]
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


def test_discover_datasets_fn_raises_on_duplicate_dataset_names() -> None:
    """Duplicate dataset names (after normalization) raise DuplicateDatasetNamesError."""
    source = [_discovered("Foo"), _discovered("foo")]
    with pytest.raises(DuplicateDatasetNamesError) as exc_info:
        discover_datasets_fn(
            pipeline_spec_path="/any/path",
            discovery_mode="source_only",
            source_only_datasets=source,
        )
    assert "foo" in exc_info.value.duplicate_names or "Foo" in exc_info.value.duplicate_names


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


def test_discover_datasets_via_dry_run_uses_custom_cmd_and_extra_args() -> None:
    """discover_datasets_via_dry_run uses spark_pipelines_cmd and extra_args when provided."""
    with patch(
        "dagster_spark.components.spark_declarative_pipeline.discovery.subprocess.run"
    ) as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stderr="",
            stdout='{"datasets":[{"name":"x"}]}',
        )
        discover_datasets_via_dry_run(
            "/path/to/spec.yaml",
            spark_pipelines_cmd="/custom/spark-pipelines",
            extra_args=["--output", "json"],
        )
        call_cmd = mock_run.call_args[0][0]
        assert call_cmd[0] == "/custom/spark-pipelines"
        assert call_cmd[1] == "dry-run"
        assert "--spec" in call_cmd
        assert "--output" in call_cmd
        assert "json" in call_cmd


# ---- Real-world fixture tests: noisy Spark stdout with JSON or text ----

NOISY_SPARK_STDOUT_WITH_JSON = """
INFO: Building Spark session...
INFO: JVM started.
WARN: Some config key was deprecated.
{"datasets": [{"name": "catalog.schema.table_a", "type": "table"}, {"name": "catalog.schema.table_b", "type": "materialized_view"}]}
INFO: Session closed.
"""

NOISY_SPARK_STDOUT_BULLETED_TEXT = """
INFO: Building Spark session...
INFO: JVM started.
- catalog.schema.table_a
* catalog.schema.table_b
1. catalog.schema.table_c
INFO: Session closed.
- Starting JVM...
* Some other log line that is not a dataset
"""

NOISY_SPARK_STDOUT_DATASET_PREFIX = """
INFO: Log line
dataset: my_dataset
dataset: another.dataset.name
INFO: More logs
"""


def test_parse_dry_run_output_to_datasets_isolates_json_from_noisy_spark_stdout() -> None:
    """parse_dry_run_output_to_datasets correctly extracts datasets from stdout that contains Spark INFO/WARN logs and a JSON block."""
    datasets = parse_dry_run_output_to_datasets(NOISY_SPARK_STDOUT_WITH_JSON)
    names = [d.name for d in datasets]
    assert "catalog.schema.table_a" in names
    assert "catalog.schema.table_b" in names
    assert len(datasets) == 2
    assert datasets[0].dataset_type == "table"
    assert datasets[1].dataset_type == "materialized_view"


def test_parse_dry_run_output_to_datasets_isolates_bulleted_text_from_noisy_spark_stdout() -> None:
    """parse_dry_run_output_to_datasets (text fallback) extracts only valid dataset ids from bulleted lines, ignoring log-like lines."""
    datasets = parse_dry_run_output_to_datasets(NOISY_SPARK_STDOUT_BULLETED_TEXT)
    names = [d.name for d in datasets]
    assert "catalog.schema.table_a" in names
    assert "catalog.schema.table_b" in names
    assert "catalog.schema.table_c" in names
    # These should NOT be included (regex requires alphanumeric/underscore/dot only, no spaces)
    assert "Starting JVM..." not in names
    assert "Some other log line that is not a dataset" not in names
    assert len(datasets) == 3


def test_parse_dry_run_output_to_datasets_isolates_dataset_prefix_from_noisy_stdout() -> None:
    """parse_dry_run_output_to_datasets (text fallback) extracts dataset: <id> lines with valid identifiers."""
    datasets = parse_dry_run_output_to_datasets(NOISY_SPARK_STDOUT_DATASET_PREFIX)
    names = [d.name for d in datasets]
    assert "my_dataset" in names
    assert "another.dataset.name" in names
    assert len(datasets) == 2


def test_extract_report_text_accepts_hyphenated_dataset_ids() -> None:
    """Text fallback accepts dataset identifiers with hyphens (e.g. my-catalog.db.table)."""
    stdout = "- my-catalog.schema.events\n* other-dataset"
    report = extract_report(stdout)
    assert report is not None
    names = [d.name for d in report.datasets]
    assert "my-catalog.schema.events" in names
    assert "other-dataset" in names
    assert len(report.datasets) == 2


def test_extract_report_text_rejects_log_like_bullet_lines() -> None:
    """Text fallback does not treat '- Starting JVM...' or similar as dataset names."""
    stdout = "- Starting JVM...\n* Some log message with spaces\n1. Not a valid id with spaces"
    report = extract_report(stdout)
    # No line is a valid dataset id (alphanumeric, underscores, dots only); report may be None or empty.
    if report is not None:
        for d in report.datasets:
            assert all(c.isalnum() or c in "_." for c in d.name), (
                "Dataset names must be valid identifiers (no spaces)"
            )
    report2 = extract_report("- Starting JVM...\n* Foo bar")
    if report2 is not None:
        names = [d.name for d in report2.datasets]
        assert "Starting JVM..." not in names
        assert "Foo bar" not in names


# ---- Unit tests for discover_datasets_from_sources ----


def test_discover_datasets_from_sources_python_decorators() -> None:
    """discover_datasets_from_sources finds @dp.table and @dp.materialized_view def names from .py files."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "pipeline.py").write_text(
            """
import dp

@dp.table
def my_table():
    pass

@dp.materialized_view
def my_mv():
    pass
"""
        )
        result = discover_datasets_from_sources(root / "pipeline.py")
    names = [d.name for d in result]
    assert "my_table" in names
    assert "my_mv" in names
    assert len(result) == 2


def test_discover_datasets_from_sources_sql_create_table() -> None:
    """discover_datasets_from_sources finds CREATE STREAMING TABLE / CREATE TABLE names from .sql files."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "schema.sql").write_text(
            """
CREATE STREAMING TABLE IF NOT EXISTS catalog.schema.events;
CREATE TABLE catalog.schema.dim_customer;
"""
        )
        result = discover_datasets_from_sources(root / "schema.sql")
    names = [d.name for d in result]
    assert "catalog.schema.events" in names
    assert "catalog.schema.dim_customer" in names
    assert len(result) == 2


def test_discover_datasets_from_sources_mixed_py_and_sql() -> None:
    """discover_datasets_from_sources finds datasets from both .py and .sql under the pipeline spec directory."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "spec.yaml").write_text(
            ""
        )  # pipeline spec path must exist so parent is used as root
        (root / "a.py").write_text(
            """
@dp.table
def py_table():
    pass
"""
        )
        (root / "b.sql").write_text("CREATE TABLE sql_dataset;")
        result = discover_datasets_from_sources(root / "spec.yaml")
    names = [d.name for d in result]
    assert "py_table" in names
    assert "sql_dataset" in names
    assert len(result) == 2
