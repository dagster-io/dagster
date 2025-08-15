from pathlib import Path

from dagster_databricks.components.databricks_asset_bundle.databricks_configs import (
    DatabricksConfigs,
)

DATABRICKS_CONFIGS_LOCATION_PATH = Path(__file__).parent / "configs" / "databricks.yml"


def test_load_databricks_configs():
    databricks_configs = DatabricksConfigs(databricks_configs_path=DATABRICKS_CONFIGS_LOCATION_PATH)
    assert databricks_configs.databricks_configs_path == DATABRICKS_CONFIGS_LOCATION_PATH
    assert len(databricks_configs.tasks) == 6

    tasks_iter = iter(databricks_configs.tasks)
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
