from typing import Optional

from dagster import AssetsDefinition


def get_task_id_from_asset(assets_def: AssetsDefinition) -> Optional[str]:
    if assets_def.node_def.tags and "airlift/task_id" in assets_def.node_def.tags:
        return assets_def.node_def.tags["airlift/task_id"]
    if len(assets_def.node_def.name.split("__")) == 2:
        return assets_def.node_def.name.split("__")[1]
    return None


def get_dag_id_from_asset(assets_def: AssetsDefinition) -> Optional[str]:
    if assets_def.node_def.tags and "airlift/dag_id" in assets_def.node_def.tags:
        return assets_def.node_def.tags["airlift/dag_id"]
    if len(assets_def.node_def.name.split("__")) == 2:
        return assets_def.node_def.name.split("__")[0]
    return None
