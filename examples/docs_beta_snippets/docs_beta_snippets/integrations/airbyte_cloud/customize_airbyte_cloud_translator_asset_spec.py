from dagster_airbyte import (
    AirbyteCloudWorkspace,
    AirbyteConnectionTableProps,
    DagsterAirbyteTranslator,
    load_airbyte_cloud_asset_specs,
)

import dagster as dg

airbyte_workspace = AirbyteCloudWorkspace(
    workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
    client_id=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_ID"),
    client_secret=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_SECRET"),
)


# A translator class lets us customize properties of the built
# Airbyte Cloud assets, such as the owners or asset key
class MyCustomAirbyteTranslator(DagsterAirbyteTranslator):
    def get_asset_spec(self, props: AirbyteConnectionTableProps) -> dg.AssetSpec:
        # We create the default asset spec using super()
        default_spec = super().get_asset_spec(props)
        # We customize the metadata and asset key prefix for all assets
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("prefix"),
        ).merge_attributes(metadata={"custom": "metadata"})


airbyte_cloud_specs = load_airbyte_cloud_asset_specs(
    airbyte_workspace, dagster_airbyte_translator=MyCustomAirbyteTranslator()
)

defs = dg.Definitions(assets=airbyte_cloud_specs)
