from dagster import AssetsDefinition, multi_asset

from .constants import DBT_UPSTREAMS
from .dbt_cloud_utils import (
    EXPECTED_TAG,
    add_deps,
    filter_specs_by_tag,
    get_project,
    relevant_check_specs,
)
from .utils import eager


def get_dbt_cloud_assets() -> AssetsDefinition:
    # dags that are upstream of models.
    dbt_cloud_project = get_project()
    filtered_specs = filter_specs_by_tag(dbt_cloud_project.get_asset_specs(), EXPECTED_TAG)
    specs_with_dbt_core_deps = add_deps(DBT_UPSTREAMS, filtered_specs)
    # Dbt cloud assets will run every time the upstream dags run.
    specs_with_eager_automation = eager(specs_with_dbt_core_deps)

    @multi_asset(
        specs=specs_with_eager_automation,
        check_specs=relevant_check_specs(
            specs_with_eager_automation, dbt_cloud_project.get_check_specs()
        ),
        group_name="dbt_cloud",
    )
    def _dbt_cloud_assets():
        client = dbt_cloud_project.get_client()
        run = client.cli(["build", "--select", f"tag:{EXPECTED_TAG}"])
        run.wait_for_success()
        yield from run.get_asset_events()

    return _dbt_cloud_assets
