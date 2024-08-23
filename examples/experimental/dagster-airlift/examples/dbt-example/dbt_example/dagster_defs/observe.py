from pathlib import Path

from dagster._core.definitions.asset_spec import AssetSpec
from dagster_airlift.core import (
    AirflowInstance,
    BasicAuthBackend,
    build_defs_from_airflow_instance,
    combine_defs,
)
from dagster_airlift.core.defs_builders import from_airflow
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
        from_airflow(
            dag_id="load_lakehouse",
            task_id="load_iris",
        ).defs(
            AssetSpec(lakehouse_asset_key(csv_path=Path("iris.csv"))),
        ),
        from_airflow(
            dag_id="dbt_dag",
            task_id="build_dbt_models",
        ).defs(
            *build_dbt_asset_specs(manifest=dbt_manifest_path()),
        ),
    ),
)
