import os
from typing import List

import yaml
from dagster import AssetKey, Definitions
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.external_asset import (
    external_assets_from_specs,
)


def load_yaml(path):
    path = os.path.join(os.path.dirname(__file__), "asset_defs.yaml")
    with open(path, "r") as f:
        return yaml.load(f, Loader=yaml.SafeLoader)


def get_deps(asset):
    return [AssetKey(dep.split("/")) for dep in asset.get("dependsOn", [])]


def asset_specs_from_de_dsl(path) -> List[AssetSpec]:
    return [
        AssetSpec(
            key=AssetKey(asset["name"].split("/")),
            deps=get_deps(asset),
            group_name="external_assets",
        )
        for asset in load_yaml(path)["assets"]
    ]


defs = Definitions(assets=external_assets_from_specs(asset_specs_from_de_dsl("lake.yaml")))
