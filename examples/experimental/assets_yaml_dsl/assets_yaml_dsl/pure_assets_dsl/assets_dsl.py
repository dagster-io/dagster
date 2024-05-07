import os
import shutil
from typing import Any, Dict, List, Optional

import yaml
from dagster import AssetsDefinition
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.factory.entity_set import ExecutableEntitySet
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._utils import file_relative_path

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from dagster import AssetKey
from dagster._core.pipes.subprocess import PipesSubprocessClient


def load_yaml(relative_path) -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), relative_path)
    with open(path, "r", encoding="utf8") as ff:
        return yaml.load(ff, Loader=Loader)


class PureDSLAsset(ExecutableEntitySet):
    def __init__(self, asset_entry: dict, sql: str, group_name: Optional[str]):
        self.sql = sql
        super().__init__(
            specs=[
                AssetSpec(
                    group_name=group_name,
                    key=AssetKey.from_user_string(asset_entry["asset_key"]),
                    description=asset_entry.get("description"),
                    deps=[
                        AssetKey.from_user_string(dep_entry)
                        for dep_entry in asset_entry.get("deps", [])
                    ],
                )
            ],
            compute_kind="python",
        )

    def execute(
        self, context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient
    ):
        python_executable = shutil.which("python")
        assert python_executable is not None
        return pipes_subprocess_client.run(
            command=[python_executable, file_relative_path(__file__, "sql_script.py"), self.sql],
            context=context,
        ).get_results()


def from_asset_entries(asset_entries: dict) -> List[AssetsDefinition]:
    return [
        PureDSLAsset(
            asset_entry=asset_entry,
            sql=asset_entry["sql"],
            group_name=asset_entries.get("group_name"),
        ).to_assets_def()
        for asset_entry in asset_entries["assets"]
    ]


def get_asset_dsl_example_defs() -> List[AssetsDefinition]:
    asset_entries = load_yaml("assets.yaml")
    return from_asset_entries(asset_entries)
