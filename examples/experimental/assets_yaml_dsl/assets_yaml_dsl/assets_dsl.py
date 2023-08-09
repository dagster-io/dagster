import os
from typing import Any, Dict, List

import yaml
from dagster import AssetsDefinition, ResourceParam

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from dagster import AssetKey, asset


def load_yaml() -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), "assets.yaml")
    with open(path, "r", encoding="utf8") as ff:
        return yaml.load(ff, Loader=Loader)


asset_entries = load_yaml()


class SomeSqlClient:
    def __init__(self) -> None:
        self.queries = []

    def query(self, query_str: str) -> None:
        self.queries.append(query_str)


def from_asset_entries(asset_entries: Dict[str, Any]) -> List[AssetsDefinition]:
    assets_defs = []

    group_name = asset_entries.get("group_name")

    for asset_entry in asset_entries["assets"]:
        asset_key_str = asset_entry["asset_key"]
        dep_entries = asset_entry.get("deps", [])
        description = asset_entry.get("description")
        asset_key = AssetKey.from_user_string(asset_key_str)
        deps = [AssetKey.from_user_string(dep_entry) for dep_entry in dep_entries]

        sql = asset_entry["sql"]  # this is required

        @asset(key=asset_key, deps=deps, description=description, group_name=group_name)
        def _assets_def(sql_client: ResourceParam[SomeSqlClient]) -> None:
            # instead of querying a dummy client, do your real data processing here
            sql_client.query(sql)

        assets_defs.append(_assets_def)

    return assets_defs


assets_dsl_assets_defs = from_asset_entries(asset_entries)
