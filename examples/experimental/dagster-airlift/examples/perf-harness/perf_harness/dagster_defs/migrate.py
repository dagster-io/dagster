from typing import List

from dagster import AssetsDefinition, Definitions
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster_airlift.core import (
    AirflowInstance,
    BasicAuthBackend,
    build_defs_from_airflow_instance,
    dag_defs,
    task_defs,
)

from perf_harness.shared.constants import get_num_assets, get_num_dags, get_num_tasks

from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


def build_asset(specs: List[AssetSpec]) -> AssetsDefinition:
    @multi_asset(specs=specs)
    def asset_fn(_):
        pass

    return asset_fn


def build_asset_for_task(task_name: str, prev_asset_specs: List[AssetSpec]) -> AssetsDefinition:
    specs = [
        # Create a bunch of dependencies for each asset.
        AssetSpec(f"{task_name}_asset_{i}", deps=[spec.key for spec in prev_asset_specs])
        for i in range(get_num_assets())
    ]
    return build_asset(specs)


def get_dag_defs() -> Definitions:
    all_dag_defs = []
    prev_asset_specs: List[AssetSpec] = []
    for i in range(get_num_dags()):
        task_defs_list = []
        for j in range(get_num_tasks()):
            task_name = f"task_{i}_{j}"
            asset = build_asset_for_task(task_name, prev_asset_specs)
            task_defs_list.append(task_defs(task_name, Definitions(assets=[asset])))
            prev_asset_specs = asset.specs  # type: ignore
        all_dag_defs.append(dag_defs(f"dag_{i}", *task_defs_list))
    return Definitions.merge(*all_dag_defs)


defs = build_defs_from_airflow_instance(airflow_instance=airflow_instance, defs=get_dag_defs())
