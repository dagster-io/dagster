from typing import Sequence, Union

from dagster import AssetSpec
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from typing_extensions import TypeAlias

from .utils import metadata_for_task_mapping

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
        else AssetSpec(
            key=asset, metadata=metadata_for_task_mapping(task_id=task_id, dag_id=dag_id)
        )
        for asset in assets
    ]
