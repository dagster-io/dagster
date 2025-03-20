import dagster as dg
from dagster_dbt.cloud_v2.resources import load_dbt_cloud_asset_specs

from dagster_dbt_cloud_kitchen_sink.resources import get_dbt_cloud_workspace

dbt_cloud_specs = load_dbt_cloud_asset_specs(workspace=get_dbt_cloud_workspace())

defs = dg.Definitions(assets=dbt_cloud_specs)
