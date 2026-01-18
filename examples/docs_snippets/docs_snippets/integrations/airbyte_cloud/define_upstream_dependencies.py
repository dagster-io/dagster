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


# start_upstream_asset
class MyCustomAirbyteTranslator(DagsterAirbyteTranslator):
    def get_asset_spec(self, props: AirbyteConnectionTableProps) -> dg.AssetSpec:
        # We create the default asset spec using super()
        default_spec = super().get_asset_spec(props)
        # We set an upstream dependency for our assets
        return default_spec.replace_attributes(deps=["my_upstream_asset_key"])


airbyte_cloud_specs = load_airbyte_cloud_asset_specs(
    airbyte_workspace, dagster_airbyte_translator=MyCustomAirbyteTranslator()
)
# end_upstream_asset

defs = dg.Definitions(assets=airbyte_cloud_specs)
