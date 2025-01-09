from collections.abc import Mapping
from typing import Optional

from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.resource_definition import ResourceDefinition


class AssetChecksDefinition(AssetsDefinition):
    """Defines a set of checks that are produced by the same op or op graph.

    AssetChecksDefinition should not be instantiated directly, but rather produced using the `@asset_check` decorator or `AssetChecksDefinition.create` method.
    """

    @staticmethod
    def create(
        *,
        keys_by_input_name: Mapping[str, AssetKey],
        node_def: OpDefinition,
        check_specs_by_output_name: Mapping[str, AssetCheckSpec],
        can_subset: bool,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    ):
        """Create an AssetChecksDefinition."""
        return AssetChecksDefinition(
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name={},
            node_def=node_def,
            partitions_def=None,
            partition_mappings=None,
            asset_deps=None,
            selected_asset_keys=None,
            can_subset=can_subset,
            resource_defs=resource_defs,
            group_names_by_key=None,
            metadata_by_key=None,
            tags_by_key=None,
            freshness_policies_by_key=None,
            backfill_policy=None,
            descriptions_by_key=None,
            check_specs_by_output_name=check_specs_by_output_name,
            selected_asset_check_keys=None,
            is_subset=False,
            owners_by_key=None,
        )


# This is still needed in a few places where we need to handle normal AssetsDefinition and
# AssetChecksDefinition differently, but eventually those areas should be refactored and this should
# be removed.
def has_only_asset_checks(assets_def: AssetsDefinition) -> bool:
    return len(assets_def.keys) == 0 and len(assets_def.check_keys) > 0
