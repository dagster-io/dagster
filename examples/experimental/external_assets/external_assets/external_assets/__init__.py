import os
from typing import List

import yaml
from dagster import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.external_asset import (
    external_assets_from_specs,
)


def load_yaml(path):
    full_path = os.path.join(os.path.dirname(__file__), path)
    with open(full_path, "r") as f:
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


def get_lake_external_assets():
    return external_assets_from_specs(asset_specs_from_de_dsl("lake.yaml"))


# defs = Definitions(assets=external_assets_from_specs(asset_specs_from_de_dsl("lake.yaml")))
