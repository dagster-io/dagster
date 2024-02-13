from datetime import datetime
from typing import Optional, Set

from dagster import asset
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.partition_mapping import StaticPartitionMapping
from dagster._core.definitions.sensor_definition import build_sensor_context
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


class AlwaysDefer(SchedulingPolicy):
    def react_to_downstream_request(self, downstream_subset) -> RequestReaction:
        return RequestReaction(execute=True)

    def react_to_upstream_request(self, upstream_subset) -> RequestReaction:
        return RequestReaction(execute=True)


class DeferToDownstream(SchedulingPolicy):
    def react_to_downstream_request(self, downstream_subset) -> RequestReaction:
        return RequestReaction(execute=True)


class DeferToUpstream(SchedulingPolicy):
    def react_to_upstream_request(self, upstream_subset) -> RequestReaction:
        return RequestReaction(execute=True)


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


def build_plan(
    builder: ReactiveRequestBuilder,
    asset_key: CoercibleToAssetKey,
    partition_key: Optional[str] = None,
) -> ReactivePlan:
    if partition_key:
        return builder.build_for_asset_subset(
            builder.make_valid_subset(
                AssetKey.from_coercible(asset_key),
                asset_partition_set(
                    AssetPartition(AssetKey.from_coercible(asset_key), partition_key)
                ),
            )
        )
    else:
        return builder.build_plan(AssetKey.from_coercible(asset_key))


def asset_partition_set(*asset_partitions: AssetPartition) -> Set[AssetPartition]:
    return set(asset_partitions)


def asset_partition(
    asset_key: CoercibleToAssetKey, partition_key: Optional[str] = None
) -> AssetPartition:
    return AssetPartition(AssetKey.from_coercible(asset_key), partition_key)


def test_reactive_request_builder_two_assets() -> None:
    @asset(scheduling_policy=AlwaysDefer())
    def up() -> None:
        ...

    @asset(deps=[up], scheduling_policy=AlwaysDefer())
    def down() -> None:
        ...

    defs = Definitions([up, down])
    instance = DagsterInstance.ephemeral()
    builder = create_test_builder(defs, instance)

    down_plan = build_plan(builder, "down")
    assert down_plan.asset_partitions == asset_partition_set(
        asset_partition("up"), asset_partition("down")
    )

    up_plan = build_plan(builder, "up")
    assert up_plan.asset_partitions == asset_partition_set(
        asset_partition("up"), asset_partition("down")
    )


def test_reactive_request_builder_three_assets_always_defer() -> None:
    # test recursion

    @asset(scheduling_policy=AlwaysDefer())
    def root() -> None:
        ...

    @asset(scheduling_policy=AlwaysDefer(), deps=[root])
    def up() -> None:
        ...

    @asset(deps=[up], scheduling_policy=AlwaysDefer())
    def down() -> None:
        ...

    defs = Definitions([root, up, down])
    instance = DagsterInstance.ephemeral()
    builder = create_test_builder(defs, instance)

    assert build_plan(builder, "root").asset_partitions == asset_partition_set(
        asset_partition("root"), asset_partition("up"), asset_partition("down")
    )

    assert build_plan(builder, "up").asset_partitions == asset_partition_set(
        asset_partition("root"), asset_partition("up"), asset_partition("down")
    )

    assert build_plan(builder, "down").asset_partitions == asset_partition_set(
        asset_partition("root"), asset_partition("up"), asset_partition("down")
    )


def test_reactive_request_builder_three_assets_only_downstream_requests_accepted() -> None:
    # test recursion

    @asset(scheduling_policy=DeferToDownstream())
    def root() -> None:
        ...

    @asset(scheduling_policy=DeferToDownstream(), deps=[root])
    def up() -> None:
        ...

    @asset(deps=[up], scheduling_policy=DeferToDownstream())
    def down() -> None:
        ...

    defs = Definitions([root, up, down])
    instance = DagsterInstance.ephemeral()
    builder = create_test_builder(defs, instance)

    assert build_plan(builder, "root").asset_partitions == asset_partition_set(
        asset_partition("root")
    )

    assert build_plan(builder, "up").asset_partitions == asset_partition_set(
        asset_partition("root"), asset_partition("up")
    )

    assert build_plan(builder, "down").asset_partitions == asset_partition_set(
        asset_partition("root"), asset_partition("up"), asset_partition("down")
    )


