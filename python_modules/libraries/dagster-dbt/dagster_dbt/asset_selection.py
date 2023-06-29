from typing import AbstractSet, Optional

import dagster._check as check
from dagster import AssetKey, AssetSelection
from dagster._annotations import experimental
from dagster._core.definitions.asset_graph import AssetGraph

from dagster_dbt.asset_utils import (
    is_non_asset_node,
)
from dagster_dbt.utils import ASSET_RESOURCE_TYPES, select_unique_ids_from_manifest

from .cli.resources_v2 import DbtManifest


@experimental
class DbtManifestAssetSelection(AssetSelection):
    """Defines a selection of assets from a dbt manifest wrapper and a dbt selection string.

    Args:
        manifest (DbtManifest): The dbt manifest wrapper.
        select (str): A dbt selection string to specify a set of dbt resources.
        exclude (Optional[str]): A dbt selection string to exclude a set of dbt resources.

    Example:
        .. code-block:: python

            manifest = DbtManifest.read("path/to/manifest.json")

            # Build the selection from the manifest.
            # Select all dbt assets that have the tag "foo" and are in the path "marts/finance".
            my_selection = manifest.build_asset_selection(
                dbt_select="tag:foo,path:marts/finance",
            )

            # Or, manually build the same selection.
            my_selection = DbtManifestAssetSelection(
                manifest=manifest,
                select="tag:foo,path:marts/finance",
            )
    """

    def __init__(
        self,
        manifest: DbtManifest,
        select: str = "fqn:*",
        exclude: Optional[str] = None,
    ) -> None:
        self.manifest = check.inst_param(manifest, "manifest", DbtManifest)
        self.select = check.str_param(select, "select")
        self.exclude = check.opt_str_param(exclude, "exclude", default="")

    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        dbt_nodes = self.manifest.node_info_by_dbt_unique_id

        keys = set()
        for unique_id in select_unique_ids_from_manifest(
            select=self.select,
            exclude=self.exclude,
            manifest_json=self.manifest.raw_manifest,
        ):
            node_info = dbt_nodes[unique_id]
            is_dbt_asset = node_info["resource_type"] in ASSET_RESOURCE_TYPES
            if is_dbt_asset and not is_non_asset_node(node_info):
                asset_key = self.manifest.node_info_to_asset_key(node_info)
                keys.add(asset_key)

        return keys
