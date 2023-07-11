from typing import AbstractSet, Any, Mapping, Optional

from dagster import (
    AssetKey,
    AssetSelection,
    _check as check,
)
from dagster._annotations import experimental
from dagster._core.definitions.asset_graph import AssetGraph

from .asset_utils import is_non_asset_node
from .dagster_dbt_translator import DagsterDbtTranslator
from .utils import (
    ASSET_RESOURCE_TYPES,
    get_node_info_by_dbt_unique_id_from_manifest,
    select_unique_ids_from_manifest,
)


@experimental
class DbtManifestAssetSelection(AssetSelection):
    """Defines a selection of assets from a dbt manifest wrapper and a dbt selection string.

    Args:
        manifest (DbtManifest): The dbt manifest wrapper.
        select (str): A dbt selection string to specify a set of dbt resources.
        exclude (Optional[str]): A dbt selection string to exclude a set of dbt resources.

    Examples:
        .. code-block:: python

            from dagster_dbt import DbtManifest, DbtManifestAssetSelection

            manifest = DbtManifest.read("path/to/manifest.json")

            # Build the selection from the manifest: select the dbt assets that have the tag "foo".
            my_selection = manifest.build_asset_selection(dbt_select="tag:foo")

            # Or, manually build the same selection.
            my_selection = DbtManifestAssetSelection(manifest=manifest, select="tag:foo")
    """

    def __init__(
        self,
        manifest: Mapping[str, Any],
        select: str = "fqn:*",
        *,
        dagster_dbt_translator: Optional[DagsterDbtTranslator] = None,
        exclude: Optional[str] = None,
    ) -> None:
        self.manifest = check.dict_param(manifest, "manifest", key_type=str)
        self.select = check.str_param(select, "select")
        self.exclude = check.opt_str_param(exclude, "exclude", default="")
        self.dagster_dbt_translator = check.opt_inst_param(
            dagster_dbt_translator,
            "dagster_dbt_translator",
            DagsterDbtTranslator,
            DagsterDbtTranslator(),
        )

    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        dbt_nodes = get_node_info_by_dbt_unique_id_from_manifest(self.manifest)

        keys = set()
        for unique_id in select_unique_ids_from_manifest(
            select=self.select,
            exclude=self.exclude,
            manifest_json=self.manifest,
        ):
            node_info = dbt_nodes[unique_id]
            is_dbt_asset = node_info["resource_type"] in ASSET_RESOURCE_TYPES
            if is_dbt_asset and not is_non_asset_node(node_info):
                asset_key = self.dagster_dbt_translator.node_info_to_asset_key(node_info)
                keys.add(asset_key)

        return keys
