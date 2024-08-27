from typing import Dict, Mapping, Union

from dagster import AssetsDefinition, AssetSpec, Definitions
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.source_asset import SourceAsset

from dagster_airlift.core.utils import DAG_ID_TAG, TASK_ID_TAG


class TaskDefs:
    def __init__(self, task_id: str, defs: Definitions):
        self.task_id = task_id
        self.defs = defs


def apply_tags_to_all_specs(defs: Definitions, tags: Dict[str, str]) -> Definitions:
    return Definitions(
        assets=[
            assets_def_with_af_tags(
                asset_ish,
                tags,
            )
            # https://linear.app/dagster-labs/issue/FOU-367/investigate-weird-behavior-in-apply-tags-to-all-spec
            # Note: Using get_asset_graph().assets_defs causes resource collisions for reasons unknown
            # for assets_def in defs.get_asset_graph().assets_defs
            for asset_ish in (defs.assets or [])
        ],
        resources=defs.resources,
        sensors=defs.sensors,
        schedules=defs.schedules,
        jobs=defs.jobs,
        loggers=defs.loggers,
        executor=defs.executor,
        asset_checks=defs.asset_checks,
    )


def spec_with_tags(spec: AssetSpec, tags: Mapping[str, str]) -> "AssetSpec":
    return spec._replace(tags={**spec.tags, **tags})


# because of the use of def.assets in apply_tags_to_all_specs, we need to handle AssetSpecs here as well
def assets_def_with_af_tags(
    asset_ish: Union[AssetSpec, AssetsDefinition, CacheableAssetsDefinition, SourceAsset],
    tags: Mapping[str, str],
) -> Union[AssetsDefinition, AssetSpec, CacheableAssetsDefinition, SourceAsset]:
    # check.inst_param(assets_def_or_spec, "assets_def_or_spec", (AssetSpec, AssetsDefinition))
    if isinstance(asset_ish, AssetSpec):
        return spec_with_tags(asset_ish, tags)
    else:
        assert isinstance(asset_ish, AssetsDefinition)
        return asset_ish.map_asset_specs(lambda spec: spec_with_tags(spec, tags))


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
            task_defs("task_one", Definitions(assets=[AssetSpec(key="asset_one"]))),
            task_defs("task_two", Definitions(assets=[AssetSpec(key="asset_two"), AssetSpec(key="asset_three")])),
        )
    """
    defs_to_merge = []
    for task_def in defs:
        defs_to_merge.append(
            apply_tags_to_all_specs(
                defs=task_def.defs,
                tags={DAG_ID_TAG: dag_id, TASK_ID_TAG: task_def.task_id},
            )
        )
    return Definitions.merge(*defs_to_merge)


def task_defs(task_id, defs: Definitions) -> TaskDefs:
    """Associate a set of definitions with a particular task in Airflow that is being tracked
    by Airlift tooling.
    """
    return TaskDefs(task_id, defs)
