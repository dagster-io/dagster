from pathlib import Path
from typing import Optional

import pytest
from dagster_databricks.components.databricks_asset_bundle.configs import (
    DatabricksClusterConfig,
    DatabricksConfig,
)

from dagster_databricks_tests.components.databricks_asset_bundle.conftest import (
    CUSTOM_CONFIG_LOCATION_PATH,
    DATABRICKS_CONFIG_LOCATION_PATH,
    PARTIAL_CUSTOM_CONFIG_LOCATION_PATH,
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


@pytest.mark.parametrize(
    "custom_config_path, spark_version, node_type_id, num_workers",
    [
        (None, "13.3.x-scala2.12", "i3.xlarge", 1),
        (CUSTOM_CONFIG_LOCATION_PATH, "test_spark_version", "test_node_type_id", 2),
        (PARTIAL_CUSTOM_CONFIG_LOCATION_PATH, "test_spark_version", "i3.xlarge", 1),
    ],
    ids=[
        "no_custom_config",
        "custom_config",
        "partial_custom_config",
    ],
)
def test_load_custom_config_from_path(
    custom_config_path: Optional[Path], spark_version: str, node_type_id: str, num_workers: int
):
    custom_config = DatabricksClusterConfig(custom_config_path=custom_config_path)
    assert custom_config.spark_version == spark_version
    assert custom_config.node_type_id == node_type_id
    assert custom_config.num_workers == num_workers
