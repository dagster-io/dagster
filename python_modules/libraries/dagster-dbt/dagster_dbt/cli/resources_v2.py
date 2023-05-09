from dataclasses import dataclass
from functools import cached_property
from typing import Any, Dict, Mapping

from dagster import AssetKey

from ..asset_utils import default_asset_key_fn, output_name_fn


@dataclass
class DbtManifest:
    """Helper class for dbt manifest operations."""

    raw_manifest: Dict[str, Any]

    @cached_property
    def node_info_by_dbt_unique_id(self) -> Mapping[str, Mapping[str, Any]]:
        """A mapping of a dbt node's unique id to the node's dictionary representation in the manifest.
        """
        return {
            **self.raw_manifest["nodes"],
            **self.raw_manifest["sources"],
            **self.raw_manifest["exposures"],
            **self.raw_manifest["metrics"],
        }

    @classmethod
    def node_info_to_asset_key(cls, node_info: Mapping[str, Any]) -> AssetKey:
        return default_asset_key_fn(node_info)

    @cached_property
    def node_info_by_asset_key(self) -> Mapping[AssetKey, Mapping[str, Any]]:
        """A mapping of the default asset key for a dbt node to the node's dictionary representation in the manifest.
        """
        return {
            self.node_info_to_asset_key(node): node
            for node in self.node_info_by_dbt_unique_id.values()
        }

    @cached_property
    def node_info_by_output_name(self) -> Mapping[str, Mapping[str, Any]]:
        """A mapping of the default output name for a dbt node to the node's dictionary representation in the manifest.
        """
        return {output_name_fn(node): node for node in self.node_info_by_dbt_unique_id.values()}

    @cached_property
    def output_asset_key_replacements(self) -> Mapping[AssetKey, AssetKey]:
        """A mapping of replacement asset keys for a dbt node to the node's dictionary representation in the manifest.
        """
        return {
            DbtManifest.node_info_to_asset_key(node_info): self.node_info_to_asset_key(node_info)
            for node_info in self.node_info_by_dbt_unique_id.values()
        }

    def get_node_info_by_output_name(self, output_name: str) -> Mapping[str, Any]:
        """Get a dbt node's dictionary representation in the manifest by its Dagster output name."""
        return self.node_info_by_output_name[output_name]

    def get_node_info_by_asset_key(self, asset_key: AssetKey) -> Mapping[str, Any]:
        """Get a dbt node's dictionary representation in the manifest by its Dagster output name."""
        return self.node_info_by_asset_key[asset_key]
