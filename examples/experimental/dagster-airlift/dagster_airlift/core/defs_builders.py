from collections import defaultdict
from typing import Sequence, Union

from dagster import AssetsDefinition, AssetSpec, Definitions, multi_asset
from dagster._core.definitions.asset_key import CoercibleToAssetKey
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
