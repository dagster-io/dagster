from datetime import datetime
from typing import Optional, Set
from uuid import uuid4

import pendulum
from dagster import (
    asset,
)
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_subset import ValidAssetSubset
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.decorators.source_asset_decorator import observable_source_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.observe import observe
from dagster._core.definitions.partition import (
    StaticPartitionsDefinition,
)
from dagster._core.definitions.partition_mapping import StaticPartitionMapping
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    TimeWindow,
)
from dagster._core.instance import DagsterInstance
from dagster._core.reactive_scheduling.asset_graph_traverser import AssetSubsetFactory
from dagster._core.reactive_scheduling.scheduling_plan import (
    OnAnyNewParentUpdated,
    ReactiveSchedulingPlan,
    Rules,
    build_reactive_scheduling_plan,
)
from dagster._core.reactive_scheduling.scheduling_policy import (
    AssetPartition,
    SchedulingExecutionContext,
    SchedulingPolicy,
)

from .test_policies import AlwaysIncludeSchedulingPolicy, NeverIncludeSchedulingPolicy


def test_include_scheduling_policy() -> None:
    assert SchedulingPolicy


def build_test_context(
    defs: Definitions,
    instance: Optional[DagsterInstance] = None,
    tick_dt: Optional[datetime] = None,
    last_storage_id: Optional[int] = None,
) -> SchedulingExecutionContext:
    return SchedulingExecutionContext.create(
        instance=instance or DagsterInstance.ephemeral(),
        repository_def=defs.get_repository_def(),
        tick_dt=tick_dt or pendulum.now(),
        last_storage_id=last_storage_id,
    )


def test_scheduling_policy_parameter() -> None:
    scheduling_policy = SchedulingPolicy()

    @asset(scheduling_policy=scheduling_policy)
    def an_asset() -> None:
        raise Exception("never executed")

    assert an_asset.scheduling_policies_by_key[AssetKey(["an_asset"])] is scheduling_policy

    defs = Definitions([an_asset])
    ak = AssetKey(["an_asset"])
    assert defs.get_assets_def(ak).scheduling_policies_by_key[ak] is scheduling_policy


def test_create_scheduling_execution_context() -> None:
    defs = Definitions([])

    instance = DagsterInstance.ephemeral()

    context = build_test_context(defs, instance)

    assert context
    assert context.queryer
    assert context.instance
    assert context.instance is instance


def test_partition_space() -> None:
    letters_static_partition_def = StaticPartitionsDefinition(["A", "B", "C"])
    numbers_static_partition_def = StaticPartitionsDefinition(["1", "2", "3"])

    @asset(partitions_def=letters_static_partition_def)
    def up_letters() -> None:
        ...

    letter_to_number_mapping = StaticPartitionMapping({"A": "1", "B": "2", "C": "3"})

    @asset(
        deps=[AssetDep(up_letters, partition_mapping=letter_to_number_mapping)],
        partitions_def=numbers_static_partition_def,
    )
    def down_numbers() -> None:
        ...

    defs = Definitions([up_letters, down_numbers])

    # asset_job = defs.get_implicit_job_def_for_assets([up_letters.key, down_numbers.key])
    # import code

    # code.interact(local=locals())
    # assert asset_job

    instance = DagsterInstance.ephemeral()

    tick_dt = pendulum.now()

    context = SchedulingExecutionContext.create(
        instance=instance,
        repository_def=defs.get_repository_def(),
        tick_dt=tick_dt,
        last_storage_id=None,
    )

    traverser = context.traverser

    starting_subset = AssetSubsetFactory.from_partition_keys(
        context.asset_graph, down_numbers.key, {"1"}
    )
    upward = traverser.parent_asset_subset(up_letters.key, starting_subset)
    assert upward.asset_key == up_letters.key
    assert set(upward.subset_value.get_partition_keys()) == {"A"}

    upward_from_down_1 = traverser.create_upstream_partition_space(
        AssetSubsetFactory.from_partition_keys(context.asset_graph, down_numbers.key, {"1"})
    )
    assert set(
        upward_from_down_1.asset_graph_subset.partitions_subsets_by_asset_key[
            up_letters.key
        ].get_partition_keys()
    ) == {"A"}

    assert upward_from_down_1.get_asset_subset(up_letters.key).asset_partitions == {
        AssetPartition(up_letters.key, "A")
    }

    assert upward_from_down_1.root_asset_keys == {up_letters.key}
    assert upward_from_down_1.toposort_asset_levels == [{up_letters.key}, {down_numbers.key}]
    assert upward_from_down_1.toposort_asset_keys == [up_letters.key, down_numbers.key]

    upward_from_up_a = traverser.create_upstream_partition_space(
        AssetSubsetFactory.from_partition_keys(context.asset_graph, up_letters.key, {"A"})
    )

    assert upward_from_up_a.root_asset_keys == {up_letters.key}
    assert upward_from_up_a.toposort_asset_keys == [up_letters.key]


