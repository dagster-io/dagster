from uuid import uuid4

from dagster import DagsterInstance, Definitions, asset
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.decorators.source_asset_decorator import observable_source_asset
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.observe import observe
from dagster._core.reactive_scheduling.reactive_scheduling_plan import ReactiveSchedulingGraph
from dagster._core.reactive_scheduling.scheduling_policy import (
    AssetPartition,
    RequestReaction,
    SchedulingExecutionContext,
    SchedulingPolicy,
)
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from .test_policies import AlwaysLaunchSchedulingPolicy, run_scheduling_pulse_on_asset


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


class IncludeOnAnyParentOutOfSync(SchedulingPolicy):
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


class IncludeOnAllParentsOutOfSync(SchedulingPolicy):
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

        return RequestReaction(include=updated_parent_partitions == parent_partitions)

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

    @asset(deps=[upup], scheduling_policy=IncludeOnAnyParentOutOfSync())
    def up() -> None:
        ...

    @asset(deps=[up], scheduling_policy=AlwaysLaunchSchedulingPolicy())
    def down() -> None:
        ...

    defs = Definitions(assets=[upup, up, down])

    instance = DagsterInstance.ephemeral()

    assert defs.get_implicit_global_asset_job_def().execute_in_process(instance=instance).success

    # everything up-to-date

    pulse_result = run_scheduling_pulse_on_asset(defs, "down", instance=instance)

    # this should only launch itself
    assert set(pulse_result.run_requests[0].asset_selection or []) == {down.key}

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(instance=instance, asset_selection=[upup.key])
        .success
    )

    # new data in upup

    pulse_result = run_scheduling_pulse_on_asset(defs, "down", instance=instance)

    assert set(pulse_result.run_requests[0].asset_selection or []) == {down.key, up.key}


def test_on_parent_basic_on_parent_osa_updated() -> None:
    @observable_source_asset
    def parent_osa() -> DataVersion:
        return DataVersion(str(uuid4()))

    @asset(deps=[parent_osa], scheduling_policy=IncludeOnAnyParentOutOfSync())
    def an_asset() -> None:
        ...

    @asset(deps=[an_asset], scheduling_policy=AlwaysLaunchSchedulingPolicy())
    def launchy_asset() -> None:
        ...

    defs = Definitions(assets=[parent_osa, an_asset, launchy_asset])

    instance = DagsterInstance.ephemeral()

    assert observe(assets=[parent_osa], instance=instance).success

    assert materialize(assets=[an_asset, launchy_asset], instance=instance).success

    pulse_result = run_scheduling_pulse_on_asset(defs, "launchy_asset", instance=instance)

    # this should only launch itself
    assert set(pulse_result.run_requests[0].asset_selection or []) == {launchy_asset.key}

    # observe parent_osa and get new data version
    assert observe(assets=[parent_osa], instance=instance).success

    pulse_result = run_scheduling_pulse_on_asset(defs, "launchy_asset", instance=instance)

    assert set(pulse_result.run_requests[0].asset_selection or []) == {
        launchy_asset.key,
        an_asset.key,
    }


def test_on_parent_any_parent_policy_one_parent() -> None:
    @asset
    def up_one() -> None:
        ...

    @asset
    def up_two() -> None:
        ...

    @asset(deps=[up_one, up_two], scheduling_policy=IncludeOnAnyParentOutOfSync())
    def down() -> None:
        ...

    @asset(deps=[down], scheduling_policy=AlwaysLaunchSchedulingPolicy())
    def launchy_asset() -> None:
        ...

    defs = Definitions(assets=[up_one, up_two, down, launchy_asset])
    instance = DagsterInstance.ephemeral()

    assert materialize(assets=[up_one, up_two, down, launchy_asset], instance=instance).success

    pulse_result = run_scheduling_pulse_on_asset(defs, "launchy_asset", instance=instance)
    assert set(pulse_result.run_requests[0].asset_selection or []) == {launchy_asset.key}

    assert materialize(assets=[up_one], instance=instance).success

    pulse_result = run_scheduling_pulse_on_asset(defs, "launchy_asset", instance=instance)
    assert set(pulse_result.run_requests[0].asset_selection or []) == {launchy_asset.key, down.key}


def test_on_parent_all_parent_policy_one_parent() -> None:
    @asset
    def up_one() -> None:
        ...

    @asset
    def up_two() -> None:
        ...

    @asset(deps=[up_one, up_two], scheduling_policy=IncludeOnAllParentsOutOfSync())
    def down() -> None:
        ...

    @asset(deps=[down], scheduling_policy=AlwaysLaunchSchedulingPolicy())
    def launchy_asset() -> None:
        ...

    defs = Definitions(assets=[up_one, up_two, down, launchy_asset])
    instance = DagsterInstance.ephemeral()

    assert materialize(assets=[up_one, up_two, down, launchy_asset], instance=instance).success

    pulse_result = run_scheduling_pulse_on_asset(defs, "launchy_asset", instance=instance)
    assert set(pulse_result.run_requests[0].asset_selection or []) == {launchy_asset.key}

    assert materialize(assets=[up_one], instance=instance).success

    pulse_result = run_scheduling_pulse_on_asset(defs, "launchy_asset", instance=instance)
    assert set(pulse_result.run_requests[0].asset_selection or []) == {launchy_asset.key}


def test_on_parent_all_parent_policy_both_parents() -> None:
    @asset
    def up_one() -> None:
        ...

    @asset
    def up_two() -> None:
        ...

    @asset(deps=[up_one, up_two], scheduling_policy=IncludeOnAllParentsOutOfSync())
    def down() -> None:
        ...

    @asset(deps=[down], scheduling_policy=AlwaysLaunchSchedulingPolicy())
    def launchy_asset() -> None:
        ...

    defs = Definitions(assets=[up_one, up_two, down, launchy_asset])
    instance = DagsterInstance.ephemeral()

    assert materialize(assets=[up_one, up_two, down, launchy_asset], instance=instance).success

    pulse_result = run_scheduling_pulse_on_asset(defs, "launchy_asset", instance=instance)
    assert set(pulse_result.run_requests[0].asset_selection or []) == {launchy_asset.key}

    assert materialize(assets=[up_one, up_two], instance=instance).success

    pulse_result = run_scheduling_pulse_on_asset(defs, "launchy_asset", instance=instance)
    assert set(pulse_result.run_requests[0].asset_selection or []) == {launchy_asset.key, down.key}
