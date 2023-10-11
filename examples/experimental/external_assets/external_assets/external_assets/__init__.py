import os
from typing import List

import yaml
from dagster import AssetKey, Definitions
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.external_asset import (
    external_assets_from_specs,
)


def asset_specs_from_de_dsl() -> List[AssetSpec]:
    specs = []
    path = os.path.join(os.path.dirname(__file__), "asset_defs.yaml")
    with open(path, "r") as f:
        data = yaml.load(f, Loader=yaml.SafeLoader)

    for asset in data["assets"]:
        deps = [AssetKey(dep.split("/")) 
                for dep in asset.get("dependsOn", [])]
        specs.append(
            AssetSpec(
                deps=deps,
                key=AssetKey(asset["name"].split("/")),
                group_name="external_assets",
            )
        )
    return specs


defs = Definitions(
    assets=external_assets_from_specs(asset_specs_from_de_dsl())
)
