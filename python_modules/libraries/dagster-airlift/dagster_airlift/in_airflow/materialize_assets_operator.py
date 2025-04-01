import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Union

from dagster_airlift.in_airflow.base_asset_operator import BaseDagsterAssetsOperator, Context

UNESCAPED_SLASH_RE = re.compile(r"(?<!\\)/")
ESCAPED_SLASH = "\\/"


class BaseMaterializeAssetsOperator(BaseDagsterAssetsOperator):
    """An operator base class that proxies execution to a user-provided list of Dagster assets.
    Will throw an error at runtime if not all assets can be found on the corresponding Dagster instance.

    Args:
        asset_key_paths (Sequence[Union[str, Sequence[str]]]): A sequence of asset key paths to materialize.
            Each path in the sequence can be a string, which is treated as an asset key path with a single
            component per "/" key, or a sequence of strings representing a path with multiple components. For more,
            see the docs on asset keys: https://docs.dagster.io/guides/build/assets#multi-part-asset-keys
    """

    def __init__(self, asset_key_paths: Sequence[Union[str, Sequence[str]]], *args, **kwargs):
        self.asset_key_paths = [
            _get_path_from_str(path) if isinstance(path, str) else tuple(path)
            for path in asset_key_paths
        ]
        super().__init__(*args, **kwargs)

    def filter_asset_nodes(
        self, context: Context, asset_nodes: Sequence[Mapping[str, Any]]
    ) -> Iterable[Mapping[str, Any]]:
        hashable_path_to_node = {tuple(node["assetKey"]["path"]): node for node in asset_nodes}
        if not all(path in hashable_path_to_node for path in self.asset_key_paths):
            raise ValueError(
                f"Could not find all asset key paths {self.asset_key_paths} in the asset nodes. Found: {list(hashable_path_to_node.keys())}"
            )
        yield from [hashable_path_to_node[path] for path in self.asset_key_paths]


def _get_path_from_str(path_str: str) -> tuple:
    parts = re.split(UNESCAPED_SLASH_RE, path_str)
    return tuple(part.replace(ESCAPED_SLASH, "/") for part in parts)
