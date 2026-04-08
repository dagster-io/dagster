"""Tests for SparkPipelinesResource run_and_observe (log streaming; asset yields MaterializeResults)."""

from unittest.mock import MagicMock, patch

import pytest
from dagster import AssetKey
from dagster_spark.components.spark_declarative_pipeline.discovery import (
    SparkPipelinesExecutionError,
)
from dagster_spark.components.spark_declarative_pipeline.resource import SparkPipelinesResource

pytestmark = pytest.mark.filterwarnings("ignore::dagster.PreviewWarning")


def test_run_and_observe_completes_successfully_with_asset_keys() -> None:
    """run_and_observe runs the subprocess and returns None; the asset yields MaterializeResults."""
    mock_context = MagicMock()
    asset_keys = [
        AssetKey(["dataset_a"]),
        AssetKey(["dataset_b"]),
    ]
    with patch(
        "dagster_spark.components.spark_declarative_pipeline.resource.subprocess.Popen"
    ) as mock_popen:
        proc = MagicMock()
        proc.stdout = iter(["line1\n", "line2\n"])
        proc.wait.return_value = 0
        proc.returncode = 0
        mock_popen.return_value = proc

        resource = SparkPipelinesResource()
        resource.run_and_observe(
            context=mock_context,
            pipeline_spec_path="/path/to/spec.yaml",
            execution_mode="incremental",
            asset_keys=asset_keys,
        )

    mock_popen.assert_called_once()


def test_run_and_observe_streams_logs_via_context() -> None:
    """run_and_observe streams stdout line-by-line and logs each line with context.log.info."""
    mock_context = MagicMock()
    with patch(
        "dagster_spark.components.spark_declarative_pipeline.resource.subprocess.Popen"
    ) as mock_popen:
        proc = MagicMock()
        proc.stdout = iter(["log line 1\n", "log line 2\n"])
        proc.wait.return_value = 0
        proc.returncode = 0
        mock_popen.return_value = proc

        resource = SparkPipelinesResource()
        resource.run_and_observe(
            context=mock_context,
            pipeline_spec_path="/path/spec.yaml",
            asset_keys=[AssetKey(["a"])],
        )

    assert mock_context.log.info.call_count >= 2
    calls = [str(c) for c in mock_context.log.info.call_args_list]
    assert any("log line 1" in c for c in calls)
    assert any("log line 2" in c for c in calls)


def test_run_and_observe_raises_with_captured_log_on_nonzero_exit() -> None:
    """run_and_observe raises SparkPipelinesExecutionError with captured log when process exits non-zero."""
    mock_context = MagicMock()
    with patch(
        "dagster_spark.components.spark_declarative_pipeline.resource.subprocess.Popen"
    ) as mock_popen:
        proc = MagicMock()
        proc.stdout = iter(["error line 1\n", "error line 2\n"])
        proc.wait.return_value = 1
        proc.returncode = 1
        mock_popen.return_value = proc

        resource = SparkPipelinesResource()
        with pytest.raises(SparkPipelinesExecutionError) as exc_info:
            resource.run_and_observe(
                context=mock_context,
                pipeline_spec_path="/path/spec.yaml",
                asset_keys=[AssetKey(["a"])],
            )
        assert exc_info.value.returncode == 1
        assert "error line" in (exc_info.value.stderr or "")


def test_run_and_observe_completes_when_asset_keys_none() -> None:
    """When asset_keys is None (full graph), run_and_observe runs and logs; asset yields results."""
    mock_context = MagicMock()
    with patch(
        "dagster_spark.components.spark_declarative_pipeline.resource.subprocess.Popen"
    ) as mock_popen:
        proc = MagicMock()
        proc.stdout = iter(["log line\n"])
        proc.wait.return_value = 0
        proc.returncode = 0
        mock_popen.return_value = proc

        resource = SparkPipelinesResource()
        resource.run_and_observe(
            context=mock_context,
            pipeline_spec_path="/path/spec.yaml",
            asset_keys=None,
        )

    mock_context.log.info.assert_any_call(
        "spark-pipelines run completed successfully (full graph; asset will yield results)."
    )
    call_cmd = mock_popen.call_args[0][0]
    assert "--refresh" not in call_cmd


