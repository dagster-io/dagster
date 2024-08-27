from typing import Optional

from dagster import (
    AssetsDefinition,
    _check as check,
)

MIGRATED_TAG = "airlift/task_migrated"
DAG_ID_TAG = "airlift/dag_id"
TASK_ID_TAG = "airlift/task_id"


def get_task_id_from_asset(
    assets_def: AssetsDefinition,
) -> Optional[str]:
    return _get_prop_from_asset(assets_def, TASK_ID_TAG)


def get_dag_id_from_asset(assets_def: AssetsDefinition) -> Optional[str]:
    return _get_prop_from_asset(assets_def, DAG_ID_TAG)


def _get_prop_from_asset(assets_def: AssetsDefinition, prop_tag: str) -> Optional[str]:
    unique_tags = {spec.tags.get(prop_tag) for spec in assets_def.specs}
    if len(unique_tags) > 1:
        check.invariant(assets_def.is_executable)
        check.invariant(assets_def.node_def)
        check.failed(f"Multiple {prop_tag} tags found in {assets_def.node_def.name}: {unique_tags}")
    return next(iter(unique_tags), None)
