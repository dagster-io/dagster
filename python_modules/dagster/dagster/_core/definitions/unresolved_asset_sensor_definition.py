from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Optional, Sequence

from dagster._core.definitions.events import AssetObservation

from .asset_selection import AssetSelection
from .sensor_definition import (
    DagsterInvalidDefinitionError,
    DefaultSensorStatus,
    MultiAssetSensorDefinition,
    MultiAssetSensorEvaluationContext,
    RawSensorEvaluationFunctionReturn,
)
from .target import ExecutableDefinition

if TYPE_CHECKING:
    from dagster._core.definitions import AssetsDefinition, SourceAsset


class UnresolvedAssetSensorDefinition(ABC):
    def __init__(
        self,
        asset_selection: AssetSelection,
        name: str,
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    ):
        self._selection = asset_selection
        self._name = name
        self._minimum_interval_seconds = minimum_interval_seconds
        self._description = description
        self._default_status = default_status

    @abstractmethod
    def resolve(
        self,
        assets: Sequence["AssetsDefinition"],
        source_assets: Sequence["SourceAsset"],
    ):
        raise NotImplementedError()

    @property
    def name(self):
        return self._name


# class UnresolvedMultiAssetSensorDefinition(UnresolvedAssetSensorDefinition):
#     def __init__(
#         self,
#         asset_materialization_fn: Callable[
#             [MultiAssetSensorEvaluationContext],
#             RawSensorEvaluationFunctionReturn,
#         ],
#         asset_selection: AssetSelection,
#         name: str,
#         minimum_interval_seconds: Optional[int] = None,
#         description: Optional[str] = None,
#         default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
#         job_name: Optional[str] = None,
#         job: Optional[ExecutableDefinition] = None,
#         jobs: Optional[Sequence[ExecutableDefinition]] = None,
#     ):
#         self._asset_materialization_fn = asset_materialization_fn
#         self._job_name = job_name
#         self._job = job
#         self._jobs = jobs
#         self._selection = asset_selection

#         super().__init__(
#             asset_selection,
#             name,
#             minimum_interval_seconds,
#             description,
#             default_status,
#         )

#     def resolve(
#         self,
#         assets: Sequence["AssetsDefinition"],
#         source_assets: Sequence["SourceAsset"],
#     ):
#         selected_asset_keys = self._selection.resolve([*assets])

#         selected_assets = []
#         for asset in assets:
#             if any([key in selected_asset_keys for key in asset.keys]):
#                 if not all([key in selected_asset_keys for key in asset.keys]):
#                     raise DagsterInvalidDefinitionError(
#                         "For each asset key selected, must select all "
#                         "other asset keys in the AssetsDefinition."
#                     )
#                 selected_assets.append(asset)

#         return MultiAssetSensorDefinition(
#             name=self._name,
#             assets=selected_assets,
#             asset_materialization_fn=self._asset_materialization_fn,
#             minimum_interval_seconds=self._minimum_interval_seconds,
#             description=self._description,
#             default_status=self._default_status,
#             job_name=self._job_name,
#             job=self._job,
#             jobs=self._jobs,
#         )