def test_reactive_request_builder_two_assets_with_partition_mapping_all_defer() -> None:
    partitions_def_up = StaticPartitionsDefinition(["up1", "up2"])
    partitions_def_down = StaticPartitionsDefinition(["down1", "down2"])

    up_to_down_mapping = StaticPartitionMapping({"up1": "down1", "up2": "down2"})

    @asset(scheduling_policy=AlwaysDefer(), partitions_def=partitions_def_up)
    def up() -> None:
        ...

    @asset(
        deps=[AssetDep("up", partition_mapping=up_to_down_mapping)],
        partitions_def=partitions_def_down,
        scheduling_policy=AlwaysDefer(),
    )
    def down() -> None:
        ...

    defs = Definitions([up, down])

    instance = DagsterInstance.ephemeral()
    builder = create_test_builder(defs, instance)

    assert build_plan(builder, "down", "down1").asset_partitions == asset_partition_set(
        asset_partition("up", "up1"), asset_partition("down", "down1")
    )

    assert build_plan(builder, "down", "down2").asset_partitions == asset_partition_set(
        asset_partition("up", "up2"), asset_partition("down", "down2")
    )

    assert build_plan(builder, "up", "up1").asset_partitions == asset_partition_set(
        asset_partition("up", "up1"), asset_partition("down", "down1")
    )

    assert build_plan(builder, "up", "up2").asset_partitions == asset_partition_set(
        asset_partition("up", "up2"), asset_partition("down", "down2")
    )


def test_reactive_request_builder_two_assets_with_partition_mapping_defer_to_up() -> None:
    root_partitions = StaticPartitionsDefinition(["root1", "root2"])
    up_partitions = StaticPartitionsDefinition(["up1", "up2"])
    down_partitions = StaticPartitionsDefinition(["down1", "down2"])

    root_to_up_mapping = StaticPartitionMapping({"root1": "up1", "root2": "up2"})
    up_to_down_mapping = StaticPartitionMapping({"up1": "down1", "up2": "down2"})

    @asset(scheduling_policy=DeferToUpstream(), partitions_def=root_partitions)
    def root() -> None:
        ...

    @asset(
        deps=[AssetDep("root", partition_mapping=root_to_up_mapping)],
        partitions_def=up_partitions,
        scheduling_policy=DeferToUpstream(),
    )
    def up() -> None:
        ...

    @asset(
        deps=[AssetDep("up", partition_mapping=up_to_down_mapping)],
        partitions_def=down_partitions,
        scheduling_policy=DeferToUpstream(),
    )
    def down() -> None:
        ...

    defs = Definitions([root, up, down])

    instance = DagsterInstance.ephemeral()
    builder = create_test_builder(defs, instance)

    assert build_plan(builder, "root", "root1").asset_partitions == asset_partition_set(
        asset_partition("root", "root1"),
        asset_partition("up", "up1"),
        asset_partition("down", "down1"),
    )

    assert build_plan(builder, "up", "up1").asset_partitions == asset_partition_set(
        asset_partition("up", "up1"),
        asset_partition("down", "down1"),
    )

    assert build_plan(builder, "down", "down1").asset_partitions == asset_partition_set(
        asset_partition("down", "down1")
    )


def test_basic_tick() -> None:
    class SchedulingPolicyWithTick(SchedulingPolicy):
        tick_cron = "*/1 * * * *"

        def schedule(self) -> SchedulingResult:
            return SchedulingResult(execute=True)

    @asset(scheduling_policy=DeferToDownstream())
    def up() -> None:
        ...

    @asset(deps=[up], scheduling_policy=SchedulingPolicyWithTick(sensor_name="the_sensor"))
    def ticking_asset() -> None:
        pass

    defs = Definitions([up, ticking_asset])

    sensor_def = defs.get_sensor_def("the_sensor")
    assert sensor_def

    instance = DagsterInstance.ephemeral()
    with build_sensor_context(
        instance=instance, repository_def=defs.get_repository_def()
    ) as context:
        eval_data = sensor_def.evaluate_tick(context=context)
