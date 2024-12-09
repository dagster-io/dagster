from dagster_fivetran import (
    FivetranWorkspace,
    build_fivetran_assets_definitions,
    fivetran_assets,
)

import dagster as dg

fivetran_workspace = FivetranWorkspace(
    account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
    api_key=dg.EnvVar("FIVETRAN_API_KEY"),
    api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
)


# Creating assets definition for a given connector using the `@fivetran_assets` decorator
@fivetran_assets(
    connector_id="fivetran_connector_id",
    name="fivetran_connector_id",
    group_name="fivetran_connector_id",
    workspace=fivetran_workspace,
)
def fivetran_connector_assets(
    context: dg.AssetExecutionContext, fivetran: FivetranWorkspace
):
    yield from fivetran.sync_and_poll(context=context)


# Alternatively, creating all assets definitions for the Fivetran workspace
# using the `build_fivetran_assets_definitions` factory
all_fivetran_assets = build_fivetran_assets_definitions(fivetran_workspace)

defs = dg.Definitions(
    assets=all_fivetran_assets,
    resources={"fivetran": fivetran_workspace},
)
