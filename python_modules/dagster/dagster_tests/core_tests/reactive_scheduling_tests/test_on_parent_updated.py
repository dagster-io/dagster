from dagster import DagsterInstance, Definitions, asset
from dagster._core.definitions.materialize import materialize
from dagster._core.reactive_scheduling.reactive_scheduling_plan import ReactiveSchedulingGraph
from dagster._core.reactive_scheduling.scheduling_policy import (
    AssetPartition,
    RequestReaction,
    SchedulingExecutionContext,
    SchedulingPolicy,
)
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from .test_policies import AlwaysLaunchSchedulingPolicy


def test_get_parent_asset_partitions_updated_after_child() -> None:
    @asset
    def up() -> None:
        ...

    @asset(deps=[up])
    def down() -> None:
        ...

    defs = Definitions(assets=[up, down])

    instance = DagsterInstance.ephemeral()

    assert materialize(assets=[up], instance=instance).success

    queryer = CachingInstanceQueryer(
        instance=instance, asset_graph=defs.get_repository_def().asset_graph
    )

    updated = queryer.get_parent_asset_partitions_updated_after_child(
        asset_partition=AssetPartition(down.key),
        parent_asset_partitions={AssetPartition(up.key)},
        respect_materialization_data_versions=True,
        ignored_parent_keys=set(),
    )

    assert updated == {AssetPartition(up.key)}


class OnAnyParentOutOfSyncPolicy(SchedulingPolicy):
    def react_to_downstream_request(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        # here we respect upstream versioning to see if we actually need this
        scheduling_graph = ReactiveSchedulingGraph.from_context(context)

        parent_partitions = scheduling_graph.get_all_parent_partitions(
            asset_partition=asset_partition,
        )

        # eventually this should be pre-computed
        updated_parent_partitions = context.queryer.get_parent_asset_partitions_updated_after_child(
            asset_partition=asset_partition,
            parent_asset_partitions=parent_partitions,
            respect_materialization_data_versions=True,
            ignored_parent_keys=set(),
        )

        return RequestReaction(include=bool(updated_parent_partitions))

    def react_to_upstream_request(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        # upstream demands request overrides any updating behavior
        # note: is this true?
        # TODO: what about getting the other upstreams?
        return RequestReaction(include=True)


def test_on_parent_basic_on_parent_updated() -> None:
    @asset
    def upup() -> None:
        ...

    @asset(deps=[upup], scheduling_policy=OnAnyParentOutOfSyncPolicy())
    def up() -> None:
        ...

    @asset(deps=[up], scheduling_policy=AlwaysLaunchSchedulingPolicy())
    def down() -> None:
        ...

    defs = Definitions(assets=[upup, up, down])

    queryer = CachingInstanceQueryer.ephemeral(defs)

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(instance=queryer.instance)
        .success
    )

    # # everything up-to-date

    # pulse_result = run_scheduling_pulse_on_asset(
    #     defs,
    #     "down",
    #     queryer=queryer,
    # )

    # assert set(pulse_result.run_requests[0].asset_selection or []) == {down.key}

    # assert materialize(assets=[upup], instance=queryer.instance).success

    # # new data in upup

    # pulse_result = run_scheduling_pulse_on_asset(
    #     defs,
    #     "down",
    #     queryer=queryer,
    # )

    # assert set(pulse_result.run_requests[0].asset_selection or []) == {down.key, up.key}
