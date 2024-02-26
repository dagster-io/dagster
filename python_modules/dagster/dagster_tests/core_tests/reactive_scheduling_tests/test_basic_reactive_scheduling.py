from datetime import datetime
from typing import Optional, Set

from dagster import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.run_request import RunRequest
from dagster._core.instance import DagsterInstance
from dagster._core.reactive_scheduling.reactive_scheduling_plan import (
    PulseResult,
    pulse_policy_on_asset,
)
from dagster._core.reactive_scheduling.scheduling_policy import (
    AssetPartition,
    RequestReaction,
    SchedulingExecutionContext,
    SchedulingPolicy,
    SchedulingResult,
)


def run_scheduling_pulse_on_asset(
    defs: Definitions,
    asset_key: CoercibleToAssetKey,
    instance: Optional[DagsterInstance] = None,
    evaluation_dt: Optional[datetime] = None,
    previous_dt: Optional[datetime] = None,
) -> PulseResult:
    return pulse_policy_on_asset(
        asset_key=AssetKey.from_coercible(asset_key),
        repository_def=defs.get_repository_def(),
        instance=instance or DagsterInstance.ephemeral(),
        evaluation_dt=evaluation_dt or datetime.now(),
        previous_dt=previous_dt,
    )


class AlwaysLaunchSchedulingPolicy(SchedulingPolicy):
    def schedule(self, context: SchedulingExecutionContext) -> SchedulingResult:
        return SchedulingResult(launch=True)


class AlwaysDeferSchedulingPolicy(SchedulingPolicy):
    def schedule(self, context: SchedulingExecutionContext) -> SchedulingResult:
        return SchedulingResult(launch=False)

    def react_to_downstream_request(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        return RequestReaction(include=True)

    def react_to_upstream_request(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        return RequestReaction(include=True)


def run_request_assets(run_request: RunRequest) -> Set[AssetKey]:
    return set(run_request.asset_selection) if run_request.asset_selection else set()


def asset_key_set(*aks: CoercibleToAssetKey) -> Set[AssetKey]:
    return {AssetKey.from_coercible(ak) for ak in aks}


def test_include_scheduling_policy() -> None:
    assert SchedulingPolicy


def test_scheduling_policy_parameter() -> None:
    scheduling_policy = SchedulingPolicy()

    @asset(scheduling_policy=scheduling_policy)
    def an_asset() -> None:
        raise Exception("never executed")

    assert an_asset.scheduling_policies_by_key[AssetKey(["an_asset"])] is scheduling_policy

    defs = Definitions([an_asset])
    ak = AssetKey(["an_asset"])
    assert defs.get_assets_def(ak).scheduling_policies_by_key[ak] is scheduling_policy


def test_never_launch() -> None:
    @asset()
    def never_launching() -> None:
        ...

    definitions = Definitions(assets=[never_launching])

    assert (
        run_scheduling_pulse_on_asset(defs=definitions, asset_key="never_launching").run_requests
        == []
    )


def test_launch_on_every_tick() -> None:
    @asset(scheduling_policy=AlwaysLaunchSchedulingPolicy())
    def always_launching() -> None:
        ...

    definitions = Definitions(assets=[always_launching])

    assert definitions.get_assets_def("always_launching").scheduling_policies_by_key[
        AssetKey.from_coercible("always_launching")
    ]

    run_requests = run_scheduling_pulse_on_asset(definitions, "always_launching").run_requests
    assert len(run_requests) == 1
    assert run_request_assets(run_requests[0]) == asset_key_set("always_launching")


def test_launch_on_every_tick_with_partitioned_upstream() -> None:
    static_partitions_def = StaticPartitionsDefinition(["1", "2"])

    @asset(partitions_def=static_partitions_def, scheduling_policy=AlwaysDeferSchedulingPolicy())
    def upup() -> None:
        ...

    @asset(
        partitions_def=static_partitions_def,
        deps=[upup],
        scheduling_policy=AlwaysDeferSchedulingPolicy(),
    )
    def up() -> None:
        ...

    @asset(
        partitions_def=static_partitions_def,
        deps=[up],
        scheduling_policy=AlwaysLaunchSchedulingPolicy(),
    )
    def down() -> None:
        ...

    defs = Definitions(assets=[upup, up, down])

    run_requests = run_scheduling_pulse_on_asset(defs, "down").run_requests

    assert len(run_requests) == 2

    assert run_request_assets(run_requests[0]) == asset_key_set("upup", "up", "down")
    assert run_requests[0].partition_key == "1"
    assert run_request_assets(run_requests[1]) == asset_key_set("upup", "up", "down")
    assert run_requests[1].partition_key == "2"
    assert not run_scheduling_pulse_on_asset(defs, "up").run_requests
    assert not run_scheduling_pulse_on_asset(defs, "upup").run_requests


def test_launch_on_every_tick_with_partitioned_downstream() -> None:
    static_partitions_def = StaticPartitionsDefinition(["1", "2"])

    @asset(partitions_def=static_partitions_def, scheduling_policy=AlwaysLaunchSchedulingPolicy())
    def up() -> None:
        ...

    @asset(
        partitions_def=static_partitions_def,
        deps=[up],
        scheduling_policy=AlwaysDeferSchedulingPolicy(),
    )
    def down() -> None:
        ...

    defs = Definitions(assets=[up, down])

    run_requests = run_scheduling_pulse_on_asset(defs, "up").run_requests

    assert len(run_requests) == 2

    assert run_request_assets(run_requests[0]) == asset_key_set("up", "down")
    assert run_requests[0].partition_key == "1"
    assert run_request_assets(run_requests[1]) == asset_key_set("up", "down")
    assert run_requests[1].partition_key == "2"

    assert not run_scheduling_pulse_on_asset(defs, "down").run_requests
