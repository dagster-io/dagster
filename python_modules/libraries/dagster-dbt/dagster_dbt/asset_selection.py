import json
from typing import AbstractSet, Any, Callable, Mapping, Optional, Sequence

import dagster._check as check
from dagster import AssetKey, AssetSelection
from dagster._annotations import experimental
from dagster._core.definitions.asset_graph import AssetGraph

from dagster_dbt.asset_defs import (
    _get_node_asset_key,
    _is_non_asset_node,
)
from dagster_dbt.utils import select_unique_ids_from_manifest


@experimental
class DbtManifestAssetSelection(AssetSelection):
    """Defines a selection of assets from a parsed dbt manifest.json file and a dbt-syntax selection
    string.

    Args:
        manifest_json (Mapping[str, Any]): The parsed manifest.json file from your dbt project. Must
            provide either this argument or `manifest_json_path`.
        manifest_json_path: (Optional[str]): The path to a manifest.json file representing the
            current state of your dbt project. Must provide either this argument or `manifest_json`.
        select (str): A dbt-syntax selection string, e.g. tag:foo or config.materialized:table.
        exclude (str): A dbt-syntax exclude string. Defaults to "".
        resource_types (Sequence[str]): The resource types to select. Defaults to ["model"].
        node_info_to_asset_key (Callable[[Mapping[str, Any]], AssetKey]): A function that takes a
            dictionary of dbt metadata and returns the AssetKey that you want to represent a given
            model or source. If you pass in a custom function to `load_assets_from_dbt_manifest`,
            you must also pass in the same function here.
        state_path: (Optional[str]): The path to a folder containing the manifest.json file representing
            the previous state of your dbt project. Providing this path will allow you to select
            dbt assets using the `state:` selector. To learn more, see the
            [dbt docs](https://docs.getdbt.com/reference/node-selection/methods#the-state-method).

    Example:
        .. code-block:: python

            my_dbt_assets = load_assets_from_dbt_manifest(
                manifest_json,
                node_info_to_asset_key=my_node_info_to_asset_key_fn,
            )

            # This will select all assets that have the tag "foo" and are in the path "marts/finance"
            my_selection = DbtManifestAssetSelection(
                manifest_json,
                select="tag:foo,path:marts/finance",
                node_info_to_asset_key=my_node_info_to_asset_key_fn,
            )

            # This will retrieve the asset keys according to the selection
            selected_asset_keys = my_selection.resolve(my_dbt_assets)

    """

    def __init__(
        self,
        manifest_json: Optional[Mapping[str, Any]] = None,
        select: str = "*",
        exclude: str = "",
        resource_types: Optional[Sequence[str]] = None,
        node_info_to_asset_key: Callable[[Mapping[str, Any]], AssetKey] = _get_node_asset_key,
        manifest_json_path: Optional[str] = None,
        state_path: Optional[str] = None,
    ):
        self.select = check.str_param(select, "select")
        self.exclude = check.str_param(exclude, "exclude")
        self.resource_types = check.opt_list_param(
            resource_types, "resource_types", of_type=str
        ) or ["model"]
        self.node_info_to_asset_key = check.callable_param(
            node_info_to_asset_key, "node_info_to_asset_key"
        )

        self.manifest_json = check.opt_mapping_param(manifest_json, "manifest_json")
        self.manifest_json_path = check.opt_str_param(manifest_json_path, "manifest_json_path")
        if self.manifest_json:
            check.param_invariant(
                not self.manifest_json_path,
                "manifest_json_path",
                "Cannot provide both manifest_json and manifest_json_path",
            )
        elif self.manifest_json_path:
            with open(self.manifest_json_path, "r") as f:
                self.manifest_json = check.opt_mapping_param(json.load(f), "manifest_json")
        else:
            check.failed("Must provide either manifest_json or manifest_json_path.")

        self.state_path = check.opt_str_param(state_path, "state_path")
        if self.state_path:
            check.param_invariant(
                self.manifest_json_path is not None,
                "state_path",
                (
                    "Must provide a manifest_json_path instead of manifest_json to use the state"
                    " selector."
                ),
            )

    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        dbt_nodes = {
            **self.manifest_json["nodes"],
            **self.manifest_json["sources"],
            **self.manifest_json["metrics"],
            **self.manifest_json["exposures"],
        }
        keys = set()
        for unique_id in select_unique_ids_from_manifest(
            select=self.select,
            exclude=self.exclude,
            state_path=self.state_path,
            manifest_json_path=self.manifest_json_path,
            manifest_json=self.manifest_json,
        ):
            node_info = dbt_nodes[unique_id]
            if node_info["resource_type"] in self.resource_types and not _is_non_asset_node(
                node_info
            ):
                keys.add(self.node_info_to_asset_key(node_info))
        return keys