def test_two_assets_always_include() -> None:
    @asset(scheduling_policy=AlwaysIncludeSchedulingPolicy())
    def up() -> None:
        ...

    @asset(deps=[up], scheduling_policy=AlwaysIncludeSchedulingPolicy())
    def down() -> None:
        ...

    defs = Definitions([up, down])

    assert materialize([up, down]).success

    instance = DagsterInstance.ephemeral()

    context = build_test_context(defs, instance)

    plan = build_reactive_scheduling_plan(
        context=context,
        starting_subsets=[AssetSubsetFactory.unpartitioned(context.asset_graph, down.key)],
    )

    assert plan.launch_partition_space.get_asset_subset(up.key).bool_value


def test_three_assets_one_root_always_include_diamond() -> None:
    @asset(scheduling_policy=AlwaysIncludeSchedulingPolicy())
    def up() -> None:
        ...

    @asset(deps=[up], scheduling_policy=AlwaysIncludeSchedulingPolicy())
    def down1() -> None:
        ...

    @asset(deps=[up], scheduling_policy=AlwaysIncludeSchedulingPolicy())
    def down2() -> None:
        ...

    defs = Definitions([up, down1, down2])

    instance = DagsterInstance.ephemeral()

    context = build_test_context(defs, instance)

    plan = build_reactive_scheduling_plan(
        context=context,
        starting_subsets=[AssetSubsetFactory.unpartitioned(context.asset_graph, down1.key)],
    )

    assert plan.launch_partition_space.asset_keys == {up.key, down2.key, down1.key}

    assert plan.launch_partition_space.get_asset_subset(up.key).bool_value


def test_three_assets_one_root_one_excludes_diamond() -> None:
    @asset(scheduling_policy=AlwaysIncludeSchedulingPolicy())
    def up() -> None:
        ...

    @asset(deps=[up], scheduling_policy=AlwaysIncludeSchedulingPolicy())
    def down1() -> None:
        ...

    @asset(deps=[up], scheduling_policy=NeverIncludeSchedulingPolicy())
    def down2() -> None:
        ...

    defs = Definitions([up, down1, down2])

    instance = DagsterInstance.ephemeral()

    context = build_test_context(defs, instance)

    plan = build_reactive_scheduling_plan(
        context=context,
        starting_subsets=[AssetSubsetFactory.unpartitioned(context.asset_graph, down1.key)],
    )

    # down2 should not be included in the launch
    assert plan.launch_partition_space.asset_keys == {up.key, down1.key}

    assert plan.launch_partition_space.get_asset_subset(up.key).bool_value


def partition_keys(plan: ReactiveSchedulingPlan, asset_key: AssetKey) -> Set[str]:
    return set(
        plan.launch_partition_space.get_asset_subset(asset_key).subset_value.get_partition_keys()
    )


