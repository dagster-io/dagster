from dagster_fivetran import FivetranWorkspace, fivetran_assets

import dagster as dg

fivetran_workspace = FivetranWorkspace(
    account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
    api_key=dg.EnvVar("FIVETRAN_API_KEY"),
    api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
)


@fivetran_assets(
    connector_id="fivetran_connector_id",
    workspace=fivetran_workspace,
)
def fivetran_connector_assets(
    context: dg.AssetExecutionContext, fivetran: FivetranWorkspace
):
    yield from fivetran.sync_and_poll(context=context).fetch_column_metadata()
