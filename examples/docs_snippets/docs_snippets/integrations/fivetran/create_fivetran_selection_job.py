from dagster_fivetran import FivetranWorkspace, fivetran_assets

import dagster as dg

fivetran_workspace = FivetranWorkspace(
    account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
    api_key=dg.EnvVar("FIVETRAN_API_KEY"),
    api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
)


@fivetran_assets(
    connector_id="fivetran_connector_id",  # Replace with your connector ID
    name="fivetran_connector_name",  # Replace with your connection name
    workspace=fivetran_workspace,
)
def fivetran_connector_assets(
    context: dg.AssetExecutionContext, fivetran: FivetranWorkspace
):
    yield from fivetran.sync_and_poll(context=context)


fivetran_connector_assets_job = dg.define_asset_job(
    name="fivetran_connector_assets_job",
    selection=[fivetran_connector_assets],
)


defs = dg.Definitions(
    assets=[fivetran_connector_assets],
    jobs=[fivetran_connector_assets_job],
    resources={"fivetran": fivetran_workspace},
)
