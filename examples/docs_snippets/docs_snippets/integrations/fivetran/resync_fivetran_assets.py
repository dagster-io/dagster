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
    group_name="fivetran_connector_name",
    workspace=fivetran_workspace,
)
def fivetran_connector_assets(
    context: dg.AssetExecutionContext, fivetran: FivetranWorkspace
):
    # Perform a historical resync of specific tables
    yield from fivetran.resync_and_poll(
        context=context,
        resync_parameters={
            "schema_name": ["table1", "table2"],
            "another_schema": ["table3"],
        },
    )


# start_resync_all
@fivetran_assets(
    connector_id="fivetran_connector_id",
    name="fivetran_connector_name_full_resync",
    group_name="fivetran_connector_name",
    workspace=fivetran_workspace,
)
def fivetran_connector_full_resync_assets(
    context: dg.AssetExecutionContext, fivetran: FivetranWorkspace
):
    # Perform a full historical resync of all tables in the connector
    yield from fivetran.resync_and_poll(context=context)


# end_resync_all


defs = dg.Definitions(
    assets=[fivetran_connector_assets, fivetran_connector_full_resync_assets],
    resources={"fivetran": fivetran_workspace},
)
