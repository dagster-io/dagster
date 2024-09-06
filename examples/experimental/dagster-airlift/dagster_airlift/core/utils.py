from typing import Optional, Union

from dagster import (
    AssetsDefinition,
    AssetSpec,
    _check as check,
)
from dagster._core.definitions.utils import VALID_NAME_REGEX
from dagster._core.storage.tags import KIND_PREFIX

from dagster_airlift.constants import DAG_ID_METADATA_KEY, TASK_ID_METADATA_KEY


def convert_to_valid_dagster_name(name: str) -> str:
    """Converts a name to a valid dagster name by replacing invalid characters with underscores. / is converted to a double underscore."""
    return "".join(c if VALID_NAME_REGEX.match(c) else "__" if c == "/" else "_" for c in name)


def get_task_id_from_asset(asset: Union[AssetsDefinition, AssetSpec]) -> Optional[str]:
    return _get_prop_from_asset(asset, TASK_ID_METADATA_KEY, 1)


def get_dag_id_from_asset(asset: Union[AssetsDefinition, AssetSpec]) -> Optional[str]:
    return _get_prop_from_asset(asset, DAG_ID_METADATA_KEY, 0)


def _get_prop_from_asset(
    asset: Union[AssetSpec, AssetsDefinition], prop_metadata_key: str, position: int
) -> Optional[str]:
    prop_from_asset_tags = prop_from_metadata(asset, prop_metadata_key)
    if isinstance(asset, AssetSpec) or not asset.is_executable:
        return prop_from_asset_tags
    prop_from_op_tags = None
    if asset.node_def.tags and prop_metadata_key in asset.node_def.tags:
        prop_from_op_tags = asset.node_def.tags[prop_metadata_key]
    prop_from_name = None
    if len(asset.node_def.name.split("__")) == 2:
        prop_from_name = asset.node_def.name.split("__")[position]
    if prop_from_asset_tags and prop_from_op_tags:
        check.invariant(
            prop_from_asset_tags == prop_from_op_tags,
            f"ID mismatch between asset tags and op tags: {prop_from_asset_tags} != {prop_from_op_tags}",
        )
    if prop_from_asset_tags and prop_from_name:
        check.invariant(
            prop_from_asset_tags == prop_from_name,
            f"ID mismatch between tags and name: {prop_from_asset_tags} != {prop_from_name}",
        )
    if prop_from_op_tags and prop_from_name:
        check.invariant(
            prop_from_op_tags == prop_from_name,
            f"ID mismatch between op tags and name: {prop_from_op_tags} != {prop_from_name}",
        )
    return prop_from_asset_tags or prop_from_op_tags or prop_from_name


def prop_from_metadata(
    asset: Union[AssetsDefinition, AssetSpec], prop_metadata_key: str
) -> Optional[str]:
    specs = asset.specs if isinstance(asset, AssetsDefinition) else [asset]
    asset_name = (
        asset.node_def.name
        if isinstance(asset, AssetsDefinition) and asset.is_executable
        else asset.key.to_user_string()
    )
    if any(prop_metadata_key in spec.metadata for spec in specs):
        prop = None
        for spec in specs:
            if prop is None:
                prop = spec.metadata[prop_metadata_key]
            else:
                if spec.metadata.get(prop_metadata_key) is None:
                    check.failed(
                        f"Missing {prop_metadata_key} tag in spec {spec.key} for {asset_name}"
                    )
                check.invariant(
                    prop == spec.metadata[prop_metadata_key],
                    f"Task ID mismatch within same AssetsDefinition: {prop} != {spec.metadata[prop_metadata_key]}",
                )
        return prop
    return None


def airflow_kind_dict() -> dict:
    return {f"{KIND_PREFIX}airflow": ""}
