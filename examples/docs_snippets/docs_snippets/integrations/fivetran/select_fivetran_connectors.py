from dagster_fivetran import FivetranWorkspace, build_fivetran_assets_definitions

import dagster as dg

fivetran_workspace = FivetranWorkspace(
    account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
    api_key=dg.EnvVar("FIVETRAN_API_KEY"),
    api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
)

all_fivetran_assets = build_fivetran_assets_definitions(
    workspace=fivetran_workspace,
    connector_selector_fn=(
        lambda connector: connector.id in {"some_connector_id", "another_connector_id"}
    ),
)

defs = dg.Definitions(
    assets=all_fivetran_assets,
    resources={"fivetran": fivetran_workspace},
)
