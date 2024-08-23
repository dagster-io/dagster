from collections import defaultdict
from typing import Sequence, Union

from dagster import AssetsDefinition, AssetSpec, Definitions, multi_asset
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster._core.definitions.op_definition import OpDefinition
from typing_extensions import TypeAlias

from .utils import DAG_ID_TAG, TASK_ID_TAG

CoercibleToAssetSpec: TypeAlias = Union[AssetSpec, CoercibleToAssetKey]


def specs_from_task(
    *, task_id: str, dag_id: str, assets: Sequence[CoercibleToAssetSpec]
) -> Sequence[AssetSpec]:
    """Construct a Dagster :py:class:`Definitions` object from a provided set of assets,
    with a mapping to which airflow task produces those assets.
    """
    return [
        asset
        if isinstance(asset, AssetSpec)
        else AssetSpec(key=asset, tags={DAG_ID_TAG: dag_id, TASK_ID_TAG: task_id})
        for asset in assets
    ]


def combine_defs(*defs: Union[AssetsDefinition, Definitions, AssetSpec]) -> Definitions:
    """Combine provided :py:class:`Definitions` objects and assets into a single object, which contains all constituent definitions."""
    assets = []
    specs_by_task_and_dag = defaultdict(list)
    for _def in defs:
        if isinstance(_def, Definitions):
            continue
        elif isinstance(_def, AssetsDefinition):
            assets.append(_def)
        elif isinstance(_def, AssetSpec):
            dag_id = _def.tags[DAG_ID_TAG]
            task_id = _def.tags[TASK_ID_TAG]
            specs_by_task_and_dag[(dag_id, task_id)].append(_def)
        else:
            raise Exception(f"Unexpected type: {type(_def)}")
    for (dag_id, task_id), specs in specs_by_task_and_dag.items():

        @multi_asset(specs=specs, name=f"{dag_id}__{task_id}")
        def _multi_asset():
            pass

        assets.append(_multi_asset)

    return Definitions.merge(
        *[the_def for the_def in defs if isinstance(the_def, Definitions)],
        Definitions(assets=assets),
    )


class WithAirflowTags:
    def __init__(self, dag_id: str, task_id: str):
        self.dag_id = dag_id
        self.task_id = task_id

    def spec_with_af_tags(self, spec: AssetSpec) -> AssetSpec:
        return spec.with_tags({DAG_ID_TAG: self.dag_id, TASK_ID_TAG: self.task_id})

    def defs(self, *defs: Union[AssetSpec, AssetsDefinition, Definitions]) -> Definitions:
        new_defs = []
        for def_ in defs:
            if isinstance(def_, AssetSpec):
                new_defs.append(self.spec_with_af_tags(def_))
            elif isinstance(def_, AssetsDefinition):
                new_defs.append(self.assets_def_with_af_tags(def_))
            else:
                new_assets_defs = []
                for assets_def in def_.get_asset_graph().assets_defs:
                    new_assets_defs.append(self.assets_def_with_af_tags(assets_def))
                new_defs.append(
                    Definitions(
                        assets=new_assets_defs,
                        resources=def_.resources,
                        sensors=def_.sensors,
                        schedules=def_.schedules,
                        jobs=def_.jobs,
                        loggers=def_.loggers,
                        executor=def_.executor,
                        asset_checks=def_.asset_checks,
                    )
                )
        return combine_defs(*defs)

    def assets_def_with_af_tags(self, assets_def: AssetsDefinition) -> AssetsDefinition:
        new_assets_def = assets_def.map_asset_specs(self.spec_with_af_tags)
        # I am a bad person. Need primitive to add tags to a node in an AssetsDefinition
        # and return a copy
        assert isinstance(new_assets_def.node_def, OpDefinition)
        assert isinstance(new_assets_def.node_def.tags, dict)
        new_assets_def.node_def.tags[DAG_ID_TAG] = self.dag_id
        new_assets_def.node_def.tags[TASK_ID_TAG] = self.task_id
        return new_assets_def


def from_airflow(dag_id: str, task_id: str) -> WithAirflowTags:
    return WithAirflowTags(dag_id, task_id)
