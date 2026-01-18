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


# start_upstream_asset
class MyCustomFivetranTranslator(DagsterFivetranTranslator):
    def get_asset_spec(self, props: FivetranConnectorTableProps) -> dg.AssetSpec:
        # We create the default asset spec using super()
        default_spec = super().get_asset_spec(props)
        # We set an upstream dependency for our assets
        return default_spec.replace_attributes(deps=["my_upstream_asset_key"])


fivetran_specs = load_fivetran_asset_specs(
    fivetran_workspace, dagster_fivetran_translator=MyCustomFivetranTranslator()
)

# end_upstream_asset

defs = dg.Definitions(assets=fivetran_specs, resources={"fivetran": fivetran_workspace})
