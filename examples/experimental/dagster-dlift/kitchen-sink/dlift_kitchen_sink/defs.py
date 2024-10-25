from dagster import (
    AssetExecutionContext,
    Definitions,
    _check as check,
    multi_asset,
)

from dlift_kitchen_sink.constants import EXPECTED_TAG
from dlift_kitchen_sink.instance import get_project

project = get_project()


@multi_asset(
    specs=[
        spec
        for spec in project.get_asset_specs()
        if EXPECTED_TAG in spec.metadata["raw_data"]["tags"]
    ],
    check_specs=[
        spec
        for spec in project.get_check_specs()
        if EXPECTED_TAG in check.not_none(spec.metadata)["raw_data"]["tags"]
    ],
)
def dbt_models(context: AssetExecutionContext):
    client = project.get_client()
    run = client.cli(["build", "--select", f"tag:{EXPECTED_TAG}"])
    run.wait_for_success()
    yield from run.get_asset_events()


defs = Definitions(assets=[dbt_models])
