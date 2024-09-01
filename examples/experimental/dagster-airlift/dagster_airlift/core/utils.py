from typing import Optional

from dagster import (
    AssetsDefinition,
    _check as check,
)
from dagster._core.definitions.utils import VALID_NAME_REGEX

MIGRATED_TAG = "airlift/task_migrated"
DAG_ID_TAG = "airlift/dag_id"
TASK_ID_TAG = "airlift/task_id"


def convert_to_valid_dagster_name(name: str) -> str:
    """Converts a name to a valid dagster name by replacing invalid characters with underscores. / is converted to a double underscore."""
    return "".join(c if VALID_NAME_REGEX.match(c) else "__" if c == "/" else "_" for c in name)


def get_task_id_from_asset(assets_def: AssetsDefinition) -> Optional[str]:
    return _get_prop_from_asset(assets_def, TASK_ID_TAG)


def get_dag_id_from_asset(assets_def: AssetsDefinition) -> Optional[str]:
    return _get_prop_from_asset(assets_def, DAG_ID_TAG)


def _get_prop_from_asset(assets_def: AssetsDefinition, prop_tag: str) -> Optional[str]:
    return prop_from_tags(assets_def, prop_tag)


def prop_from_tags(assets_def: AssetsDefinition, prop_tag: str) -> Optional[str]:
    specs = assets_def.specs
    if not any(prop_tag in spec.tags for spec in specs):
        return None

    prop = None
    for spec in specs:
        if prop is None:
            prop = spec.tags[prop_tag]
        else:
            if spec.tags.get(prop_tag) is None:
                asset_name = (
                    assets_def.node_def.name
                    if assets_def.is_executable
                    else assets_def.key.to_user_string()
                )
                check.failed(f"Missing {prop_tag} tag in spec {spec.key} for asset {asset_name}.")
            check.invariant(
                prop == spec.tags[prop_tag],
                f"Task ID mismatch within same AssetsDefinition: {prop} != {spec.tags[prop_tag]}",
            )
    return prop
