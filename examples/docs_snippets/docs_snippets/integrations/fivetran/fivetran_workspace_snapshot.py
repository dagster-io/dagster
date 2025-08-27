from dagster_fivetran import FivetranWorkspace, load_fivetran_asset_specs

import dagster as dg

fivetran_workspace = FivetranWorkspace(
    account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
    api_key=dg.EnvVar("FIVETRAN_API_KEY"),
    api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
    snapshot_path=dg.EnvVar("FIVETRAN_SNAPSHOT_PATH"),
)

fivetran_specs = load_fivetran_asset_specs(workspace=fivetran_workspace)

defs = dg.Definitions(assets=fivetran_specs)
