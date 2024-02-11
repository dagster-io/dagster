from typing import Union

from dagster import _check as check
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.sensor_decorator import sensor
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.run_request import RunRequest, SensorResult, SkipReason
from dagster._core.definitions.sensor_definition import (
    DefaultSensorStatus,
    SensorDefinition,
    SensorEvaluationContext,
)


class PartitionSubsetFetcher:
    def __init__(
        self,
        assets_def: AssetsDefinition,
        asset_key: AssetKey,
        dynamic_partitions_store,
        current_time,
    ):
        self.assets_def = assets_def
        self.asset_key = asset_key
        self.dynamic_partitions_store = dynamic_partitions_store
        self.current_time = current_time

    @property
    def is_partitioned(self) -> bool:
        return bool(self.assets_def.partitions_def)

    def get_latest_asset_subset(self) -> AssetSubset:
        if not self.is_partitioned:
            return AssetSubset(self.asset_key, True)
        else:
            assert self.assets_def.partitions_def  # for pyright
            last_partition_key = self.assets_def.partitions_def.get_last_partition_key(
                current_time=self.current_time,
                dynamic_partitions_store=self.dynamic_partitions_store,
            )
            partitions_subset = self.assets_def.partitions_def.empty_subset()
            if last_partition_key:
                partitions_subset = partitions_subset.with_partition_keys([last_partition_key])
            return AssetSubset(self.asset_key, partitions_subset)


def build_reactive_scheduling_sensor(
    assets_def: AssetsDefinition, asset_key: AssetKey
) -> SensorDefinition:
    check.invariant(asset_key in assets_def.scheduling_policy_by_key)
    scheduling_policy = assets_def.scheduling_policy_by_key[asset_key]

    @sensor(
        name=scheduling_policy.sensor_name
        if scheduling_policy.sensor_name
        else f"{asset_key.to_python_identifier()}_reactive_scheduling_sensor",
        minimum_interval_seconds=10,
        default_status=DefaultSensorStatus.RUNNING,
        asset_selection="*",
    )
    def sensor_fn(context: SensorEvaluationContext) -> Union[SensorResult, SkipReason]:
        check.invariant(
            context.repository_def, "SensorEvaluationContext must have a repository_def"
        )
        assert context.repository_def

        # asset_graph = context.repository_def.asset_graph

        subset_fetcher = PartitionSubsetFetcher(
            assets_def=assets_def,
            asset_key=asset_key,
            dynamic_partitions_store=context.instance,
            current_time=None,
        )

        scheduling_result = scheduling_policy.schedule()

        if not scheduling_result.execute:
            return SkipReason(
                skip_message=f"Scheduling policy for {asset_key.to_user_string()} did not request execution"
            )

        latest_asset_subset = subset_fetcher.get_latest_asset_subset()

        # TODO support ranged backfils

        run_requests = []
        for ap in latest_asset_subset.asset_partitions:
            run_requests.append(
                RunRequest(asset_selection=[asset_key], partition_key=ap.partition_key)
            )

        return SensorResult(run_requests=run_requests)

    return sensor_fn