def test_basic_partition_launch() -> None:
    letters_static_partition_def = StaticPartitionsDefinition(["A", "B", "C"])
    numbers_static_partition_def = StaticPartitionsDefinition(["1", "2", "3"])

    @asset(
        partitions_def=letters_static_partition_def,
        scheduling_policy=AlwaysIncludeSchedulingPolicy(),
    )
    def up_letters() -> None:
        ...

    letter_to_number_mapping = StaticPartitionMapping({"A": "1", "B": "2", "C": "3"})

    @asset(
        deps=[AssetDep(up_letters, partition_mapping=letter_to_number_mapping)],
        partitions_def=numbers_static_partition_def,
        scheduling_policy=AlwaysIncludeSchedulingPolicy(),
    )
    def down_numbers() -> None:
        ...

    defs = Definitions([up_letters, down_numbers])

    instance = DagsterInstance.ephemeral()

    context = build_test_context(defs, instance)

    plan_from_down_2 = build_reactive_scheduling_plan(
        context=context,
        starting_subsets=[
            AssetSubsetFactory.from_partition_keys(context.asset_graph, down_numbers.key, {"2"})
        ],
    )

    assert partition_keys(plan_from_down_2, up_letters.key) == {"B"}

    plan_from_down_3 = build_reactive_scheduling_plan(
        context=context,
        starting_subsets=[
            AssetSubsetFactory.from_partition_keys(context.asset_graph, down_numbers.key, {"3"})
        ],
    )

    assert partition_keys(plan_from_down_3, up_letters.key) == {"C"}


def test_time_windowing_partition() -> None:
    start = pendulum.datetime(2021, 1, 1)
    end = pendulum.datetime(2021, 1, 2)
    daily_partitions_def = DailyPartitionsDefinition(start_date=start, end_date=end)
    hourly_partitions_def = HourlyPartitionsDefinition(start_date=start, end_date=end)

    @asset(partitions_def=hourly_partitions_def, scheduling_policy=AlwaysIncludeSchedulingPolicy())
    def up_hourly() -> None:
        ...

    @asset(
        deps=[up_hourly],
        partitions_def=daily_partitions_def,
        scheduling_policy=AlwaysIncludeSchedulingPolicy(),
    )
    def down_daily() -> None:
        ...

    defs = Definitions([up_hourly, down_daily])

    instance = DagsterInstance.ephemeral()

    context = build_test_context(defs, instance)

    plan = build_reactive_scheduling_plan(
        context=context,
        starting_subsets=[
            AssetSubsetFactory.from_time_window(
                context.asset_graph, up_hourly.key, TimeWindow(start, end)
            )
        ],
    )

    assert (
        plan.launch_partition_space.get_asset_subset(down_daily.key).asset_partitions
        == AssetSubsetFactory.from_time_window(
            context.asset_graph, down_daily.key, TimeWindow(start, end)
        ).asset_partitions
    )


from dagster import _check as check


def subsets_equal(left: ValidAssetSubset, right: ValidAssetSubset) -> bool:
    if left.asset_key != right.asset_key:
        return False
    if left.is_partitioned and right.is_partitioned:
        return set(left.subset_value.get_partition_keys()) == set(
            right.subset_value.get_partition_keys()
        )
    elif not left.is_partitioned and not right.is_partitioned:
        return left.bool_value == right.bool_value
    else:
        check.failed("should not get here with valid subsets")


