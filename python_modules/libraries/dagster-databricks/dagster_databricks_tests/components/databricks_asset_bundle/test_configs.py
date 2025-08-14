from pathlib import Path

from dagster_databricks.components.databricks_asset_bundle.databricks_configs import (
    DatabricksConfigs,
)

DATABRICKS_CONFIGS_LOCATION_PATH = Path(__file__).parent / "configs" / "databricks.yml"


def test_load_databricks_configs():
    databricks_configs = DatabricksConfigs(databricks_configs_path=DATABRICKS_CONFIGS_LOCATION_PATH)
    assert databricks_configs.databricks_configs_path == DATABRICKS_CONFIGS_LOCATION_PATH
    assert len(databricks_configs.tasks) == 1

    notebook_task = next(iter(databricks_configs.tasks))
    assert notebook_task.task_type == "notebook"
    assert notebook_task.task_key == "data_processing_notebook"
    assert "notebook_task" in notebook_task.task_config
    assert len(notebook_task.task_parameters) == 14
    assert len(notebook_task.depends_on) == 0
    assert notebook_task.job_name == "databricks_pipeline_job"
    assert len(notebook_task.libraries) == 2
