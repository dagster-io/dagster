from typing import Sequence, Union

from dagster import AssetSpec
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from typing_extensions import TypeAlias

from dagster_airlift.constants import DAG_ID_METADATA_KEY, TASK_ID_METADATA_KEY

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
            key=asset, metadata={DAG_ID_METADATA_KEY: dag_id, TASK_ID_METADATA_KEY: task_id}
        )
        for asset in assets
    ]
