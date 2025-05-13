from dagster import AssetKey, AssetSpec
from dagster._core.definitions.asset_dep import AssetDep

SELECTION_TAG = "tag:demo"


def spec_with_dep(uid_to_dep_mapping: dict[str, AssetKey], spec: AssetSpec) -> AssetSpec:
    uid = spec.metadata["raw_data"]["uniqueId"]
    if uid in uid_to_dep_mapping:
        spec = spec.replace_attributes(deps=[*spec.deps, AssetDep(uid_to_dep_mapping[uid])])
    return spec
