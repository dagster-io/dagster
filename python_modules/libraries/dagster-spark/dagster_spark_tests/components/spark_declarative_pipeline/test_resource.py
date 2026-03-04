"""Tests for SparkPipelinesResource run_and_observe (log streaming and MaterializeResult yields)."""

from unittest.mock import MagicMock, patch

import pytest
from dagster import AssetKey
from dagster._core.definitions.result import MaterializeResult
from dagster_spark.components.spark_declarative_pipeline.discovery import SparkPipelinesDryRunError
from dagster_spark.components.spark_declarative_pipeline.resource import SparkPipelinesResource


def test_run_and_observe_yields_materialize_results_for_selected_datasets() -> None:
    """run_and_observe yields correct MaterializeResults for the selected asset keys on success."""
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
        results = list(
            resource.run_and_observe(
                context=mock_context,
                pipeline_spec_path="/path/to/spec.yaml",
                execution_mode="incremental",
                asset_keys=asset_keys,
            )
        )

    assert len(results) == 2
    assert all(isinstance(r, MaterializeResult) for r in results)
    assert results[0].asset_key == AssetKey(["dataset_a"])
    assert results[1].asset_key == AssetKey(["dataset_b"])


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
        list(
            resource.run_and_observe(
                context=mock_context,
                pipeline_spec_path="/path/spec.yaml",
                asset_keys=[AssetKey(["a"])],
            )
        )

    assert mock_context.log.info.call_count >= 2
    calls = [str(c) for c in mock_context.log.info.call_args_list]
    assert any("log line 1" in c for c in calls)
    assert any("log line 2" in c for c in calls)


def test_run_and_observe_raises_with_captured_log_on_nonzero_exit() -> None:
    """run_and_observe raises SparkPipelinesDryRunError with captured log when process exits non-zero."""
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
        with pytest.raises(SparkPipelinesDryRunError) as exc_info:
            list(
                resource.run_and_observe(
                    context=mock_context,
                    pipeline_spec_path="/path/spec.yaml",
                    asset_keys=[AssetKey(["a"])],
                )
            )
        assert exc_info.value.returncode == 1
        assert "error line" in (exc_info.value.stderr or "")


def test_run_and_observe_yields_nothing_when_no_asset_keys() -> None:
    """When asset_keys is empty, run_and_observe yields nothing and completes gracefully (logs only)."""
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
        results = list(
            resource.run_and_observe(
                context=mock_context,
                pipeline_spec_path="/path/spec.yaml",
                asset_keys=None,
            )
        )

    assert len(results) == 0
    mock_context.log.info.assert_any_call(
        "No specific asset keys requested; spark-pipelines run completed successfully."
    )


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
        list(
            resource.run_and_observe(
                context=mock_context,
                pipeline_spec_path="/path/spec.yaml",
                asset_keys=asset_keys,
            )
        )

    call_cmd = mock_popen.call_args[0][0]
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
        list(
            resource.run_and_observe(
                context=mock_context,
                pipeline_spec_path="/path/spec.yaml",
                asset_keys=[AssetKey(["a"])],
            )
        )

    call_cmd = mock_popen.call_args[0][0]
    assert call_cmd[0] == "/usr/local/bin/spark-pipelines"
    assert "--option" in call_cmd
    assert "value" in call_cmd


def test_run_and_observe_only_yields_on_success() -> None:
    """MaterializeResults are only yielded when process returncode is 0."""
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
        with pytest.raises(SparkPipelinesDryRunError):
            list(
                resource.run_and_observe(
                    context=mock_context,
                    pipeline_spec_path="/path/spec.yaml",
                    asset_keys=[AssetKey(["a"])],
                )
            )