def test_run_and_observe_passes_dot_notation_datasets_to_cli() -> None:
    """run_and_observe passes dataset names as dot-separated (catalog.db.table) to the CLI, not slash."""
    mock_context = MagicMock()
    asset_keys = [
        AssetKey(["my_catalog", "my_db", "orders"]),
    ]
    with patch(
        "dagster_spark.components.spark_declarative_pipeline.resource.subprocess.Popen"
    ) as mock_popen:
        proc = MagicMock()
        proc.stdout = iter([])
        proc.wait.return_value = 0
        proc.returncode = 0
        mock_popen.return_value = proc

        resource = SparkPipelinesResource()
        resource.run_and_observe(
            context=mock_context,
            pipeline_spec_path="/path/spec.yaml",
            asset_keys=asset_keys,
        )

    call_cmd = mock_popen.call_args[0][0]
    assert call_cmd[1] == "run"
    assert "--spec" in call_cmd
    datasets_arg = call_cmd[-1]
    assert datasets_arg == "my_catalog.my_db.orders"
    assert "/" not in datasets_arg


def test_run_and_observe_uses_configurable_cmd_and_run_extra_args() -> None:
    """run_and_observe uses spark_pipelines_cmd and appends run_extra_args to the command."""
    mock_context = MagicMock()
    with patch(
        "dagster_spark.components.spark_declarative_pipeline.resource.subprocess.Popen"
    ) as mock_popen:
        proc = MagicMock()
        proc.stdout = iter([])
        proc.wait.return_value = 0
        proc.returncode = 0
        mock_popen.return_value = proc

        resource = SparkPipelinesResource(
            spark_pipelines_cmd="/usr/local/bin/spark-pipelines",
            run_extra_args=["--option", "value"],
        )
        resource.run_and_observe(
            context=mock_context,
            pipeline_spec_path="/path/spec.yaml",
            asset_keys=[AssetKey(["a"])],
        )

    call_cmd = mock_popen.call_args[0][0]
    assert call_cmd[0] == "/usr/local/bin/spark-pipelines"
    assert call_cmd[1] == "run"
    assert "--spec" in call_cmd
    assert "--option" in call_cmd
    assert "value" in call_cmd


def test_run_and_observe_full_refresh_no_asset_keys_uses_full_refresh_all() -> None:
    """When execution_mode is full_refresh and asset_keys is empty, CLI gets --full-refresh-all."""
    mock_context = MagicMock()
    with patch(
        "dagster_spark.components.spark_declarative_pipeline.resource.subprocess.Popen"
    ) as mock_popen:
        proc = MagicMock()
        proc.stdout = iter([])
        proc.wait.return_value = 0
        proc.returncode = 0
        mock_popen.return_value = proc

        resource = SparkPipelinesResource()
        resource.run_and_observe(
            context=mock_context,
            pipeline_spec_path="/path/spec.yaml",
            execution_mode="full_refresh",
            asset_keys=None,
        )

    call_cmd = mock_popen.call_args[0][0]
    assert "--spec" in call_cmd
    assert "--full-refresh-all" in call_cmd
    assert "--full-refresh" not in call_cmd


def test_run_and_observe_raises_on_nonzero_exit() -> None:
    """run_and_observe raises SparkPipelinesExecutionError when process returncode is not 0."""
    mock_context = MagicMock()
    with patch(
        "dagster_spark.components.spark_declarative_pipeline.resource.subprocess.Popen"
    ) as mock_popen:
        proc = MagicMock()
        proc.stdout = iter([])
        proc.wait.return_value = 1
        proc.returncode = 1
        mock_popen.return_value = proc

        resource = SparkPipelinesResource()
        with pytest.raises(SparkPipelinesExecutionError):
            resource.run_and_observe(
                context=mock_context,
                pipeline_spec_path="/path/spec.yaml",
                asset_keys=[AssetKey(["a"])],
            )
