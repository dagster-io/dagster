from typing import Any, Mapping, Optional

from dagster import AssetKey
from dagster._core.definitions.events import (
    CoercibleToAssetKeyPrefix,
    check_opt_coercible_to_asset_key_prefix_param,
)

from .asset_utils import default_asset_key_fn, default_description_fn, default_metadata_fn


class DagsterDbtTranslator:
    @classmethod
    def node_info_to_asset_key(cls, node_info: Mapping[str, Any]) -> AssetKey:
        """A function that takes a dictionary representing the dbt node and returns the
        Dagster asset key the represents the dbt node.

        This method can be overridden to provide a custom asset key for a dbt node.

        Args:
            node_info (Mapping[str, Any]): A dictionary representing the dbt node.

        Returns:
            AssetKey: The Dagster asset key for the dbt node.

        Examples:
            .. code-block:: python

                from typing import Any, Mapping

                from dagster import AssetKey
                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    @classmethod
                    def node_info_to_asset_key(cls, node_info: Mapping[str, Any]) -> AssetKey:
                        return AssetKey(["prefix", node_info["alias"]])
        """
        return default_asset_key_fn(node_info)

    @classmethod
    def node_info_to_description(cls, node_info: Mapping[str, Any]) -> str:
        """A function that takes a dictionary representing the dbt node and returns the
        Dagster description the represents the dbt node.

        This method can be overridden to provide a custom description for a dbt node.

        Args:
            node_info (Mapping[str, Any]): A dictionary representing the dbt node.

        Returns:
            str: The description for the dbt node.

        Examples:
            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    @classmethod
                    def node_info_to_description(cls, node_info: Mapping[str, Any]) -> str:
                        return "custom description"
        """
        return default_description_fn(node_info)

    @classmethod
    def node_info_to_metadata(cls, node_info: Mapping[str, Any]) -> Mapping[str, Any]:
        """A function that takes a dictionary representing the dbt node and returns the
        Dagster metadata the represents the dbt node.

        This method can be overridden to provide custom metadata for a dbt node.

        Args:
            node_info (Mapping[str, Any]): A dictionary representing the dbt node.

        Returns:
            Mapping[str, Any]: A dictionary representing the Dagster metadata for the dbt node.

        Examples:
            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    @classmethod
                    def node_info_to_metadata(cls, node_info: Mapping[str, Any]) -> Mapping[str, Any]:
                        return {"custom": "metadata"}
        """
        return default_metadata_fn(node_info)


class KeyPrefixDagsterDbtTranslator:
    """A DagsterDbtTranslator that applies prefixes to the asset keys generated from dbt resources.

    Attributes:
        asset_key_prefix (Optional[Union[str, Sequence[str]]]): A prefix to apply to all dbt models,
            seeds, snapshots, etc. This will *not* apply to dbt sources.
        source_asset_key_prefix (Optional[Union[str, Sequence[str]]]): A prefix to apply to all dbt
            sources.
    """

    def __init__(
        self,
        asset_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        source_asset_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    ):
        self._asset_key_prefix = (
            check_opt_coercible_to_asset_key_prefix_param(asset_key_prefix, "asset_key_prefix")
            or []
        )
        self._source_asset_key_prefix = (
            check_opt_coercible_to_asset_key_prefix_param(
                source_asset_key_prefix, "source_asset_key_prefix"
            )
            or []
        )

    def node_info_to_asset_key(self, node_info: Mapping[str, Any]) -> AssetKey:
        base_key = default_asset_key_fn(node_info)
        if node_info["resource_type"] == "source":
            return base_key.with_prefix(self._source_asset_key_prefix)
        else:
            return base_key.with_prefix(self._asset_key_prefix)
