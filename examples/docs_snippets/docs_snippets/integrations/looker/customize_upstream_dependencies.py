from dagster_looker import (
    DagsterLookerApiTranslator,
    LookerApiTranslatorStructureData,
    LookerResource,
    LookerStructureType,
    load_looker_asset_specs,
)

import dagster as dg

looker_resource = LookerResource(
    client_id=dg.EnvVar("LOOKERSDK_CLIENT_ID"),
    client_secret=dg.EnvVar("LOOKERSDK_CLIENT_SECRET"),
    base_url=dg.EnvVar("LOOKERSDK_HOST_URL"),
)


# start_upstream_asset
class CustomDagsterLookerApiTranslator(DagsterLookerApiTranslator):
    def get_asset_spec(
        self, looker_structure: LookerApiTranslatorStructureData
    ) -> dg.AssetSpec:
        # We create the default asset spec using super()
        default_spec = super().get_asset_spec(looker_structure)
        # We customize upstream dependencies for the Looker view named `my_looker_view`
        return default_spec.replace_attributes(
            deps=["my_upstream_asset"]
            if looker_structure.structure_type == LookerStructureType.VIEW
            and looker_structure.data.view_name == "my_looker_view"
            else ...
        )


looker_specs = load_looker_asset_specs(
    looker_resource, dagster_looker_translator=CustomDagsterLookerApiTranslator()
)
# end_upstream_asset

defs = dg.Definitions(assets=[*looker_specs], resources={"looker": looker_resource})
