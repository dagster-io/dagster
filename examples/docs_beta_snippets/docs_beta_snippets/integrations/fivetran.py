import os

from dagster_fivetran import FivetranResource, load_assets_from_fivetran_instance

import dagster as dg

fivetran_assets = load_assets_from_fivetran_instance(
    # Connect to your Fivetran instance
    FivetranResource(
        api_key="some_key",
        api_secret=dg.EnvVar("FIVETRAN_SECRET"),
    )
)


defs = dg.Definitions(
    assets=[fivetran_assets],
)
