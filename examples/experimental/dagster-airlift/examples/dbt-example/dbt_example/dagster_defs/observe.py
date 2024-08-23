from pathlib import Path

from dagster import AssetSpec
from dagster_airlift.core import (
    AirflowInstance,
    BasicAuthBackend,
    build_defs_from_airflow_instance,
    combine_defs,
)
from dagster_airlift.core.dag_defs import dag_defs, task_defs
from dagster_dbt.asset_specs import build_dbt_asset_specs

from dbt_example.dagster_defs.lakehouse import lakehouse_asset_key

from .constants import (
    AIRFLOW_BASE_URL,
    AIRFLOW_INSTANCE_NAME,
    PASSWORD,
    USERNAME,
    dbt_manifest_path,
)

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    orchestrated_defs=combine_defs(
        dag_defs(
            "load_lakehouse",
            task_defs(
                "load_iris",
                AssetSpec(lakehouse_asset_key(csv_path=Path("iris.csv"))),
            ),
        ),
        dag_defs(
            "dbt_dag",
            task_defs(
                "build_dbt_models",
                *build_dbt_asset_specs(manifest=dbt_manifest_path()),
            ),
        ),
    ),
)
