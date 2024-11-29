from pathlib import Path
from typing import AbstractSet

from dagster import AssetsDefinition, Definitions
from dagster_airlift.core import (
    AirflowBasicAuthBackend,
    AirflowInstance,
    assets_with_task_mappings,
    build_defs_from_airflow_instance,
)
from dagster_sdf import SdfCliResource, SdfWorkspace, sdf_assets

WORKSPACE_DIR = Path(__file__).parent.parent.parent / "sdf-project"

SDF_WORKSPACE = SdfWorkspace(
    workspace_dir=WORKSPACE_DIR,
)


def build_sdf_asset_from_targets(targets: AbstractSet[str]) -> AssetsDefinition:
    @sdf_assets(workspace=SDF_WORKSPACE, targets=targets, name="_".join(targets).replace(".", "_"))
    def sdf_asset(context, sdf: SdfCliResource):
        return sdf.cli(["run", *targets], raise_on_error=False).wait()

    return sdf_asset


customer_models = assets_with_task_mappings(
    dag_id="operate_on_customers_data",
    task_mappings={
        "run_customers_models": [
            build_sdf_asset_from_targets({"jaffle_shop.staging.stg_customers"})
        ],
    },
)
order_models = assets_with_task_mappings(
    dag_id="operate_on_orders_data",
    task_mappings={
        "run_orders_models": [build_sdf_asset_from_targets({"jaffle_shop.staging.stg_orders"})],
    },
)

airflow_instance = AirflowInstance(
    auth_backend=AirflowBasicAuthBackend(
        webserver_url="http://localhost:8080", username="admin", password="admin"
    ),
    name="airflow_instance",
)

defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=Definitions(
        assets=[*customer_models, *order_models],
        resources={"sdf": SdfCliResource(workspace_dir=SDF_WORKSPACE)},
    ),
)
