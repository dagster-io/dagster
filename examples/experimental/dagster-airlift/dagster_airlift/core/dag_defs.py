from typing import Dict, Mapping, Sequence, Union

from dagster import AssetsDefinition, AssetSpec, Definitions
from typing_extensions import TypeAlias

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
    new_assets_defs = []
    new_specs = []
    for def_ish in defs_list:
        if isinstance(def_ish, AssetSpec):
            new_specs.append(spec_with_tags(def_ish, tags))
        elif isinstance(def_ish, AssetsDefinition):
            new_assets_defs.append(assets_def_with_af_tags(def_ish, tags))
        else:
            more_new_assets_defs = []
            for assets_def in def_ish.get_asset_graph().assets_defs:
                more_new_assets_defs.append(assets_def_with_af_tags(assets_def, tags))
            new_defs.append(
                Definitions(
                    assets=more_new_assets_defs,
                    resources=def_ish.resources,
                    sensors=def_ish.sensors,
                    schedules=def_ish.schedules,
                    jobs=def_ish.jobs,
                    loggers=def_ish.loggers,
                    executor=def_ish.executor,
                    asset_checks=def_ish.asset_checks,
                )
            )
    return Definitions.merge(Definitions(assets=new_specs + new_assets_defs), *new_defs)


def spec_with_tags(spec: AssetSpec, tags: Mapping[str, str]) -> "AssetSpec":
    return spec._replace(tags={**spec.tags, **tags})


def assets_def_with_af_tags(
    assets_def: AssetsDefinition, tags: Mapping[str, str]
) -> AssetsDefinition:
    return assets_def.map_asset_specs(lambda spec: spec_with_tags(spec, tags))


def dag_defs(dag_id: str, *defs: TaskDefs) -> Definitions:
    """Construct a Dagster :py:class:`Definitions` object with definitions
    associated with a particular Dag in Airflow that is being tracked by Airlift tooling.

    Concretely this adds tags to all asset specs in the provided definitions
    with the provided dag_id and task_id. Dag id is tagged with the
    "airlift/dag_id" key and task id is tagged with the "airlift/task_id" key.

    Used in concert with :py:func:`task_defs`.

    Example:
    .. code-block:: python
        defs = dag_defs(
            "dag_one",
            task_defs("task_one", AssetSpec(key="asset_one")),
            task_defs("task_two", AssetSpec(key="asset_two"), AssetSpec(key="asset_three")),
        )
    """
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
    """Associate a set of definitions with a particular task in Airflow that is being tracked
    by Airlift tooling.
    """
    return TaskDefs(task_id, defs)
