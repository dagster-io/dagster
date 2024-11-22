import os
import shutil
from typing import Any, Dict, List

import yaml
from dagster import AssetsDefinition
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._utils import file_relative_path

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from dagster import AssetKey, asset
from dagster._core.pipes.subprocess import PipesSubprocessClient


def load_yaml(relative_path) -> dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), relative_path)
    with open(path, encoding="utf8") as ff:
        return yaml.load(ff, Loader=Loader)


def from_asset_entries(asset_entries: dict[str, Any]) -> list[AssetsDefinition]:
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
        def _assets_def(
            context: AssetExecutionContext,
            pipes_subprocess_client: PipesSubprocessClient,
        ):
            # instead of querying a dummy client, do your real data processing here

            python_executable = shutil.which("python")
            assert python_executable is not None
            pipes_subprocess_client.run(
                command=[python_executable, file_relative_path(__file__, "sql_script.py"), sql],
                context=context,
            ).get_results()

        assets_defs.append(_assets_def)

    return assets_defs


def get_asset_dsl_example_defs() -> list[AssetsDefinition]:
    asset_entries = load_yaml("assets.yaml")
    return from_asset_entries(asset_entries)
