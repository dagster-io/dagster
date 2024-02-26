from typing import Optional, Set
from uuid import uuid4

from dagster import DagsterInstance, Definitions, asset
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.decorators.source_asset_decorator import observable_source_asset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.observe import observe
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.run_request import RunRequest
from dagster._core.reactive_scheduling.reactive_scheduling_plan import (
    PulseResult,
)
from dagster._core.reactive_scheduling.scheduling_policy import (
    AssetPartition,
)
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from .test_policies import (
    AlwaysLaunchSchedulingPolicy,
    IncludeOnAllParentsOutOfSync,
    IncludeOnAnyParentOutOfSync,
    run_scheduling_pulse_on_asset,
)


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


def run_request_with_partition(
    pulse_result: PulseResult, partition_key: str
) -> Optional[RunRequest]:
    for run_request in pulse_result.run_requests:
        if run_request.partition_key == partition_key:
            return run_request
    return None


def asset_selection_of_partition(pulse_result: PulseResult, partition_key: str) -> Set[AssetKey]:
    run_request = run_request_with_partition(pulse_result, partition_key)
    if not run_request:
        return set()
    return set(run_request.asset_selection) if run_request.asset_selection else set()


def test_on_parent_all_parent_policy_both_parents_static_partitioned() -> None:
    static_partitions_def = StaticPartitionsDefinition(["1", "2"])

    @asset(partitions_def=static_partitions_def)
    def up_one() -> None:
        ...

    @asset(partitions_def=static_partitions_def)
    def up_two() -> None:
        ...

    @asset(
        deps=[up_one, up_two],
        scheduling_policy=IncludeOnAllParentsOutOfSync(),
        partitions_def=static_partitions_def,
    )
    def down() -> None:
        ...

    @asset(
        deps=[down],
        scheduling_policy=AlwaysLaunchSchedulingPolicy(),
        partitions_def=static_partitions_def,
    )
    def launchy_asset() -> None:
        ...

    defs = Definitions(assets=[up_one, up_two, down, launchy_asset])
    instance = DagsterInstance.ephemeral()

    # set up both partitions with one materialization
    assert materialize(
        assets=[up_one, up_two, down, launchy_asset], instance=instance, partition_key="1"
    ).success
    assert materialize(
        assets=[up_one, up_two, down, launchy_asset], instance=instance, partition_key="2"
    ).success

    pulse_result = run_scheduling_pulse_on_asset(defs, "launchy_asset", instance=instance)
    assert len(pulse_result.run_requests) == 2

    assert asset_selection_of_partition(pulse_result, "1") == {launchy_asset.key}
    assert asset_selection_of_partition(pulse_result, "2") == {launchy_asset.key}

    assert materialize(assets=[up_one, up_two], instance=instance, partition_key="1").success

    pulse_result = run_scheduling_pulse_on_asset(defs, "launchy_asset", instance=instance)
    assert len(pulse_result.run_requests) == 2

    assert asset_selection_of_partition(pulse_result, "1") == {launchy_asset.key, down.key}
    assert asset_selection_of_partition(pulse_result, "2") == {launchy_asset.key}
