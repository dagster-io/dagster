from dagster_fivetran import FivetranWorkspace, build_fivetran_assets_definitions

import dagster as dg

fivetran_workspace = FivetranWorkspace(
    account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
    api_key=dg.EnvVar("FIVETRAN_API_KEY"),
    api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
)

all_fivetran_assets = build_fivetran_assets_definitions(workspace=fivetran_workspace)

defs = dg.Definitions(
    assets=all_fivetran_assets,
    resources={"fivetran": fivetran_workspace},
)
