from typing import Sequence

from dagster import _check as check
from dagster._annotations import public
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.time_window_partitions import TimeWindow

from .system import StepExecutionContext


class AssetInputExecutionContext:
    """This class should not be instantiated directly by users."""

    def __init__(self, step_context: StepExecutionContext, input_name: str):
        self._step_context = step_context
        self._input_name = input_name

    @public
    @property
    def asset_key(self) -> AssetKey:
        return check.not_none(
            self._step_context.job_def.asset_layer.asset_key_for_input(
                node_handle=self._step_context.node_handle, input_name=self._input_name
            )
        )

    @public
    @property
    def partition_time_window(self) -> TimeWindow:
        return self._step_context.asset_partitions_time_window_for_input(self._input_name)

    @public
    @property
    def partition_key(self) -> str:
        return self._step_context.asset_partition_key_for_input(self._input_name)

    @public
    @property
    def partition_keys(self) -> Sequence[str]:
        return list(
            self._step_context.asset_partitions_subset_for_input(
                self._input_name
            ).get_partition_keys()
        )

    @public
    @property
    def partition_key_range(self) -> PartitionKeyRange:
        return self._step_context.asset_partition_key_range_for_input(self._input_name)