def test_on_any_parent_updated() -> None:
    @asset
    def upup() -> None:
        ...

    @asset(deps=[upup], scheduling_policy=OnAnyNewParentUpdated())
    def up() -> None:
        ...

    @asset(deps=[up], scheduling_policy=AlwaysIncludeSchedulingPolicy())
    def down() -> None:
        ...

    defs = Definitions([upup, up, down])

    instance = DagsterInstance.ephemeral()

    context_one = build_test_context(defs, instance)

    down_subset = AssetSubsetFactory.unpartitioned(context_one.asset_graph, down.key)
    up_subset = AssetSubsetFactory.unpartitioned(context_one.asset_graph, up.key)
    upup_subset = AssetSubsetFactory.unpartitioned(context_one.asset_graph, upup.key)

    assert materialize([up], instance=instance).success

    assert Rules.any_parent_updated(context_one, down_subset).bool_value
    assert not Rules.any_parent_updated(context_one, up_subset).bool_value
    assert not Rules.any_parent_updated(context_one, upup_subset).bool_value

    assert subsets_equal(
        OnAnyNewParentUpdated().evaluate(context_one, down_subset).asset_subset, down_subset
    )
    assert subsets_equal(
        OnAnyNewParentUpdated().evaluate(context_one, up_subset).asset_subset,
        context_one.empty_subset(up.key),
    )
    assert subsets_equal(
        OnAnyNewParentUpdated().evaluate(context_one, upup_subset).asset_subset,
        context_one.empty_subset(upup.key),
    )

    plan_one = build_reactive_scheduling_plan(
        context=context_one,
        starting_subsets=[down_subset],
    )

    assert plan_one.launch_partition_space.get_asset_subset(down.key).bool_value
    assert not plan_one.launch_partition_space.get_asset_subset(up.key).bool_value
    assert not plan_one.launch_partition_space.get_asset_subset(upup.key).bool_value

    assert materialize([upup], instance=instance).success

    # with upup updated, up should be return true for any parent updated and should be included in launch plan

    context_two = build_test_context(defs, instance)

    assert Rules.any_parent_updated(context_two, down_subset).bool_value
    assert Rules.any_parent_updated(context_two, up_subset).bool_value
    assert not Rules.any_parent_updated(context_two, upup_subset).bool_value

    assert subsets_equal(
        OnAnyNewParentUpdated().evaluate(context_two, down_subset).asset_subset, down_subset
    )
    assert subsets_equal(
        OnAnyNewParentUpdated().evaluate(context_two, up_subset).asset_subset, up_subset
    )
    assert subsets_equal(
        OnAnyNewParentUpdated().evaluate(context_two, upup_subset).asset_subset,
        context_two.empty_subset(upup.key),
    )

    plan_two = build_reactive_scheduling_plan(
        context=context_two,
        starting_subsets=[down_subset],
    )

    assert plan_two.launch_partition_space.get_asset_subset(down.key).bool_value
    assert plan_two.launch_partition_space.get_asset_subset(up.key).bool_value
    assert not plan_two.launch_partition_space.get_asset_subset(upup.key).bool_value


def test_any_all_parent_out_of_sync() -> None:
    @observable_source_asset
    def observable_one() -> DataVersion:
        return DataVersion(str(uuid4()))
        ...

    @observable_source_asset
    def observable_two() -> DataVersion:
        return DataVersion(str(uuid4()))
        ...

    @asset(deps=[observable_one])
    def asset_one() -> None:
        ...

    @asset(deps=[observable_two])
    def asset_two() -> None:
        ...

    @asset(deps=[asset_one, asset_two], scheduling_policy=AlwaysIncludeSchedulingPolicy())
    def downstream() -> None:
        ...

    defs = Definitions([observable_one, observable_two, asset_one, asset_two, downstream])

    instance = DagsterInstance.ephemeral()

    assert observe([observable_one, observable_two], instance=instance).success
    assert materialize([asset_one, asset_two, downstream], instance=instance).success
    # all observed, then materialized. Should be synced

    context_t0 = build_test_context(defs, instance)

    downstream_subset = AssetSubsetFactory.unpartitioned(context_t0.asset_graph, downstream.key)
    assert not Rules.any_parent_out_of_sync(context_t0, downstream_subset).bool_value
    assert not Rules.all_parents_out_of_sync(context_t0, downstream_subset).bool_value

    assert observe([observable_one], instance=instance).success

    # # one observed. asset_one out of sync. any but not all out of sync
    context_t1 = build_test_context(defs, instance)
    assert Rules.any_parent_out_of_sync(context_t1, downstream_subset).bool_value
    assert not Rules.all_parents_out_of_sync(context_t1, downstream_subset).bool_value
