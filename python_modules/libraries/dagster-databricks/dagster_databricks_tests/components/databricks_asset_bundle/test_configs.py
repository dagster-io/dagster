from unittest.mock import MagicMock, patch

import pytest
from dagster_databricks.components.databricks_asset_bundle.configs import (
    DatabricksConfig,
    load_databricks_bundle_config,
)

from dagster_databricks_tests.components.databricks_asset_bundle.conftest import (
    DATABRICKS_CONFIG_LOCATION_PATH,
)


def test_load_databrick_config():
    databricks_config = DatabricksConfig(databricks_config_path=DATABRICKS_CONFIG_LOCATION_PATH)
    assert databricks_config.databricks_config_path == DATABRICKS_CONFIG_LOCATION_PATH
    assert len(databricks_config.tasks) == 6

    tasks_iter = iter(databricks_config.tasks)
    notebook_task = next(tasks_iter)
    assert notebook_task.task_type == "notebook"
    assert notebook_task.task_key == "data_processing_notebook"
    assert "notebook_task" in notebook_task.task_config
    assert len(notebook_task.task_parameters) == 14
    assert len(notebook_task.depends_on) == 0
    assert notebook_task.job_name == "databricks_pipeline_job"
    assert len(notebook_task.libraries) == 2

    python_wheel_task = next(tasks_iter)
    assert python_wheel_task.task_type == "python_wheel"
    assert python_wheel_task.task_key == "stage_documents"
    assert "python_wheel_task" in python_wheel_task.task_config
    assert len(python_wheel_task.task_parameters) == 14
    assert len(python_wheel_task.depends_on) == 1
    assert python_wheel_task.job_name == "databricks_pipeline_job"
    assert len(python_wheel_task.libraries) == 2

    spark_jar_task = next(tasks_iter)
    assert spark_jar_task.task_type == "spark_jar"
    assert spark_jar_task.task_key == "spark_processing_jar"
    assert "spark_jar_task" in spark_jar_task.task_config
    assert len(spark_jar_task.task_parameters) == 14
    assert len(spark_jar_task.depends_on) == 1
    assert spark_jar_task.job_name == "databricks_pipeline_job"
    assert len(spark_jar_task.libraries) == 2

    job_task = next(tasks_iter)
    assert job_task.task_type == "run_job"
    assert job_task.task_key == "existing_job_with_references"
    assert "run_job_task" in job_task.task_config
    assert len(job_task.task_parameters) == 14
    assert len(job_task.depends_on) == 1
    assert job_task.job_name == "databricks_pipeline_job"
    assert len(job_task.libraries) == 0

    condition_task = next(tasks_iter)
    assert condition_task.task_type == "condition"
    assert condition_task.task_key == "check_data_quality"
    assert "condition_task" in condition_task.task_config
    assert len(condition_task.task_parameters) == 0
    assert len(condition_task.depends_on) == 1
    assert condition_task.job_name == "databricks_pipeline_job"
    assert len(condition_task.libraries) == 0

    spark_python_task = next(tasks_iter)
    assert spark_python_task.task_type == "spark_python"
    assert spark_python_task.task_key == "hello_world_spark_task"
    assert "spark_python_task" in spark_python_task.task_config
    assert len(spark_python_task.task_parameters) == 2
    assert len(spark_python_task.depends_on) == 0
    assert spark_python_task.job_name == "databricks_pipeline_job"
    assert len(spark_python_task.libraries) == 1


def test_databricks_cli_template_resolution(mock_databricks_cli):
    """Test that template variables are resolved via Databricks CLI."""
    databricks_config = DatabricksConfig(databricks_config_path=DATABRICKS_CONFIG_LOCATION_PATH)

    # Verify that subprocess.run was called with correct arguments
    mock_databricks_cli.assert_called_once()
    call_args = mock_databricks_cli.call_args
    assert call_args[0][0] == ["databricks", "bundle", "validate", "--output", "json"]
    assert call_args[1]["cwd"] == DATABRICKS_CONFIG_LOCATION_PATH.parent

    # Verify notebook task has resolved path
    notebook_task = next(t for t in databricks_config.tasks if t.task_type == "notebook")
    notebook_path = notebook_task.task_config["notebook_task"]["notebook_path"]

    # The mock should have resolved {{workspace_user}} to test_user@example.com
    assert "{{" not in notebook_path, f"Template variable not resolved: {notebook_path}"
    assert "test_user@example.com" in notebook_path or "/Users/" in notebook_path


def test_databricks_cli_not_found():
    """Test error handling when Databricks CLI is not found."""
    with patch("subprocess.run", side_effect=FileNotFoundError()):
        with pytest.raises(RuntimeError, match="Databricks CLI not found"):
            load_databricks_bundle_config(DATABRICKS_CONFIG_LOCATION_PATH.parent)


def test_databricks_cli_validation_failure():
    """Test error handling when Databricks CLI validation fails."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Error: Unable to authenticate"
    mock_result.stdout = ""

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="Failed to validate Databricks bundle"):
            load_databricks_bundle_config(DATABRICKS_CONFIG_LOCATION_PATH.parent)


def test_databricks_cli_timeout():
    """Test error handling when Databricks CLI times out."""
    import subprocess

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
        with pytest.raises(RuntimeError, match="timed out"):
            load_databricks_bundle_config(DATABRICKS_CONFIG_LOCATION_PATH.parent)


def test_databricks_cli_invalid_json():
    """Test error handling when Databricks CLI returns invalid JSON."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "not valid json"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="Failed to parse.*JSON"):
            load_databricks_bundle_config(DATABRICKS_CONFIG_LOCATION_PATH.parent)
