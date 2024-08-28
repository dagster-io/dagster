from typing import Sequence, Union

from dagster import AssetSpec
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
