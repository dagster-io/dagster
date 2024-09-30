from dagster_looker import (
    DagsterLookerApiTranslator,
    LookerResource,
    LookerStructureData,
    LookerStructureType,
)

from dagster import AssetSpec, EnvVar

resource = LookerResource(
    client_id=EnvVar("LOOKERSDK_CLIENT_ID"),
    client_secret=EnvVar("LOOKERSDK_CLIENT_SECRET"),
    base_url=EnvVar("LOOKERSDK_HOST_URL"),
)


class CustomDagsterLookerApiTranslator(DagsterLookerApiTranslator):
    def get_asset_spec(self, looker_structure: LookerStructureData) -> AssetSpec:
        asset_spec = super().get_asset_spec(looker_structure)

        # Add a team owner for all Looker assets
        asset_spec = asset_spec._replace(owners=["my_team"])

        # For only Looker dashboard, prefix the asset key with "looker" for organizational purposes
        if looker_structure.structure_type == LookerStructureType.DASHBOARD:
            asset_spec = asset_spec._replace(key=asset_spec.key.with_prefix("looker"))

        return asset_spec


defs = resource.build_defs(dagster_looker_translator=CustomDagsterLookerApiTranslator())
