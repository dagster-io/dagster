from dagster_fivetran import FivetranWorkspace, fivetran_assets

import dagster as dg

fivetran_workspace = FivetranWorkspace(
    account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
    api_key=dg.EnvVar("FIVETRAN_API_KEY"),
    api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
)


@fivetran_assets(
    connector_id="fivetran_connector_id",
    name="fivetran_connector_id",
    group_name="fivetran_connector_id",
    workspace=fivetran_workspace,
)
def fivetran_connector_assets(
    context: dg.AssetExecutionContext, fivetran: FivetranWorkspace
):
    # Do something before the materialization...
    yield from fivetran.sync_and_poll(context=context)
    # Do something after the materialization...


defs = dg.Definitions(
    assets=[fivetran_connector_assets],
    resources={"fivetran": fivetran_workspace},
)
