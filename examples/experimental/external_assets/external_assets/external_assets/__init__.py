import os

import yaml
from dagster import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.external_asset import external_assets_from_specs


def build_asset_specs_from_external_definitions():
    specs = []
    with open(os.path.join(os.path.dirname(__file__), "asset_defs.yaml")) as f:
        data = yaml.load(f, Loader=yaml.SafeLoader)
        for asset in data["assets"]:
            deps = []
            for dep in asset.get("dependsOn", []):
                deps.append(AssetKey(dep.split("/")))
            specs.append(
                AssetSpec(
                    key=AssetKey(asset["name"].split("/")), group_name="external_assets", deps=deps
                )
            )
    return specs


external_asset_defs = external_assets_from_specs(
    specs=build_asset_specs_from_external_definitions()
)
