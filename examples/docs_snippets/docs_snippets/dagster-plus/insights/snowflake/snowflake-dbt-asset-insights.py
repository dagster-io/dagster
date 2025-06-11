# highlight-start
from dagster_cloud.dagster_insights import create_snowflake_insights_asset_and_schedule

# highlight-end
from dagster_dbt import DbtCliResource, dbt_assets
from path import Path

import dagster as dg

# highlight-start
insights_definitions = create_snowflake_insights_asset_and_schedule(
    start_date="2024-01-01-00:00"
)
# highlight-end


@dbt_assets(manifest=Path(__file__).parent / "manifest.json")
def my_asset(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    # highlight-start
    yield from dbt.cli(["build"], context=context).stream().with_insights()
    # highlight-end
