from dagster_fivetran import (
    DagsterFivetranTranslator,
    FivetranConnectorTableProps,
    FivetranWorkspace,
    build_fivetran_assets_definitions,
    fivetran_assets,
    load_fivetran_asset_specs,
)

import dagster as dg

fivetran_workspace = FivetranWorkspace(
    account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
    api_key=dg.EnvVar("FIVETRAN_API_KEY"),
    api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
)


# A translator class lets us customize properties of the built
# Fivetran assets, such as the owners or asset key
class MyCustomFivetranTranslator(DagsterFivetranTranslator):
    def get_asset_spec(self, props: FivetranConnectorTableProps) -> dg.AssetSpec:
        # We create the default asset spec using super()
        default_spec = super().get_asset_spec(props)
        # We customize the metadata, asset key prefix and team owner tag for all assets
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("prefix"),
            owners=["team:my_team"],
        ).merge_attributes(metadata={"custom": "metadata"})


# When loading asset specs
fivetran_specs = load_fivetran_asset_specs(
    fivetran_workspace, dagster_fivetran_translator=MyCustomFivetranTranslator()
)


# Alternatively, when creating assets definition for a given connector using the `@fivetran_assets` decorator
@fivetran_assets(
    connector_id="fivetran_connector_id",
    name="fivetran_connector_id",
    group_name="fivetran_connector_id",
    workspace=fivetran_workspace,
    dagster_fivetran_translator=MyCustomFivetranTranslator(),
)
def fivetran_connector_assets(
    context: dg.AssetExecutionContext, fivetran: FivetranWorkspace
):
    yield from fivetran.sync_and_poll(context=context)


# Alternatively, when creating all assets definitions for the Fivetran workspace
# using the `build_fivetran_assets_definitions` factory
all_fivetran_assets = build_fivetran_assets_definitions(
    fivetran_workspace, dagster_fivetran_translator=MyCustomFivetranTranslator()
)

defs = dg.Definitions(
    assets=all_fivetran_assets, resources={"fivetran": fivetran_workspace}
)
