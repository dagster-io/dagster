from dagster_fivetran import (
    DagsterFivetranTranslator,
    FivetranConnectorTableProps,
    FivetranWorkspace,
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
        # We customize the metadata and asset key prefix for all assets
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("prefix"),
        ).merge_attributes(metadata={"custom": "metadata"})


fivetran_specs = load_fivetran_asset_specs(
    fivetran_workspace, dagster_fivetran_translator=MyCustomFivetranTranslator()
)

defs = dg.Definitions(assets=fivetran_specs, resources={"fivetran": fivetran_workspace})
