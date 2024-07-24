from dagster import Definitions

from .assets.dbt import DBT_PROJECT_DIR, dbt_project_assets, dbt_project_assets_2, dbt_resource
from .assets.ingest_assets import ingest_customer

resources = {
    # this resource is used to execute dbt cli commands
    "dbt": dbt_resource,
}


defs = Definitions(
    assets=[
        dbt_project_assets,
        ingest_customer,
    ],  # , dbt_project_assets_2], adding this it throws an duplicate asset check key error
    resources=resources,
)
