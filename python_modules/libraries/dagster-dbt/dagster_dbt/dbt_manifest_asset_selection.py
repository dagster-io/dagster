from typing import AbstractSet, Optional

from dagster import (
    AssetKey,
    AssetSelection,
    _check as check,
)
from dagster._core.definitions.asset_graph import AssetGraph

from .asset_utils import is_non_asset_node
from .dagster_dbt_translator import DagsterDbtTranslator
from .dbt_manifest import DbtManifestParam, validate_manifest
from .utils import (
    ASSET_RESOURCE_TYPES,
    get_dbt_resource_props_by_dbt_unique_id_from_manifest,
    select_unique_ids_from_manifest,
)


class DbtManifestAssetSelection(AssetSelection):
    """Defines a selection of assets from a dbt manifest wrapper and a dbt selection string.

    Args:
        manifest (Mapping[str, Any]): The dbt manifest blob.
        select (str): A dbt selection string to specify a set of dbt resources.
        exclude (Optional[str]): A dbt selection string to exclude a set of dbt resources.

    Examples:
        .. code-block:: python

            import json
            from pathlib import Path

            from dagster_dbt import DbtManifestAssetSelection

            manifest = json.loads(Path("path/to/manifest.json").read_text())

            # select the dbt assets that have the tag "foo".
            my_selection = DbtManifestAssetSelection(manifest=manifest, select="tag:foo")
    """

    def __init__(
        self,
        manifest: DbtManifestParam,
        select: str = "fqn:*",
        *,
        dagster_dbt_translator: Optional[DagsterDbtTranslator] = None,
        exclude: Optional[str] = None,
    ) -> None:
        self.manifest = validate_manifest(manifest)
        self.select = check.str_param(select, "select")
        self.exclude = check.opt_str_param(exclude, "exclude", default="")
        self.dagster_dbt_translator = check.opt_inst_param(
            dagster_dbt_translator,
            "dagster_dbt_translator",
            DagsterDbtTranslator,
            DagsterDbtTranslator(),
        )

    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        dbt_nodes = get_dbt_resource_props_by_dbt_unique_id_from_manifest(self.manifest)

        keys = set()
        for unique_id in select_unique_ids_from_manifest(
            select=self.select,
            exclude=self.exclude,
            manifest_json=self.manifest,
        ):
            dbt_resource_props = dbt_nodes[unique_id]
            is_dbt_asset = dbt_resource_props["resource_type"] in ASSET_RESOURCE_TYPES
            if is_dbt_asset and not is_non_asset_node(dbt_resource_props):
                asset_key = self.dagster_dbt_translator.get_asset_key(dbt_resource_props)
                keys.add(asset_key)

        return keys
