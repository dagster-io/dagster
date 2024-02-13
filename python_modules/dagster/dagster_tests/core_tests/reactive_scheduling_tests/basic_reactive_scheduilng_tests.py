from datetime import datetime
from typing import Optional, Set

from dagster import asset
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.instance import DagsterInstance
from dagster._core.reactive_scheduling.reactive_policy import (
    AssetPartition,
    RequestReaction,
    SchedulingPolicy,
    SchedulingResult,
)
from dagster._core.reactive_scheduling.reactive_scheduling_sensor_factory import (
    ReactivePlan,
    ReactiveRequestBuilder,
)


def scheduling_policy_of_asset(
    assets_def: AssetsDefinition, asset_key: Optional[CoercibleToAssetKey] = None
) -> SchedulingPolicy:
    if asset_key:
        return assets_def.scheduling_policy_by_key[AssetKey.from_coercible(asset_key)]
    else:
        return assets_def.scheduling_policy_by_key[assets_def.key]


def test_thread_through_asset_property() -> None:
    class EmptySchedulingPolicy(SchedulingPolicy):
        ...

    @asset(
        scheduling_policy=EmptySchedulingPolicy(),
    )
    def an_asset() -> None:
        ...

    assert isinstance(scheduling_policy_of_asset(an_asset), EmptySchedulingPolicy)
    assert isinstance(scheduling_policy_of_asset(an_asset, "an_asset"), EmptySchedulingPolicy)


def test_creation_of_sensor() -> None:
    class SchedulingPolicyWithTick(SchedulingPolicy):
        tick_cron = "*/1 * * * *"

        def schedule(self) -> SchedulingResult:
            return SchedulingResult(execute=True)

    @asset(
        scheduling_policy=SchedulingPolicyWithTick(),
    )
    def an_asset() -> None:
        ...

    defs = Definitions([an_asset])
    assert len(defs.get_repository_def().sensor_defs) == 1
    sensor_def = defs.get_repository_def().sensor_defs[0]
    assert "reactive_scheduling_sensor" in sensor_def.name


def create_test_builder(
    defs: Definitions, instance: DagsterInstance, current_time: Optional[datetime] = None
) -> ReactiveRequestBuilder:
    return ReactiveRequestBuilder(
        asset_graph=defs.get_repository_def().asset_graph,
        dynamic_partitions_store=instance,
        current_time=current_time if current_time else datetime.now(),
        repository_def=defs.get_repository_def(),
    )


def build_plan(builder: ReactiveRequestBuilder, asset_key: CoercibleToAssetKey) -> ReactivePlan:
    return builder.build_plan(AssetKey.from_coercible(asset_key))


def asset_partition_set(*asset_partitions: AssetPartition) -> Set[AssetPartition]:
    return set(asset_partitions)


def asset_partition(
    asset_key: CoercibleToAssetKey, partition_key: Optional[str] = None
) -> AssetPartition:
    return AssetPartition(AssetKey.from_coercible(asset_key), partition_key)


def test_reactive_request_builder() -> None:
    class DeferToDownstreamSchedulingPolicy(SchedulingPolicy):
        def react_to_downstream_request(self, asset_partition) -> RequestReaction:
            return RequestReaction(execute=True)

    @asset(scheduling_policy=DeferToDownstreamSchedulingPolicy())
    def up() -> None:
        ...

    @asset(deps=[up], scheduling_policy=DeferToDownstreamSchedulingPolicy())
    def down() -> None:
        ...

    defs = Definitions([up, down])
    instance = DagsterInstance.ephemeral()
    builder = create_test_builder(defs, instance)

    plan = build_plan(builder, "down")
    assert plan.asset_partitions == asset_partition_set(
        asset_partition("up"), asset_partition("down")
    )

    plan = build_plan(builder, "up")
    assert plan.asset_partitions == asset_partition_set(
        asset_partition("up"), asset_partition("down")
    )
