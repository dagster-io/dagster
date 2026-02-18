from collections.abc import Mapping
from typing import Any, Optional

from dagster_dbt import DbtProject, DbtProjectComponent

import dagster as dg


# start_custom_component_translator
class CustomDbtProjectComponent(DbtProjectComponent):
    """Custom DbtProjectComponent that customizes asset metadata.

    This is the recommended approach for migrating custom DagsterDbtTranslator logic.
    """

    def get_asset_spec(
        self, manifest: Mapping[str, Any], unique_id: str, project: DbtProject | None
    ) -> dg.AssetSpec:
        base_spec = super().get_asset_spec(manifest, unique_id, project)
        dbt_props = self.get_resource_props(manifest, unique_id)

        # Customize the asset key with a prefix
        new_key = dg.AssetKey(["my_prefix_"] + list(base_spec.key.path))

        # Customize group name and add custom metadata
        return base_spec.replace_attributes(
            key=new_key,
            group_name="my_dbt_group",
        ).merge_attributes(
            metadata={
                "dbt_model_name": dbt_props["name"],
            },
        )


# end_custom_component_translator
