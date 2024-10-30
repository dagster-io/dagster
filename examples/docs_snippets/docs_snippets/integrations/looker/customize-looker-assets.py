from dagster_looker import (
    DagsterLookerApiTranslator,
    LookerResource,
    LookerStructureData,
    LookerStructureType,
    load_looker_asset_specs,
)

import dagster as dg

looker_resource = LookerResource(
    client_id=dg.EnvVar("LOOKERSDK_CLIENT_ID"),
    client_secret=dg.EnvVar("LOOKERSDK_CLIENT_SECRET"),
    base_url=dg.EnvVar("LOOKERSDK_HOST_URL"),
)


class CustomDagsterLookerApiTranslator(DagsterLookerApiTranslator):
    def get_asset_spec(self, looker_structure: LookerStructureData) -> dg.AssetSpec:
        asset_spec = super().get_asset_spec(looker_structure)

        # Add a team owner tag for all Looker assets
        asset_spec = asset_spec._replace(owners=["team:my_team"])

        # For only Looker dashboard, prefix the asset key with "looker" for organizational purposes
        if looker_structure.structure_type == LookerStructureType.DASHBOARD:
            asset_spec = asset_spec._replace(key=asset_spec.key.with_prefix("looker"))

        return asset_spec


looker_specs = load_looker_asset_specs(
    looker_resource, dagster_looker_translator=CustomDagsterLookerApiTranslator
)
defs = dg.Definitions(assets=[*looker_specs], resources={"looker": looker_resource})
