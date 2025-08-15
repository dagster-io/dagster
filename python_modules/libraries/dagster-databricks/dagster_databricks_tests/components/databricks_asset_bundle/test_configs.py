from pathlib import Path

from dagster_databricks.components.databricks_asset_bundle.databricks_configs import (
    DatabricksConfigs,
)

DATABRICKS_CONFIGS_LOCATION_PATH = Path(__file__).parent / "configs" / "databricks.yml"


def test_load_databricks_configs():
    databricks_configs = DatabricksConfigs(databricks_configs_path=DATABRICKS_CONFIGS_LOCATION_PATH)
    assert databricks_configs.databricks_configs_path == DATABRICKS_CONFIGS_LOCATION_PATH
    assert len(databricks_configs.tasks) == 3

    tasks_iter = iter(databricks_configs.tasks)
    notebook_task = next(tasks_iter)
    assert notebook_task.task_type == "notebook"
    assert notebook_task.task_key == "data_processing_notebook"
    assert "notebook_task" in notebook_task.task_config
    assert len(notebook_task.task_parameters) == 14
    assert len(notebook_task.depends_on) == 0
    assert notebook_task.job_name == "databricks_pipeline_job"
    assert len(notebook_task.libraries) == 2

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
