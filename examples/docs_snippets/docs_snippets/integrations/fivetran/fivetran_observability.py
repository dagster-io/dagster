from dagster_fivetran import (
    FivetranWorkspace,
    build_fivetran_polling_sensor,
    load_fivetran_asset_specs,
)

import dagster as dg

fivetran_workspace = FivetranWorkspace(
    account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
    api_key=dg.EnvVar("FIVETRAN_API_KEY"),
    api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
)

# Load all connector tables as asset specs
fivetran_specs = load_fivetran_asset_specs(fivetran_workspace)

# Build a sensor that polls Fivetran for completed syncs and emits
# AssetMaterialization events into the Dagster event log
fivetran_polling_sensor = build_fivetran_polling_sensor(workspace=fivetran_workspace)

defs = dg.Definitions(
    assets=fivetran_specs,
    sensors=[fivetran_polling_sensor],
    resources={"fivetran": fivetran_workspace},
)
