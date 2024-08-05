import os
from pathlib import Path

from dagster import Definitions
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster_airlift import (
    AirflowInstance,
    BasicAuthBackend,
    PythonDefs,
    create_defs_from_airflow_instance,
    load_migration_state_from_yaml,
)
from dagster_airlift.dbt import DbtProjectDefs

from .constants import (
    AIRFLOW_BASE_URL,
    AIRFLOW_INSTANCE_NAME,
    MIGRATION_STATE_PATH,
    PASSWORD,
    USERNAME,
)

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


def dbt_project_path() -> Path:
    env_val = os.getenv("DBT_PROJECT_DIR")
    assert env_val
    return Path(env_val)


defs = create_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    orchestrated_defs=Definitions.merge(
        PythonDefs(
            name="load_lakehouse__load_iris",
            specs=[AssetSpec(key=AssetKey.from_user_string("iris_dataset/iris_lakehouse_table"))],
            python_fn=lambda: None,
        ).build_defs(),
        DbtProjectDefs(
            name="dbt_dag__build_dbt_models",
            dbt_project_path=dbt_project_path(),
            group="dbt",
        ).build_defs(),
    ),
    migration_state_override=load_migration_state_from_yaml(
        migration_yaml_path=MIGRATION_STATE_PATH
    ),
)
