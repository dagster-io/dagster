from typing import AbstractSet, Any, Mapping, Optional

from dagster import (
    AssetKey,
    AssetSelection,
    _check as check,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.base_asset_graph import BaseAssetGraph

from .asset_utils import is_non_asset_node
from .dagster_dbt_translator import DagsterDbtTranslator
from .dbt_manifest import DbtManifestParam, validate_manifest
from .utils import (
    ASSET_RESOURCE_TYPES,
    get_dbt_resource_props_by_dbt_unique_id_from_manifest,
    select_unique_ids_from_manifest,
)


class DbtManifestAssetSelection(
    AssetSelection,
    frozen=True,
    arbitrary_types_allowed=True,
):
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

    manifest: Mapping[str, Any]
    select: str
    dagster_dbt_translator: DagsterDbtTranslator
    exclude: str

    @classmethod
    def build(
        cls,
        manifest: DbtManifestParam,
        select: str = "fqn:*",
        *,
        dagster_dbt_translator: Optional[DagsterDbtTranslator] = None,
        exclude: Optional[str] = None,
    ):
        return cls(
            manifest=validate_manifest(manifest),
            select=check.str_param(select, "select"),
            dagster_dbt_translator=check.opt_inst_param(
                dagster_dbt_translator,
                "dagster_dbt_translator",
                DagsterDbtTranslator,
                DagsterDbtTranslator(),
            ),
            exclude=check.opt_str_param(exclude, "exclude", default=""),
        )

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool = False
    ) -> AbstractSet[AssetKey]:
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

    def resolve_checks_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetCheckKey]:
        if not self.dagster_dbt_translator.settings.enable_asset_checks:
            return set()

        dbt_nodes = get_dbt_resource_props_by_dbt_unique_id_from_manifest(self.manifest)

        keys = set()
        for unique_id in select_unique_ids_from_manifest(
            select=self.select,
            exclude=self.exclude,
            manifest_json=self.manifest,
        ):
            dbt_resource_props = dbt_nodes[unique_id]
            if dbt_resource_props["resource_type"] != "test":
                continue
            attached_node_unique_id = dbt_resource_props.get("attached_node")
            is_generic_test = bool(attached_node_unique_id)

            if not is_generic_test:
                continue

            asset_resource_props = dbt_nodes[attached_node_unique_id]
            asset_key = self.dagster_dbt_translator.get_asset_key(asset_resource_props)

            keys.add(AssetCheckKey(asset_key, dbt_resource_props["name"]))

        return keys
