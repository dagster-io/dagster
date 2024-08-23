from typing import Optional

from dagster import (
    AssetsDefinition,
    _check as check,
)

MIGRATED_TAG = "airlift/task_migrated"
DAG_ID_TAG = "airlift/dag_id"
TASK_ID_TAG = "airlift/task_id"


def get_task_id_from_asset(assets_def: AssetsDefinition) -> Optional[str]:
    return _get_prop_from_asset(assets_def, TASK_ID_TAG, 1)


def get_dag_id_from_asset(assets_def: AssetsDefinition) -> Optional[str]:
    return _get_prop_from_asset(assets_def, DAG_ID_TAG, 0)


def _get_prop_from_asset(
    assets_def: AssetsDefinition, prop_tag: str, position: int
) -> Optional[str]:
    prop_from_tags = None
    if any(prop_tag in spec.tags for spec in assets_def.specs):
        prop = None
        for spec in assets_def.specs:
            if prop is None:
                prop = spec.tags[prop_tag]
            else:
                if spec.tags.get(prop_tag) is None:
                    check.failed(
                        f"Missing {prop_tag} tag in spec {spec.key} for {assets_def.node_def.name}"
                    )
                check.invariant(
                    prop == spec.tags[prop_tag],
                    f"Task ID mismatch within same AssetsDefinition: {prop} != {spec.tags[prop_tag]}",
                )
        prop_from_tags = prop
    prop_from_op_tags = None
    if assets_def.node_def.tags and prop_tag in assets_def.node_def.tags:
        prop_from_op_tags = assets_def.node_def.tags[prop_tag]
    prop_from_name = None
    if len(assets_def.node_def.name.split("__")) == 2:
        prop_from_name = assets_def.node_def.name.split("__")[position]
    if prop_from_tags and prop_from_op_tags:
        check.invariant(
            prop_from_tags == prop_from_op_tags,
            f"ID mismatch between asset tags and op tags: {prop_from_tags} != {prop_from_op_tags}",
        )
    if prop_from_tags and prop_from_name:
        check.invariant(
            prop_from_tags == prop_from_name,
            f"ID mismatch between tags and name: {prop_from_tags} != {prop_from_name}",
        )
    if prop_from_op_tags and prop_from_name:
        check.invariant(
            prop_from_op_tags == prop_from_name,
            f"ID mismatch between op tags and name: {prop_from_op_tags} != {prop_from_name}",
        )
    return prop_from_tags or prop_from_op_tags or prop_from_name
