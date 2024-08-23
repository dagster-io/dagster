from typing import Dict, Mapping, Sequence, Union

from dagster import AssetsDefinition, AssetSpec, Definitions
from typing_extensions import TypeAlias

from dagster_airlift.core import combine_defs
from dagster_airlift.core.utils import DAG_ID_TAG, TASK_ID_TAG

CoercibleToDefs: TypeAlias = Union[AssetsDefinition, AssetSpec, Definitions]


class TaskDefs:
    def __init__(self, task_id: str, defs_list: Sequence[CoercibleToDefs]):
        self.task_id = task_id
        self.defs_list = defs_list


def apply_tags_to_all_specs(
    defs_list: Sequence[CoercibleToDefs], tags: Dict[str, str]
) -> Definitions:
    new_defs = []
    for def_ish in defs_list:
        if isinstance(def_ish, AssetSpec):
            new_defs.append(spec_with_tags(def_ish, tags))
        elif isinstance(def_ish, AssetsDefinition):
            new_defs.append(assets_def_with_af_tags(def_ish, tags))
        else:
            new_assets_defs = []
            for assets_def in def_ish.get_asset_graph().assets_defs:
                new_assets_defs.append(assets_def_with_af_tags(assets_def, tags))
            new_defs.append(
                Definitions(
                    assets=new_assets_defs,
                    resources=def_ish.resources,
                    sensors=def_ish.sensors,
                    schedules=def_ish.schedules,
                    jobs=def_ish.jobs,
                    loggers=def_ish.loggers,
                    executor=def_ish.executor,
                    asset_checks=def_ish.asset_checks,
                )
            )
    return combine_defs(*new_defs)


def spec_with_tags(spec: AssetSpec, tags: Mapping[str, str]) -> "AssetSpec":
    return spec._replace(tags={**spec.tags, **tags})


def assets_def_with_af_tags(
    assets_def: AssetsDefinition, tags: Mapping[str, str]
) -> AssetsDefinition:
    return assets_def.map_asset_specs(lambda spec: spec_with_tags(spec, tags))


def dag_defs(dag_id: str, *defs: TaskDefs) -> Definitions:
    defs_to_merge = []
    for task_def in defs:
        defs_to_merge.append(
            apply_tags_to_all_specs(
                task_def.defs_list,
                tags={DAG_ID_TAG: dag_id, TASK_ID_TAG: task_def.task_id},
            )
        )
    return Definitions.merge(*defs_to_merge)


def task_defs(task_id, *defs: Union[AssetsDefinition, Definitions, AssetSpec]) -> TaskDefs:
    return TaskDefs(task_id, defs)
