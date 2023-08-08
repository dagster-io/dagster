import os
from typing import Any, Dict, List

import yaml
from dagster import AssetsDefinition, Definitions

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


def from_asset_entries(asset_entries: Dict[str, Any]) -> List[AssetsDefinition]:
    assets = []

    group_name = asset_entries.get("group_name")

    for asset_entry in asset_entries["assets"]:
        asset_key_str = asset_entry["asset_key"]
        dep_entries = asset_entry.get("deps", [])
        description = asset_entry.get("description")
        string_to_return = asset_entry.get("string_to_return")
        asset_key = AssetKey.from_user_string(asset_key_str)
        deps = [AssetKey.from_user_string(dep_entry) for dep_entry in dep_entries]

        @asset(key=asset_key, deps=deps, description=description, group_name=group_name)
        def _asset_fn() -> str:
            # instead of returning a string, put your logic to do data processing or launch an external process
            return string_to_return

        assets.append(_asset_fn)
    return assets


defs = Definitions(assets=from_asset_entries(asset_entries))
