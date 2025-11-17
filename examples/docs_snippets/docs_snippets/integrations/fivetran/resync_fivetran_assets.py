from dagster_fivetran import FivetranSyncConfig, FivetranWorkspace, fivetran_assets

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
    context: dg.AssetExecutionContext,
    fivetran: FivetranWorkspace,
    config: FivetranSyncConfig,
):
    """Syncs Fivetran connector with optional resync capability.

    Configure at runtime:
    - For normal sync: Pass config with resync=False (default)
    - For historical resync of specific tables: Pass config with resync=True and resync_parameters
    - For full historical resync: Pass config with resync=True and no resync_parameters
    """
    yield from fivetran.sync_and_poll(context=context, config=config)


# start_resync_all
@fivetran_assets(
    connector_id="fivetran_connector_id",
    name="fivetran_connector_name_full_resync",
    group_name="fivetran_connector_name",
    workspace=fivetran_workspace,
)
def fivetran_connector_full_resync_assets(
    context: dg.AssetExecutionContext,
    fivetran: FivetranWorkspace,
    config: FivetranSyncConfig,
):
    """Performs a full historical resync of all tables in the connector.

    Configure at runtime with resync=True.
    """
    yield from fivetran.sync_and_poll(context=context, config=config)


# end_resync_all


defs = dg.Definitions(
    assets=[fivetran_connector_assets, fivetran_connector_full_resync_assets],
    resources={"fivetran": fivetran_workspace},
)
