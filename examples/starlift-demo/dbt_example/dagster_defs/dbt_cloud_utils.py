import os

from dagster import AssetKey, AssetSpec
from dagster._core.definitions.assets.definition.asset_dep import AssetDep
from dagster_dbt.asset_utils import DAGSTER_DBT_UNIQUE_ID_METADATA_KEY

SELECTION_TAG = "tag:demo"


def spec_with_dep(uid_to_dep_mapping: dict[str, AssetKey], spec: AssetSpec) -> AssetSpec:
    uid = spec.metadata[DAGSTER_DBT_UNIQUE_ID_METADATA_KEY]
    if uid in uid_to_dep_mapping:
        spec = spec.replace_attributes(deps=[*spec.deps, AssetDep(uid_to_dep_mapping[uid])])
    return spec


def get_env_var(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise Exception(f"{var_name} is not set")
    return value
