from dagster import AssetsDefinition, Definitions, asset
from dagster_airlift.core import (
    AirflowInstance,
    BasicAuthBackend,
    build_defs_from_airflow_instance,
    dag_defs,
    task_defs,
)

from perf_harness.shared.constants import get_num_dags, get_num_tasks

from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


def build_asset(key: str) -> AssetsDefinition:
    @asset(key=key)
    def asset_fn(_):
        return key

    return asset_fn


defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=Definitions.merge(
        *[
            dag_defs(
                f"dag_{i}",
                *[
                    task_defs(f"task_{i}_{j}", Definitions(assets=[build_asset(f"asset_{i}_{j}")]))
                    for j in range(get_num_tasks())
                ],
            )
            for i in range(get_num_dags())
        ]
    ),
)
