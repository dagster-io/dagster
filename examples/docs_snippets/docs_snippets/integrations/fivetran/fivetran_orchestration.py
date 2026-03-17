from dagster_fivetran import (
    FivetranWorkspace,
    build_fivetran_assets_definitions,
    build_fivetran_polling_sensor,
)

import dagster as dg

fivetran_workspace = FivetranWorkspace(
    account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
    api_key=dg.EnvVar("FIVETRAN_API_KEY"),
    api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
)

# Build materializable asset definitions for all connectors
all_fivetran_assets = build_fivetran_assets_definitions(workspace=fivetran_workspace)

# Automate materialization with Declarative Automation
all_fivetran_assets = [
    assets_def.map_asset_specs(
        lambda spec: spec.replace_attributes(
            automation_condition=dg.AutomationCondition.eager()
        )
    )
    for assets_def in all_fivetran_assets
]

# Declarative Automation sensor triggers syncs based on upstream dependencies
automation_sensor = dg.AutomationConditionSensorDefinition(
    name="automation_sensor",
    target="*",
    default_status=dg.DefaultSensorStatus.RUNNING,
    minimum_interval_seconds=1,
)

# Polling sensor detects externally completed syncs
fivetran_polling_sensor = build_fivetran_polling_sensor(workspace=fivetran_workspace)

defs = dg.Definitions(
    assets=all_fivetran_assets,
    sensors=[automation_sensor, fivetran_polling_sensor],
    resources={"fivetran": fivetran_workspace},
)
