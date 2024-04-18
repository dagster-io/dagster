import os
import shutil
from typing import Any, Dict, Iterable, List, Sequence

import yaml
from dagster import (
    _check as check,
)
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.pipes.client import PipesClient
from dagster._core.pipes.context import PipesExecutionResult
from dagster._utils import file_relative_path

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from dagster import AssetKey
from examples.experimental.assets_yaml_dsl.assets_yaml_dsl.asset_graph_execution_node import (
    AssetGraphExecutionNode,
)


class PureAssetDSLNode(AssetGraphExecutionNode):
    def __init__(self, *, asset_spec, sql) -> None:
        self.sql = sql
        super().__init__([asset_spec])

    # TODO: generalize to all execution results
    def execute(self, context: AssetExecutionContext) -> Iterable[PipesExecutionResult]:
        pipes_subprocess_client = check.inst(context.resources.pipes_subprocess_client, PipesClient)
        python_executable = shutil.which("python")
        assert python_executable is not None
        return pipes_subprocess_client.run(
            command=[python_executable, file_relative_path(__file__, "sql_script.py"), self.sql],
            context=context,
        ).get_results()


def from_asset_entries(asset_entries: Dict[str, Any]) -> List[PureAssetDSLNode]:
    group_name = asset_entries.get("group_name")

    return [
        PureAssetDSLNode(
            asset_spec=AssetSpec(
                key=AssetKey.from_user_string(asset_entry["asset_key"]),
                description=asset_entry.get("description"),
                group_name=group_name,
                deps=[
                    AssetKey.from_user_string(dep_entry)
                    for dep_entry in asset_entry.get("deps", [])
                ],
            ),
            sql=asset_entry["sql"],
        )
        for asset_entry in asset_entries["assets"]
    ]


def load_yaml(relative_path) -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), relative_path)
    with open(path, "r", encoding="utf8") as ff:
        return yaml.load(ff, Loader=Loader)


def get_asset_dsl_example_defs() -> Sequence[PureAssetDSLNode]:
    asset_entries = load_yaml("assets.yaml")
    return from_asset_entries(asset_entries)
