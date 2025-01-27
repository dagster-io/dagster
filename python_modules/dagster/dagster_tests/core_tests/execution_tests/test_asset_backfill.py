import datetime
import logging
from collections.abc import Iterable, Mapping, Sequence
from typing import AbstractSet, NamedTuple, Optional, Union, cast  # noqa: UP035
from unittest.mock import MagicMock, patch

import pytest
from dagster import (
    AssetCheckResult,
    AssetDep,
    AssetIn,
    AssetKey,
    AssetOut,
    AssetsDefinition,
    AssetSpec,
    BackfillPolicy,
    DagsterInstance,
    DagsterRunStatus,
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    LastPartitionMapping,
    MaterializeResult,
    Nothing,
    PartitionKeyRange,
    PartitionsDefinition,
    RunRequest,
    StaticPartitionMapping,
    StaticPartitionsDefinition,
    TimeWindowPartitionMapping,
    WeeklyPartitionsDefinition,
    asset,
    asset_check,
    materialize,
    multi_asset,
)
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, TemporalContext
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.decorators.repository_decorator import repository
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.remote_asset_graph import RemoteWorkspaceAssetGraph
from dagster._core.definitions.selector import (
    PartitionRangeSelector,
    PartitionsByAssetSelector,
    PartitionsSelector,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.asset_backfill import (
    AssetBackfillData,
    AssetBackfillIterationResult,
    AssetBackfillStatus,
    backfill_is_complete,
    execute_asset_backfill_iteration_inner,
    get_canceling_asset_backfill_iteration_data,
)
from dagster._core.storage.dagster_run import RunsFilter
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    BACKFILL_ID_TAG,
    PARTITION_NAME_TAG,
)
from dagster._core.test_utils import (
    environ,
    freeze_time,
    instance_for_test,
    mock_workspace_from_repos,
)
from dagster._serdes import deserialize_value, serialize_value
from dagster._time import create_datetime, get_current_datetime, get_current_timestamp
from dagster._utils import Counter, traced_counter
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from dagster_tests.declarative_automation_tests.legacy_tests.scenarios.asset_graphs import (
    multipartitioned_self_dependency,
    one_asset_self_dependency,
    root_assets_different_partitions_same_downstream,
    two_assets_in_sequence_fan_in_partitions,
    two_assets_in_sequence_fan_out_partitions,
)
from dagster_tests.declarative_automation_tests.legacy_tests.scenarios.partition_scenarios import (
    hourly_to_daily_partitions,
    non_partitioned_after_partitioned,
    one_asset_one_partition,
    one_asset_two_partitions,
    partitioned_after_non_partitioned,
    two_assets_in_sequence_one_partition,
    two_assets_in_sequence_two_partitions,
    two_dynamic_assets,
    unpartitioned_after_dynamic_asset,
)
from dagster_tests.declarative_automation_tests.scenario_utils.base_scenario import do_run


class AssetBackfillScenario(NamedTuple):
    assets_by_repo_name: Mapping[str, Sequence[AssetsDefinition]]
    evaluation_time: datetime.datetime
    # when backfilling "some" partitions, the subset of partitions of root assets in the backfill
    # to target:
    target_root_partition_keys: Optional[Sequence[str]]
    last_storage_id_cursor_offset: Optional[int]


def scenario(
    assets: Union[Mapping[str, Sequence[AssetsDefinition]], Sequence[AssetsDefinition]],
    evaluation_time: Optional[datetime.datetime] = None,
    target_root_partition_keys: Optional[Sequence[str]] = None,
    last_storage_id_cursor_offset: Optional[int] = None,
) -> AssetBackfillScenario:
    if isinstance(assets, list):
        assets_by_repo_name = {"repo": assets}
    else:
        assets_by_repo_name = assets

    return AssetBackfillScenario(
        assets_by_repo_name=cast(Mapping[str, Sequence[AssetsDefinition]], assets_by_repo_name),
        evaluation_time=evaluation_time if evaluation_time else get_current_datetime(),
        target_root_partition_keys=target_root_partition_keys,
        last_storage_id_cursor_offset=last_storage_id_cursor_offset,
    )


scenarios = {
    "one_asset_one_partition": scenario(one_asset_one_partition),
    "one_asset_one_partition_cursor_offset": scenario(
        one_asset_one_partition, last_storage_id_cursor_offset=100
    ),
    "one_asset_two_partitions": scenario(one_asset_two_partitions),
    "two_assets_in_sequence_one_partition": scenario(two_assets_in_sequence_one_partition),
    "two_assets_in_sequence_one_partition_cross_repo": scenario(
        {
            "repo1": [two_assets_in_sequence_one_partition[0]],
            "repo2": [two_assets_in_sequence_one_partition[1]],
        },
    ),
    "two_assets_in_sequence_one_partition_cross_repo_cursor_offset": scenario(
        {
            "repo1": [two_assets_in_sequence_one_partition[0]],
            "repo2": [two_assets_in_sequence_one_partition[1]],
        },
        last_storage_id_cursor_offset=100,
    ),
    "two_assets_in_sequence_two_partitions": scenario(two_assets_in_sequence_two_partitions),
    "two_assets_in_sequence_two_partitions_cursor_offset": scenario(
        two_assets_in_sequence_two_partitions, last_storage_id_cursor_offset=100
    ),
    "two_assets_in_sequence_fan_in_partitions": scenario(two_assets_in_sequence_fan_in_partitions),
    "two_assets_in_sequence_fan_out_partitions": scenario(
        two_assets_in_sequence_fan_out_partitions
    ),
    "one_asset_self_dependency": scenario(
        one_asset_self_dependency, create_datetime(year=2020, month=1, day=7, hour=4)
    ),
    "non_partitioned_after_partitioned": scenario(
        non_partitioned_after_partitioned, create_datetime(year=2020, month=1, day=7, hour=4)
    ),
    "partitioned_after_non_partitioned": scenario(
        partitioned_after_non_partitioned,
        create_datetime(year=2020, month=1, day=7, hour=4),
    ),
    "unpartitioned_after_dynamic_asset": scenario(unpartitioned_after_dynamic_asset),
    "two_dynamic_assets": scenario(two_dynamic_assets),
    "hourly_to_daily_partiitons": scenario(
        hourly_to_daily_partitions,
        create_datetime(year=2013, month=1, day=7, hour=0),
        target_root_partition_keys=[
            "2013-01-05-22:00",
            "2013-01-05-23:00",
            "2013-01-06-00:00",
            "2013-01-06-01:00",
        ],
    ),
    "root_assets_different_partitions": scenario(root_assets_different_partitions_same_downstream),
    "hourly_with_nonexistent_downstream_daily_partition": scenario(
        hourly_to_daily_partitions,
        create_datetime(year=2013, month=1, day=7, hour=10),
        target_root_partition_keys=[
            "2013-01-07-05:00",
        ],
    ),
    "multipartitioned_self_dependency": scenario(
        multipartitioned_self_dependency, create_datetime(year=2020, month=1, day=7, hour=4)
    ),
}


@pytest.mark.parametrize(
    "scenario_name, partition_keys, expected_target_asset_partitions",
    [
        (
            "two_assets_in_sequence_fan_in_partitions",
            ["a_1", "a_2"],
            [("asset1", "a_1"), ("asset1", "a_2"), ("asset2", "a")],
        ),
        (
            "two_assets_in_sequence_fan_out_partitions",
            ["a"],
            [("asset1", "a"), ("asset2", "a_1"), ("asset2", "a_2"), ("asset2", "a_3")],
        ),
        (
            "non_partitioned_after_partitioned",
            ["2022-01-01", "2022-01-02"],
            [("asset1", "2022-01-01"), ("asset1", "2022-01-02"), ("asset2", None)],
        ),
        (
            "partitioned_after_non_partitioned",
            ["2022-01-01", "2022-01-02"],
            [
                ("asset1", None),
                ("asset2", None),
                ("asset3", "2022-01-01"),
                ("asset3", "2022-01-02"),
            ],
        ),
    ],
)
def test_from_asset_partitions_target_subset(
    scenario_name, partition_keys, expected_target_asset_partitions
):
    assets_by_repo_name = scenarios[scenario_name].assets_by_repo_name
    asset_graph = get_asset_graph(assets_by_repo_name)
    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=partition_keys,
        asset_graph=asset_graph,
        asset_selection=list(asset_graph.materializable_asset_keys),
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=scenarios[scenario_name].evaluation_time.timestamp(),
    )
    assert backfill_data.target_subset == AssetGraphSubset.from_asset_partition_set(
        {
            AssetKeyPartitionKey(AssetKey(asset_key_str), partition_key)
            for asset_key_str, partition_key in expected_target_asset_partitions
        },
        asset_graph=asset_graph,
    )


def _get_instance_queryer(
    instance: DagsterInstance, asset_graph: BaseAssetGraph, evaluation_time: datetime.datetime
) -> CachingInstanceQueryer:
    return AssetGraphView(
        temporal_context=TemporalContext(
            effective_dt=evaluation_time or get_current_datetime(), last_event_id=None
        ),
        instance=instance,
        asset_graph=asset_graph,
    ).get_inner_queryer_for_back_compat()


def _single_backfill_iteration(
    backfill_id,
    backfill_data,
    asset_graph: RemoteWorkspaceAssetGraph,
    instance,
    assets_by_repo_name,
) -> AssetBackfillData:
    result = execute_asset_backfill_iteration_consume_generator(
        backfill_id, backfill_data, asset_graph, instance
    )

    backfill_data = result.backfill_data

    for run_request in result.run_requests:
        asset_keys = run_request.asset_selection
        assert asset_keys is not None

        assets = assets_by_repo_name[
            asset_graph.get_repository_handle(asset_keys[0]).repository_name
        ]

        do_run(
            all_assets=assets,
            asset_keys=asset_keys,
            partition_key=run_request.partition_key,
            instance=instance,
            failed_asset_keys=[],
            tags={**run_request.tags, BACKFILL_ID_TAG: backfill_id},
        )

    return backfill_data.with_run_requests_submitted(
        result.run_requests,
        asset_graph,
        instance_queryer=_get_instance_queryer(
            instance, asset_graph, backfill_data.backfill_start_datetime
        ),
    )


def _single_backfill_iteration_create_but_do_not_submit_runs(
    backfill_id, backfill_data, asset_graph, instance, assets_by_repo_name
) -> AssetBackfillData:
    # Patch the run execution to not actually execute the run, but instead just create it
    with patch(
        "dagster._core.execution.execute_in_process.ExecuteRunWithPlanIterable",
        return_value=MagicMock(),
    ):
        return _single_backfill_iteration(
            backfill_id, backfill_data, asset_graph, instance, assets_by_repo_name
        )


@pytest.mark.parametrize("some_or_all", ["all", "some"])
@pytest.mark.parametrize("failures", ["no_failures", "root_failures", "random_half_failures"])
@pytest.mark.parametrize("scenario", list(scenarios.values()), ids=list(scenarios.keys()))
def test_scenario_to_completion(scenario: AssetBackfillScenario, failures: str, some_or_all: str):
    with (
        instance_for_test() as instance,
        environ(
            {"ASSET_BACKFILL_CURSOR_OFFSET": str(scenario.last_storage_id_cursor_offset)}
            if scenario.last_storage_id_cursor_offset
            else {}
        ),
    ):
        instance.add_dynamic_partitions("foo", ["a", "b"])

        with freeze_time(scenario.evaluation_time):
            assets_by_repo_name = scenario.assets_by_repo_name

            asset_graph = get_asset_graph(assets_by_repo_name)
            if some_or_all == "all":
                target_subset = AssetGraphSubset.all(
                    asset_graph,
                    dynamic_partitions_store=instance,
                    current_time=scenario.evaluation_time,
                )
            elif some_or_all == "some":
                if scenario.target_root_partition_keys is None:
                    target_subset = make_random_subset(
                        asset_graph, instance, scenario.evaluation_time
                    )
                else:
                    target_subset = make_subset_from_partition_keys(
                        scenario.target_root_partition_keys,
                        asset_graph,
                        instance,
                        evaluation_time=scenario.evaluation_time,
                    )
            else:
                assert False

            backfill_data = AssetBackfillData.empty(
                target_subset,
                scenario.evaluation_time.timestamp(),
                dynamic_partitions_store=instance,
            )
            if failures == "no_failures":
                fail_asset_partitions: set[AssetKeyPartitionKey] = set()
            elif failures == "root_failures":
                fail_asset_partitions = set(
                    (
                        backfill_data.target_subset.filter_asset_keys(
                            asset_graph.root_materializable_asset_keys
                        )
                    ).iterate_asset_partitions()
                )
            elif failures == "random_half_failures":
                fail_asset_partitions = {
                    asset_partition
                    for asset_partition in backfill_data.target_subset.iterate_asset_partitions()
                    if hash(str(asset_partition.asset_key) + str(asset_partition.partition_key)) % 2
                    == 0
                }

            else:
                assert False

            run_backfill_to_completion(
                asset_graph, assets_by_repo_name, backfill_data, fail_asset_partitions, instance
            )


def test_materializations_outside_of_backfill():
    assets_by_repo_name = {"repo": one_asset_one_partition}
    asset_graph = get_asset_graph(assets_by_repo_name)

    instance = DagsterInstance.ephemeral()

    do_run(
        all_assets=one_asset_one_partition,
        asset_keys=[one_asset_one_partition[0].key],
        partition_key=cast(
            PartitionsDefinition, one_asset_one_partition[0].partitions_def
        ).get_partition_keys()[0],
        instance=instance,
        tags={},
    )

    run_backfill_to_completion(
        instance=instance,
        asset_graph=asset_graph,
        assets_by_repo_name=assets_by_repo_name,
        backfill_data=make_backfill_data("all", asset_graph, instance, None),  # pyright: ignore[reportArgumentType]
        fail_asset_partitions=set(),
    )


def test_do_not_rerequest_while_existing_run_in_progress():
    @asset(
        partitions_def=DailyPartitionsDefinition("2023-01-01"),
    )
    def upstream():
        pass

    @asset(
        partitions_def=DailyPartitionsDefinition("2023-01-01"),
    )
    def downstream(upstream):
        pass

    assets_by_repo_name = {"repo": [upstream, downstream]}
    asset_graph = get_asset_graph(assets_by_repo_name)

    instance = DagsterInstance.ephemeral()

    backfill_id = "dummy_backfill_id"
    asset_backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=["2023-01-01"],
        asset_selection=[downstream.key],
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=create_datetime(2023, 1, 9, 0, 0, 0).timestamp(),
    )

    do_run(
        all_assets=[upstream],
        asset_keys=[upstream.key],
        partition_key="2023-01-01",
        instance=instance,
    )

    asset_backfill_data = _single_backfill_iteration_create_but_do_not_submit_runs(
        backfill_id, asset_backfill_data, asset_graph, instance, assets_by_repo_name
    )

    assert (
        AssetKeyPartitionKey(downstream.key, partition_key="2023-01-01")
        in asset_backfill_data.requested_subset
    )

    # Run for 2023-01-01 exists and is in progress, but has not materialized
    backfill_runs = instance.get_runs(RunsFilter(tags={BACKFILL_ID_TAG: backfill_id}))
    assert len(backfill_runs) == 1
    assert backfill_runs[0].tags.get(PARTITION_NAME_TAG) == "2023-01-01"
    assert backfill_runs[0].status == DagsterRunStatus.NOT_STARTED

    do_run(
        all_assets=[upstream],
        asset_keys=[upstream.key],
        partition_key="2023-01-01",
        instance=instance,
    )

    _single_backfill_iteration_create_but_do_not_submit_runs(
        backfill_id, asset_backfill_data, asset_graph, instance, assets_by_repo_name
    )

    # Confirm that no additional runs for 2023-01-02 are kicked off
    assert len(instance.get_runs(RunsFilter(tags={BACKFILL_ID_TAG: backfill_id}))) == 1


def make_backfill_data(
    some_or_all: str,
    asset_graph: RemoteWorkspaceAssetGraph,
    instance: DagsterInstance,
    current_time: datetime.datetime,
) -> AssetBackfillData:
    if some_or_all == "all":
        target_subset = AssetGraphSubset.all(
            asset_graph,
            dynamic_partitions_store=instance,
            current_time=current_time,
        )
    elif some_or_all == "some":
        target_subset = make_random_subset(asset_graph, instance, current_time)
    else:
        assert False

    return AssetBackfillData.empty(
        target_subset,
        current_time.timestamp() if current_time else get_current_timestamp(),
        dynamic_partitions_store=instance,
    )


def make_random_subset(
    asset_graph: RemoteWorkspaceAssetGraph,
    instance: DagsterInstance,
    evaluation_time: datetime.datetime,
) -> AssetGraphSubset:
    # all partitions downstream of half of the partitions in each partitioned root asset
    root_asset_partitions: set[AssetKeyPartitionKey] = set()
    for i, root_asset_key in enumerate(sorted(asset_graph.root_materializable_asset_keys)):
        partitions_def = asset_graph.get(root_asset_key).partitions_def

        if partitions_def is not None:
            partition_keys = list(
                partitions_def.get_partition_keys(
                    dynamic_partitions_store=instance, current_time=evaluation_time
                )
            )
            start_index = len(partition_keys) // 2
            chosen_partition_keys = partition_keys[start_index:]
            root_asset_partitions.update(
                AssetKeyPartitionKey(root_asset_key, partition_key)
                for partition_key in chosen_partition_keys
            )
        else:
            if i % 2 == 0:
                root_asset_partitions.add(AssetKeyPartitionKey(root_asset_key, None))

    target_asset_partitions, _ = asset_graph.bfs_filter_asset_partitions(
        instance, lambda _a, _b: (True, ""), root_asset_partitions, evaluation_time=evaluation_time
    )

    return AssetGraphSubset.from_asset_partition_set(target_asset_partitions, asset_graph)


def make_subset_from_partition_keys(
    partition_keys: Sequence[str],
    asset_graph: RemoteWorkspaceAssetGraph,
    instance: DagsterInstance,
    evaluation_time: datetime.datetime,
) -> AssetGraphSubset:
    root_asset_partitions: set[AssetKeyPartitionKey] = set()
    for i, root_asset_key in enumerate(sorted(asset_graph.root_materializable_asset_keys)):
        if asset_graph.get(root_asset_key).is_partitioned:
            root_asset_partitions.update(
                AssetKeyPartitionKey(root_asset_key, partition_key)
                for partition_key in partition_keys
            )
        else:
            root_asset_partitions.add(AssetKeyPartitionKey(root_asset_key, None))

    target_asset_partitions, _ = asset_graph.bfs_filter_asset_partitions(
        instance, lambda _a, _b: (True, ""), root_asset_partitions, evaluation_time=evaluation_time
    )

    return AssetGraphSubset.from_asset_partition_set(target_asset_partitions, asset_graph)


def get_asset_graph(
    assets_by_repo_name: Mapping[str, Sequence[AssetsDefinition]],
) -> RemoteWorkspaceAssetGraph:
    assets_defs_by_key = {
        key: assets_def
        for assets in assets_by_repo_name.values()
        for assets_def in assets
        for key in assets_def.keys
    }
    with patch(
        "dagster._core.remote_representation.external_data.get_builtin_partition_mapping_types"
    ) as get_builtin_partition_mapping_types:
        get_builtin_partition_mapping_types.return_value = tuple(
            assets_def.infer_partition_mapping(
                next(iter(assets_def.keys)),
                dep_key,
                assets_defs_by_key[dep_key].specs_by_key[dep_key].partitions_def,
            ).__class__
            for assets in assets_by_repo_name.values()
            for assets_def in assets
            for dep_key in assets_def.dependency_keys
        )
        return remote_asset_graph_from_assets_by_repo_name(assets_by_repo_name)


def execute_asset_backfill_iteration_consume_generator(
    backfill_id: str,
    asset_backfill_data: AssetBackfillData,
    asset_graph: RemoteWorkspaceAssetGraph,
    instance: DagsterInstance,
) -> AssetBackfillIterationResult:
    counter = Counter()
    traced_counter.set(counter)

    with environ({"ASSET_BACKFILL_CURSOR_DELAY_TIME": "0"}):
        for result in execute_asset_backfill_iteration_inner(
            backfill_id=backfill_id,
            asset_backfill_data=asset_backfill_data,
            instance_queryer=_get_instance_queryer(
                instance, asset_graph, asset_backfill_data.backfill_start_datetime
            ),
            asset_graph=asset_graph,
            backfill_start_timestamp=asset_backfill_data.backfill_start_timestamp,
            logger=logging.getLogger("fake_logger"),
        ):
            if isinstance(result, AssetBackfillIterationResult):
                assert counter.counts().get("DagsterInstance.get_dynamic_partitions", 0) <= 1
                return result

    assert False


def run_backfill_to_completion(
    asset_graph: RemoteWorkspaceAssetGraph,
    assets_by_repo_name: Mapping[str, Sequence[AssetsDefinition]],
    backfill_data: AssetBackfillData,
    fail_asset_partitions: Iterable[AssetKeyPartitionKey],
    instance: DagsterInstance,
) -> tuple[AssetBackfillData, AbstractSet[AssetKeyPartitionKey], AbstractSet[AssetKeyPartitionKey]]:
    iteration_count = 0
    instance = instance or DagsterInstance.ephemeral()
    backfill_id = "backfillid_x"

    # assert each asset partition only targeted once
    requested_asset_partitions: set[AssetKeyPartitionKey] = set()

    fail_and_downstream_asset_partitions, _ = asset_graph.bfs_filter_asset_partitions(
        instance,
        lambda _a, _b: (True, ""),
        fail_asset_partitions,
        evaluation_time=backfill_data.backfill_start_datetime,
    )

    while not backfill_is_complete(
        backfill_id=backfill_id,
        backfill_data=backfill_data,
        instance=instance,
        logger=logging.getLogger("fake_logger"),
    ):
        iteration_count += 1

        result1 = execute_asset_backfill_iteration_consume_generator(
            backfill_id=backfill_id,
            asset_backfill_data=backfill_data,
            asset_graph=asset_graph,
            instance=instance,
        )

        assert result1.backfill_data != backfill_data

        instance_queryer = _get_instance_queryer(
            instance, asset_graph, evaluation_time=backfill_data.backfill_start_datetime
        )

        backfill_data_with_submitted_runs = result1.backfill_data.with_run_requests_submitted(
            result1.run_requests,
            asset_graph,
            instance_queryer,
        )

        # once everything that was requested is added to the requested subset, nothing should change if the iteration repeats
        result2 = execute_asset_backfill_iteration_consume_generator(
            backfill_id=backfill_id,
            asset_backfill_data=backfill_data_with_submitted_runs,
            asset_graph=asset_graph,
            instance=instance,
        )
        assert result2.backfill_data == backfill_data_with_submitted_runs
        assert result2.run_requests == []

        backfill_data = result1.backfill_data

        for asset_partition in backfill_data.materialized_subset.iterate_asset_partitions():
            assert asset_partition not in fail_and_downstream_asset_partitions

            parent_partitions_result = asset_graph.get_parents_partitions(
                instance,
                backfill_data.backfill_start_datetime,
                *asset_partition,
            )

            for parent_asset_partition in parent_partitions_result.parent_partitions:
                if (
                    parent_asset_partition in backfill_data.target_subset
                    and parent_asset_partition not in backfill_data.materialized_subset
                ):
                    assert False, (
                        f"{asset_partition} was materialized before its parent"
                        f" {parent_asset_partition},"
                    )

        for run_request in result1.run_requests:
            asset_keys = run_request.asset_selection
            assert asset_keys is not None
            requested_asset_partitions.update(
                _requested_asset_partitions_in_run_request(run_request, asset_graph)
            )

            assert all(
                asset_graph.get_repository_handle(asset_keys[0])
                == asset_graph.get_repository_handle(asset_key)
                for asset_key in asset_keys
            )
            assets = assets_by_repo_name[
                asset_graph.get_repository_handle(asset_keys[0]).repository_name
            ]

            do_run(
                all_assets=assets,
                asset_keys=asset_keys,
                partition_key=run_request.partition_key,
                instance=instance,
                failed_asset_keys=[
                    asset_key
                    for asset_key in asset_keys
                    if AssetKeyPartitionKey(asset_key, run_request.partition_key)
                    in fail_asset_partitions
                ],
                tags={**run_request.tags, BACKFILL_ID_TAG: backfill_id},
            )

        assert iteration_count <= len(requested_asset_partitions) + 1
    return backfill_data, requested_asset_partitions, fail_and_downstream_asset_partitions


def _requested_asset_partitions_in_run_request(
    run_request: RunRequest, asset_graph: BaseAssetGraph
) -> set[AssetKeyPartitionKey]:
    asset_keys = run_request.asset_selection
    assert asset_keys is not None
    requested_asset_partitions = set()
    partition_range_start = run_request.tags.get(ASSET_PARTITION_RANGE_START_TAG)
    partition_range_end = run_request.tags.get(ASSET_PARTITION_RANGE_END_TAG)
    if partition_range_start and partition_range_end and run_request.partition_key is None:
        # backfill was a chunked backfill
        partition_range = PartitionKeyRange(
            start=partition_range_start,
            end=partition_range_end,
        )
        asset_partitions = []
        for asset_key in asset_keys:
            asset_partitions.extend(
                asset_graph.get_partitions_in_range(
                    asset_key=asset_key,
                    partition_key_range=partition_range,
                    dynamic_partitions_store=MagicMock(),
                )
            )
        duplicate_asset_partitions = set(asset_partitions) & requested_asset_partitions
        assert len(duplicate_asset_partitions) == 0, (
            f" {duplicate_asset_partitions} requested twice. Requested:"
            f" {requested_asset_partitions}."
        )
        requested_asset_partitions.update(asset_partitions)
    else:
        # backfill was a partition by partition backfill
        for asset_key in asset_keys:
            asset_partition = AssetKeyPartitionKey(asset_key, run_request.partition_key)
            assert (
                asset_partition not in requested_asset_partitions
            ), f"{asset_partition} requested twice. Requested: {requested_asset_partitions}."
            requested_asset_partitions.add(asset_partition)
    return requested_asset_partitions


def remote_asset_graph_from_assets_by_repo_name(
    assets_by_repo_name: Mapping[str, Sequence[AssetsDefinition]],
) -> RemoteWorkspaceAssetGraph:
    repos = []
    for repo_name, assets in assets_by_repo_name.items():

        @repository(name=repo_name)
        def repo(assets=assets):
            return assets

        repos.append(repo)

    return mock_workspace_from_repos(repos).asset_graph


@pytest.mark.parametrize(
    "static_serialization",
    [
        (
            r'{"requested_runs_for_target_roots": false, "serialized_target_subset":'
            r' {"partitions_subsets_by_asset_key": {"static_asset": "{\"version\": 1, \"subset\":'
            r' [\"b\", \"d\", \"c\", \"a\", \"e\", \"f\"]}"}, "non_partitioned_asset_keys": []},'
            r' "latest_storage_id": null, "serialized_requested_subset":'
            r' {"partitions_subsets_by_asset_key": {}, "non_partitioned_asset_keys": []},'
            r' "serialized_materialized_subset": {"partitions_subsets_by_asset_key": {},'
            r' "non_partitioned_asset_keys": []}, "serialized_failed_subset":'
            r' {"partitions_subsets_by_asset_key": {}, "non_partitioned_asset_keys": []}}'
        ),
        (
            r'{"requested_runs_for_target_roots": false, "serialized_target_subset":'
            r' {"partitions_subsets_by_asset_key": {"static_asset": "{\"version\": 1, \"subset\":'
            r' [\"f\", \"b\", \"e\", \"c\", \"d\", \"a\"]}"},'
            r' "serializable_partitions_ids_by_asset_key": {"static_asset":'
            r' "7c2047f8b02e90a69136c1a657bd99ad80b433a2"}, "subset_types_by_asset_key":'
            r' {"static_asset": "DEFAULT"}, "non_partitioned_asset_keys": []}, "latest_storage_id":'
            r' null, "serialized_requested_subset": {"partitions_subsets_by_asset_key": {},'
            r' "serializable_partitions_ids_by_asset_key": {}, "subset_types_by_asset_key": {},'
            r' "non_partitioned_asset_keys": []}, "serialized_materialized_subset":'
            r' {"partitions_subsets_by_asset_key": {},'
            r' "serializable_partitions_ids_by_asset_key": {},'
            r' "subset_types_by_asset_key": {}, "non_partitioned_asset_keys": []},'
            r' "serialized_failed_subset": {"partitions_subsets_by_asset_key": {},'
            r' "serializable_partitions_ids_by_asset_key": {}, "subset_types_by_asset_key": {},'
            r' "non_partitioned_asset_keys": []}}'
        ),
    ],
)
@pytest.mark.parametrize(
    "time_window_serialization",
    [
        (
            r'{"requested_runs_for_target_roots": false, "serialized_target_subset":'
            r' {"partitions_subsets_by_asset_key": {"daily_asset": "{\"version\": 1,'
            r" \"time_windows\":"
            r' [[1659484800.0, 1659744000.0]], \"num_partitions\": 3}"},'
            r' "non_partitioned_asset_keys":'
            r' []}, "latest_storage_id": null, "serialized_requested_subset":'
            r' {"partitions_subsets_by_asset_key": {}, "non_partitioned_asset_keys": []},'
            r' "serialized_materialized_subset": {"partitions_subsets_by_asset_key": {},'
            r' "non_partitioned_asset_keys": []}, "serialized_failed_subset":'
            r' {"partitions_subsets_by_asset_key": {}, "non_partitioned_asset_keys": []}}'
        ),
        (
            r'{"requested_runs_for_target_roots": true, "serialized_target_subset":'
            r' {"partitions_subsets_by_asset_key": {"daily_asset": "{\"version\": 1,'
            r' \"time_windows\": [[1571356800.0, 1571529600.0]], \"num_partitions\": 2}"},'
            r' "serializable_partitions_def_ids_by_asset_key": {"daily_asset":'
            r' "1d3558e8825a28611c33c1cfe60984c0c5dcf147"},'
            r' "partitions_def_class_names_by_asset_key": {"daily_asset":'
            r' "TimeWindowPartitionsDefinition"}, "non_partitioned_asset_keys": []},'
            r' "latest_storage_id": 235, "serialized_requested_subset":'
            r' {"partitions_subsets_by_asset_key": {"daily_asset": "{\"version\": 1,'
            r' \"time_windows\": [[1571356800.0, 1571529600.0]], \"num_partitions\": 2}"},'
            r' "serializable_partitions_def_ids_by_asset_key": {"daily_asset":'
            r' "1d3558e8825a28611c33c1cfe60984c0c5dcf147"},'
            r' "partitions_def_class_names_by_asset_key": {"daily_asset":'
            r' "TimeWindowPartitionsDefinition"}, "non_partitioned_asset_keys": []},'
            r' "serialized_materialized_subset": {"partitions_subsets_by_asset_key": {},'
            r' "serializable_partitions_def_ids_by_asset_key": {},'
            r' "partitions_def_class_names_by_asset_key": {}, "non_partitioned_asset_keys": []},'
            r' "serialized_failed_subset": {"partitions_subsets_by_asset_key": {},'
            r' "serializable_partitions_def_ids_by_asset_key": {},'
            r' "partitions_def_class_names_by_asset_key": {}, "non_partitioned_asset_keys": []}}'
        ),
    ],
)
def test_serialization(static_serialization, time_window_serialization):
    time_window_partitions = DailyPartitionsDefinition(start_date="2015-05-05")
    keys = ["a", "b", "c", "d", "e", "f"]
    static_partitions = StaticPartitionsDefinition(keys)

    def make_asset_graph1():
        @asset(partitions_def=time_window_partitions)
        def daily_asset(): ...

        @asset(partitions_def=static_partitions)
        def static_asset(): ...

        return remote_asset_graph_from_assets_by_repo_name({"repo": [daily_asset, static_asset]})

    asset_graph1 = make_asset_graph1()
    assert AssetBackfillData.is_valid_serialization(time_window_serialization, asset_graph1) is True
    assert AssetBackfillData.is_valid_serialization(static_serialization, asset_graph1) is True

    def make_asset_graph2():
        @asset(partitions_def=static_partitions)
        def daily_asset(): ...

        @asset(partitions_def=time_window_partitions)
        def static_asset(): ...

        return remote_asset_graph_from_assets_by_repo_name({"repo": [daily_asset, static_asset]})

    asset_graph2 = make_asset_graph2()
    assert (
        AssetBackfillData.is_valid_serialization(time_window_serialization, asset_graph2) is False
    )
    assert AssetBackfillData.is_valid_serialization(static_serialization, asset_graph2) is False

    def make_asset_graph3():
        @asset(partitions_def=StaticPartitionsDefinition(keys + ["x"]))
        def daily_asset(): ...

        @asset(partitions_def=static_partitions)
        def static_asset(): ...

        return remote_asset_graph_from_assets_by_repo_name({"repo": [daily_asset, static_asset]})

    asset_graph3 = make_asset_graph3()

    assert AssetBackfillData.is_valid_serialization(static_serialization, asset_graph3) is True

    def make_asset_graph4():
        @asset(partitions_def=static_partitions)
        def daily_asset_renamed():
            return 1

        @asset(partitions_def=time_window_partitions)
        def static_asset(): ...

        return remote_asset_graph_from_assets_by_repo_name(
            {"repo": [daily_asset_renamed, static_asset]}
        )

    asset_graph4 = make_asset_graph4()

    assert (
        AssetBackfillData.is_valid_serialization(time_window_serialization, asset_graph4) is False
    )


def test_asset_backfill_status_counts():
    @asset
    def unpartitioned_upstream_of_partitioned():
        return 1

    @asset(partitions_def=DailyPartitionsDefinition("2023-01-01"))
    def upstream_daily_partitioned_asset(unpartitioned_upstream_of_partitioned):
        return unpartitioned_upstream_of_partitioned

    @asset(partitions_def=WeeklyPartitionsDefinition("2023-01-01"))
    def downstream_weekly_partitioned_asset(
        upstream_daily_partitioned_asset,
    ):
        return upstream_daily_partitioned_asset + 1

    assets_by_repo_name = {
        "repo": [
            unpartitioned_upstream_of_partitioned,
            upstream_daily_partitioned_asset,
            downstream_weekly_partitioned_asset,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)
    instance = DagsterInstance.ephemeral()

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=["2023-01-09"],
        asset_graph=asset_graph,
        asset_selection=[
            unpartitioned_upstream_of_partitioned.key,
            upstream_daily_partitioned_asset.key,
            downstream_weekly_partitioned_asset.key,
        ],
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=get_current_timestamp(),
    )

    (
        completed_backfill_data,
        requested_asset_partitions,
        fail_and_downstream_asset_partitions,
    ) = run_backfill_to_completion(
        instance=instance,
        asset_graph=asset_graph,
        assets_by_repo_name=assets_by_repo_name,
        backfill_data=backfill_data,
        fail_asset_partitions=[
            AssetKeyPartitionKey(
                asset_key=upstream_daily_partitioned_asset.key, partition_key="2023-01-09"
            )
        ],
    )

    counts = completed_backfill_data.get_backfill_status_per_asset_key(asset_graph)

    assert counts[0].asset_key == unpartitioned_upstream_of_partitioned.key
    assert counts[0].backfill_status == AssetBackfillStatus.MATERIALIZED  # pyright: ignore[reportAttributeAccessIssue]

    assert counts[1].asset_key == upstream_daily_partitioned_asset.key
    assert counts[1].partitions_counts_by_status[AssetBackfillStatus.MATERIALIZED] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[1].partitions_counts_by_status[AssetBackfillStatus.FAILED] == 1  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[1].partitions_counts_by_status[AssetBackfillStatus.IN_PROGRESS] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[1].num_targeted_partitions == 1  # pyright: ignore[reportAttributeAccessIssue]

    assert counts[2].asset_key == downstream_weekly_partitioned_asset.key
    assert counts[2].partitions_counts_by_status[AssetBackfillStatus.MATERIALIZED] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[2].partitions_counts_by_status[AssetBackfillStatus.FAILED] == 1  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[2].partitions_counts_by_status[AssetBackfillStatus.IN_PROGRESS] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[2].num_targeted_partitions == 1  # pyright: ignore[reportAttributeAccessIssue]


def test_asset_backfill_status_counts_with_reexecution():
    @asset(partitions_def=DailyPartitionsDefinition("2023-01-01"), key="upstream")
    def upstream_fail():
        raise Exception("noo")

    @asset(partitions_def=DailyPartitionsDefinition("2023-01-01"), key="upstream")
    def upstream_success():
        pass

    assets_by_repo_name = {
        "repo": [
            upstream_fail,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)
    instance = DagsterInstance.ephemeral()

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=["2023-01-01"],
        asset_graph=asset_graph,
        asset_selection=[
            upstream_fail.key,
        ],
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=get_current_timestamp(),
    )

    backfill_data = _single_backfill_iteration(
        "fake_id", backfill_data, asset_graph, instance, assets_by_repo_name
    )
    backfill_data = _single_backfill_iteration(
        "fake_id", backfill_data, asset_graph, instance, assets_by_repo_name
    )

    counts = backfill_data.get_backfill_status_per_asset_key(asset_graph)
    assert counts[0].asset_key == upstream_fail.key
    assert counts[0].partitions_counts_by_status[AssetBackfillStatus.MATERIALIZED] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[0].partitions_counts_by_status[AssetBackfillStatus.FAILED] == 1  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[0].partitions_counts_by_status[AssetBackfillStatus.IN_PROGRESS] == 0  # pyright: ignore[reportAttributeAccessIssue]

    materialize(
        [upstream_success],
        instance=instance,
        partition_key="2023-01-01",
        tags={BACKFILL_ID_TAG: "fake_id"},
    )

    backfill_data = _single_backfill_iteration(
        "fake_id", backfill_data, asset_graph, instance, assets_by_repo_name
    )
    counts = backfill_data.get_backfill_status_per_asset_key(asset_graph)
    assert counts[0].asset_key == upstream_fail.key
    assert counts[0].partitions_counts_by_status[AssetBackfillStatus.MATERIALIZED] == 1  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[0].partitions_counts_by_status[AssetBackfillStatus.FAILED] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[0].partitions_counts_by_status[AssetBackfillStatus.IN_PROGRESS] == 0  # pyright: ignore[reportAttributeAccessIssue]


def test_asset_backfill_selects_only_existent_partitions():
    @asset(partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00"))
    def upstream_hourly_partitioned_asset():
        return 1

    @asset(partitions_def=DailyPartitionsDefinition("2023-01-01"))
    def downstream_daily_partitioned_asset(
        upstream_hourly_partitioned_asset,
    ):
        return upstream_hourly_partitioned_asset + 1

    assets_by_repo_name = {
        "repo": [
            upstream_hourly_partitioned_asset,
            downstream_daily_partitioned_asset,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=["2023-01-09-00:00"],
        asset_graph=asset_graph,
        asset_selection=[
            upstream_hourly_partitioned_asset.key,
            downstream_daily_partitioned_asset.key,
        ],
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=create_datetime(2023, 1, 9, 0, 0, 0).timestamp(),
    )

    target_subset = backfill_data.target_subset
    assert target_subset.get_partitions_subset(
        upstream_hourly_partitioned_asset.key, asset_graph
    ).get_partition_keys() == ["2023-01-09-00:00"]
    assert (
        len(
            target_subset.get_partitions_subset(downstream_daily_partitioned_asset.key, asset_graph)
        )
        == 0
    )


def test_asset_backfill_throw_error_on_invalid_upstreams():
    @asset(partitions_def=DailyPartitionsDefinition("2023-06-01"))
    def june_asset():
        return 1

    @asset(partitions_def=DailyPartitionsDefinition("2023-05-01"))
    def may_asset(
        june_asset,
    ):
        return june_asset + 1

    assets_by_repo_name = {
        "repo": [
            june_asset,
            may_asset,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=["2023-05-10"],
        asset_graph=asset_graph,
        asset_selection=[
            may_asset.key,
        ],
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=create_datetime(2023, 5, 15, 0, 0, 0).timestamp(),
    )

    instance = DagsterInstance.ephemeral()
    with pytest.raises(DagsterInvariantViolationError, match="depends on invalid partition keys"):
        run_backfill_to_completion(asset_graph, assets_by_repo_name, backfill_data, [], instance)


def test_asset_backfill_cancellation():
    instance = DagsterInstance.ephemeral()

    @asset(partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00"))
    def upstream_hourly_partitioned_asset():
        return 1

    @asset(partitions_def=DailyPartitionsDefinition("2023-01-01"))
    def downstream_daily_partitioned_asset(
        upstream_hourly_partitioned_asset,
    ):
        return upstream_hourly_partitioned_asset + 1

    assets_by_repo_name = {
        "repo": [
            upstream_hourly_partitioned_asset,
            downstream_daily_partitioned_asset,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)

    backfill_id = "dummy_backfill_id"
    backfill_start_datetime = create_datetime(2023, 1, 9, 0, 0, 0)
    asset_selection = [
        upstream_hourly_partitioned_asset.key,
        downstream_daily_partitioned_asset.key,
    ]
    targeted_partitions = ["2023-01-09-00:00"]

    asset_backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=targeted_partitions,
        asset_selection=asset_selection,
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=backfill_start_datetime.timestamp(),
    )

    _single_backfill_iteration(
        backfill_id, asset_backfill_data, asset_graph, instance, assets_by_repo_name
    )

    assert len(instance.get_runs()) == 1

    instance_queryer = _get_instance_queryer(instance, asset_graph, backfill_start_datetime)

    canceling_backfill_data = None
    for canceling_backfill_data in get_canceling_asset_backfill_iteration_data(
        backfill_id,
        asset_backfill_data,
        instance_queryer,
        asset_graph,
        backfill_start_datetime.timestamp(),
    ):
        pass

    assert isinstance(canceling_backfill_data, AssetBackfillData)

    assert (
        canceling_backfill_data.all_requested_partitions_marked_as_materialized_or_failed() is True
    )
    assert (
        canceling_backfill_data.materialized_subset.get_partitions_subset(
            upstream_hourly_partitioned_asset.key, asset_graph
        ).get_partition_keys()
        == targeted_partitions
    )
    assert (
        canceling_backfill_data.materialized_subset.get_partitions_subset(
            downstream_daily_partitioned_asset.key, asset_graph
        ).get_partition_keys()
        == []
    )


def test_asset_backfill_cancels_without_fetching_downstreams_of_failed_partitions():
    instance = DagsterInstance.ephemeral()

    @asset(partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00"))
    def upstream_hourly_partitioned_asset():
        raise Exception("noo")

    @asset(partitions_def=DailyPartitionsDefinition("2023-01-01"))
    def downstream_daily_partitioned_asset(
        upstream_hourly_partitioned_asset,
    ):
        return upstream_hourly_partitioned_asset + 1

    assets_by_repo_name = {
        "repo": [
            upstream_hourly_partitioned_asset,
            downstream_daily_partitioned_asset,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)

    backfill_id = "dummy_backfill_id"
    backfill_start_datetime = create_datetime(2023, 1, 10, 0, 0, 0)
    asset_selection = [
        upstream_hourly_partitioned_asset.key,
        downstream_daily_partitioned_asset.key,
    ]
    targeted_partitions = ["2023-01-09-00:00"]

    asset_backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=targeted_partitions,
        asset_selection=asset_selection,
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=backfill_start_datetime.timestamp(),
    )

    for _ in range(2):
        # One iteration to submit a run targeting the partition
        # Second iteration to update the asset backfill data
        asset_backfill_data = _single_backfill_iteration(
            backfill_id, asset_backfill_data, asset_graph, instance, assets_by_repo_name
        )

    assert (
        AssetKeyPartitionKey(upstream_hourly_partitioned_asset.key, "2023-01-09-00:00")
        in asset_backfill_data.failed_and_downstream_subset
    )
    assert (
        AssetKeyPartitionKey(downstream_daily_partitioned_asset.key, "2023-01-09")
        in asset_backfill_data.failed_and_downstream_subset
    )

    instance_queryer = _get_instance_queryer(instance, asset_graph, backfill_start_datetime)

    canceling_backfill_data = None
    for canceling_backfill_data in get_canceling_asset_backfill_iteration_data(
        backfill_id,
        asset_backfill_data,
        instance_queryer,
        asset_graph,
        backfill_start_datetime.timestamp(),
    ):
        pass

    assert isinstance(canceling_backfill_data, AssetBackfillData)
    assert (
        AssetKeyPartitionKey(upstream_hourly_partitioned_asset.key, "2023-01-09-00:00")
        in canceling_backfill_data.failed_and_downstream_subset
    )
    assert (
        AssetKeyPartitionKey(downstream_daily_partitioned_asset.key, "2023-01-09")
        in canceling_backfill_data.failed_and_downstream_subset
    )


def test_asset_backfill_target_asset_and_same_partitioning_grandchild():
    instance = DagsterInstance.ephemeral()

    @asset(partitions_def=DailyPartitionsDefinition("2023-10-01"))
    def foo():
        pass

    @asset(partitions_def=DailyPartitionsDefinition("2023-10-01"), deps=[foo])
    def foo_child():
        pass

    @asset(partitions_def=DailyPartitionsDefinition("2023-10-01"), deps=[foo_child])
    def foo_grandchild():
        pass

    assets_by_repo_name = {
        "repo": [
            foo,
            foo_child,
            foo_grandchild,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)

    asset_selection = [
        foo.key,
        foo_grandchild.key,
    ]
    all_partitions = [f"2023-10-0{x}" for x in range(1, 5)]

    asset_backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=None,
        asset_selection=asset_selection,
        dynamic_partitions_store=MagicMock(),
        all_partitions=True,
        backfill_start_timestamp=create_datetime(2023, 10, 5, 0, 0, 0).timestamp(),
    )
    assert set(asset_backfill_data.target_subset.iterate_asset_partitions()) == {
        AssetKeyPartitionKey(asset_key, partition_key)
        for asset_key in [foo.key, foo_grandchild.key]
        for partition_key in all_partitions
    }

    asset_backfill_data = _single_backfill_iteration(
        "fake_id", asset_backfill_data, asset_graph, instance, assets_by_repo_name
    )
    assert asset_backfill_data.requested_subset == asset_backfill_data.target_subset


def test_asset_backfill_target_asset_and_differently_partitioned_grandchild():
    instance = DagsterInstance.ephemeral()

    @asset(partitions_def=DailyPartitionsDefinition("2023-10-01"))
    def foo():
        pass

    @asset(partitions_def=DailyPartitionsDefinition("2023-10-01"), deps={foo})
    def foo_child():
        pass

    @asset(partitions_def=WeeklyPartitionsDefinition("2023-10-01"), deps={foo_child})
    def foo_grandchild():
        pass

    assets_by_repo_name = {
        "repo": [
            foo,
            foo_child,
            foo_grandchild,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)

    asset_selection = [
        foo.key,
        foo_grandchild.key,
    ]

    asset_backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=None,
        asset_selection=asset_selection,
        dynamic_partitions_store=MagicMock(),
        all_partitions=True,
        backfill_start_timestamp=create_datetime(2023, 10, 8, 0, 0, 0).timestamp(),
    )

    expected_targeted_partitions = {
        AssetKeyPartitionKey(foo_grandchild.key, "2023-10-01"),
        *{
            AssetKeyPartitionKey(asset_key, partition_key)
            for asset_key in [foo.key]
            for partition_key in [f"2023-10-0{x}" for x in range(1, 8)]
        },
    }

    assert (
        set(asset_backfill_data.target_subset.iterate_asset_partitions())
        == expected_targeted_partitions
    )

    asset_backfill_data = _single_backfill_iteration(
        "fake_id", asset_backfill_data, asset_graph, instance, assets_by_repo_name
    )
    assert asset_backfill_data.requested_subset == asset_backfill_data.target_subset


def test_asset_backfill_nonexistent_parent_partitions():
    instance = DagsterInstance.ephemeral()

    @asset(partitions_def=DailyPartitionsDefinition("2023-10-05"))
    def foo():
        pass

    @asset(
        partitions_def=DailyPartitionsDefinition("2023-10-01"),
        ins={
            "foo": AssetIn(
                key=foo.key,
                partition_mapping=TimeWindowPartitionMapping(
                    allow_nonexistent_upstream_partitions=True
                ),
                dagster_type=Nothing,
            )
        },
    )
    def foo_child():
        pass

    assets_by_repo_name = {
        "repo": [
            foo,
            foo_child,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)

    asset_backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=None,
        asset_selection=[foo.key, foo_child.key],
        dynamic_partitions_store=MagicMock(),
        all_partitions=True,
        backfill_start_timestamp=create_datetime(2023, 10, 8, 0, 0, 0).timestamp(),
    )

    backfill_data, _, _ = run_backfill_to_completion(
        asset_graph, assets_by_repo_name, asset_backfill_data, [], instance
    )

    assert set(backfill_data.target_subset.get_partitions_subset(foo.key).get_partition_keys()) == {
        "2023-10-05",
        "2023-10-06",
        "2023-10-07",
    }
    assert set(
        backfill_data.target_subset.get_partitions_subset(foo_child.key).get_partition_keys()
    ) == {
        "2023-10-01",
        "2023-10-02",
        "2023-10-03",
        "2023-10-04",
        "2023-10-05",
        "2023-10-06",
        "2023-10-07",
    }
    assert backfill_data.target_subset == backfill_data.materialized_subset


def test_connected_assets_disconnected_partitions():
    instance = DagsterInstance.ephemeral()

    @asset(partitions_def=DailyPartitionsDefinition("2023-10-01"))
    def foo():
        pass

    @asset(partitions_def=DailyPartitionsDefinition("2023-10-01"))
    def foo_child(foo):
        pass

    @asset(partitions_def=DailyPartitionsDefinition("2023-10-01"))
    def foo_grandchild(foo_child):
        pass

    assets_by_repo_name = {"repo": [foo, foo_child, foo_grandchild]}
    asset_graph = get_asset_graph(assets_by_repo_name)

    backfill_start_datetime = create_datetime(2023, 10, 30, 0, 0, 0)
    instance_queryer = _get_instance_queryer(instance, asset_graph, backfill_start_datetime)
    asset_backfill_data = AssetBackfillData.from_partitions_by_assets(
        asset_graph,
        instance_queryer,
        backfill_start_datetime.timestamp(),
        [
            PartitionsByAssetSelector(
                asset_key=foo.key,
                partitions=PartitionsSelector([PartitionRangeSelector("2023-10-01", "2023-10-05")]),
            ),
            PartitionsByAssetSelector(
                asset_key=foo_child.key,
                partitions=PartitionsSelector([PartitionRangeSelector("2023-10-01", "2023-10-03")]),
            ),
            PartitionsByAssetSelector(
                asset_key=foo_grandchild.key,
                partitions=PartitionsSelector([PartitionRangeSelector("2023-10-10", "2023-10-13")]),
            ),
        ],
    )

    target_root_partitions = asset_backfill_data.get_target_root_asset_partitions(instance_queryer)
    assert set(target_root_partitions) == {
        AssetKeyPartitionKey(asset_key=AssetKey(["foo"]), partition_key="2023-10-05"),
        AssetKeyPartitionKey(asset_key=AssetKey(["foo"]), partition_key="2023-10-03"),
        AssetKeyPartitionKey(asset_key=AssetKey(["foo"]), partition_key="2023-10-04"),
        AssetKeyPartitionKey(asset_key=AssetKey(["foo"]), partition_key="2023-10-02"),
        AssetKeyPartitionKey(asset_key=AssetKey(["foo"]), partition_key="2023-10-01"),
        AssetKeyPartitionKey(asset_key=AssetKey(["foo_grandchild"]), partition_key="2023-10-11"),
        AssetKeyPartitionKey(asset_key=AssetKey(["foo_grandchild"]), partition_key="2023-10-13"),
        AssetKeyPartitionKey(asset_key=AssetKey(["foo_grandchild"]), partition_key="2023-10-12"),
        AssetKeyPartitionKey(asset_key=AssetKey(["foo_grandchild"]), partition_key="2023-10-10"),
    }


def test_partition_outside_backfill_materialized():
    """Tests the case where the PartitionsDefinition has a new partition since the backfill started,
    and that partitions is materialized outside of the backfill.
    """
    instance = DagsterInstance.ephemeral()

    @asset(partitions_def=DailyPartitionsDefinition("2023-10-01"))
    def foo():
        pass

    @asset(partitions_def=DailyPartitionsDefinition("2023-10-01"), deps={foo})
    def foo_child():
        pass

    assets_by_repo_name = {"repo1": [foo], "repo2": [foo_child]}
    asset_graph = get_asset_graph(assets_by_repo_name)

    asset_backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=["2023-10-01", "2023-10-02"],
        asset_selection=[foo.key, foo_child.key],
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=create_datetime(2023, 10, 3, 0, 0, 0).timestamp(),
    )

    backfill_data, _, _ = run_backfill_to_completion(
        asset_graph, assets_by_repo_name, asset_backfill_data, [], instance
    )

    _single_backfill_iteration(
        backfill_id="apple",
        backfill_data=backfill_data,
        asset_graph=asset_graph,
        instance=instance,
        assets_by_repo_name=assets_by_repo_name,
    )

    materialize(assets=[foo], partition_key="2023-10-03", instance=instance)

    result_backfill_data = _single_backfill_iteration(
        backfill_id="apple",
        backfill_data=backfill_data,
        asset_graph=asset_graph,
        instance=instance,
        assets_by_repo_name=assets_by_repo_name,
    )

    materialized_subset = result_backfill_data.materialized_subset
    assert result_backfill_data.target_subset == materialized_subset
    assert (
        "2023-10-03" not in materialized_subset.get_partitions_subset(foo.key).get_partition_keys()
    )
    assert (
        "2023-10-03"
        not in materialized_subset.get_partitions_subset(foo_child.key).get_partition_keys()
    )


def test_asset_backfill_unpartitioned_downstream_of_partitioned():
    instance = DagsterInstance.ephemeral()

    foo_partitions_def = DailyPartitionsDefinition("2023-10-01")

    @asset(partitions_def=foo_partitions_def)
    def foo():
        pass

    @asset(
        partitions_def=foo_partitions_def,
        ins={
            "foo": AssetIn(
                key=foo.key, partition_mapping=LastPartitionMapping(), dagster_type=Nothing
            )
        },
    )
    def foo_child():
        pass

    assets_by_repo_name = {"repo": [foo, foo_child]}
    asset_graph = get_asset_graph(assets_by_repo_name)
    partition_key_range = PartitionKeyRange(start="2023-10-01", end="2023-10-07")

    asset_backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=foo_partitions_def.get_partition_keys_in_range(partition_key_range),
        asset_selection=[foo.key, foo_child.key],
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=create_datetime(2023, 10, 8, 0, 0, 0).timestamp(),
    )

    assert asset_backfill_data.target_subset.partitions_subsets_by_asset_key == {
        foo.key: foo_partitions_def.empty_subset().with_partition_key_range(
            foo_partitions_def, partition_key_range
        ),
        foo_child.key: foo_partitions_def.empty_subset().with_partition_key_range(
            foo_partitions_def, partition_key_range
        ),
    }

    run_backfill_to_completion(asset_graph, assets_by_repo_name, asset_backfill_data, [], instance)


def test_asset_backfill_serialization_deserialization():
    @asset(
        partitions_def=DailyPartitionsDefinition("2023-01-01"),
    )
    def upstream():
        pass

    @asset
    def middle():
        pass

    @asset(
        partitions_def=DailyPartitionsDefinition("2023-01-01"),
    )
    def downstream(upstream):
        pass

    assets_by_repo_name = {"repo": [upstream, downstream, middle]}
    asset_graph = get_asset_graph(assets_by_repo_name)

    asset_backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=["2023-01-01", "2023-01-02", "2023-01-05"],
        asset_selection=[upstream.key, middle.key, downstream.key],
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=create_datetime(2023, 1, 9, 0, 0, 0).timestamp(),
    )

    assert (
        deserialize_value(serialize_value(asset_backfill_data), AssetBackfillData)
        == asset_backfill_data
    )


def test_asset_backfill_unpartitioned_root_turned_to_partitioned():
    @asset
    def first():
        return 1

    @asset(
        partitions_def=DailyPartitionsDefinition("2024-01-01"),
        ins={"first": AssetIn(key=AssetKey("first"))},
    )
    def second(first):
        return 1

    @asset(key=AssetKey("first"), partitions_def=DailyPartitionsDefinition("2024-01-01"))
    def first_partitioned():
        return 1

    repo_with_unpartitioned_root = {"repo": [first, second]}
    asset_backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=get_asset_graph(repo_with_unpartitioned_root),
        partition_names=["2024-01-01"],
        asset_selection=[first.key, second.key],
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=create_datetime(2024, 1, 9, 0, 0, 0).timestamp(),
    )

    repo_with_partitioned_root = {"repo": [first_partitioned, second]}
    assert asset_backfill_data.get_target_root_partitions_subset(
        get_asset_graph(repo_with_partitioned_root)
    ).get_partition_keys() == ["2024-01-01"]  # pyright: ignore[reportOptionalMemberAccess]


def test_multi_asset_internal_deps_asset_backfill():
    @multi_asset(
        outs={"a": AssetOut(key="a"), "b": AssetOut(key="b"), "c": AssetOut(key="c")},
        internal_asset_deps={"c": {AssetKey("a")}, "b": {AssetKey("a")}, "a": set()},
        partitions_def=StaticPartitionsDefinition(["1", "2", "3"]),
    )
    def my_multi_asset():
        pass

    instance = DagsterInstance.ephemeral()
    repo_with_unpartitioned_root = {"repo": [my_multi_asset]}
    asset_graph = get_asset_graph(repo_with_unpartitioned_root)
    asset_backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=["1"],
        asset_selection=[AssetKey("a"), AssetKey("b"), AssetKey("c")],
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=create_datetime(2024, 1, 9, 0, 0, 0).timestamp(),
    )
    backfill_data = _single_backfill_iteration(
        "fake_id", asset_backfill_data, asset_graph, instance, repo_with_unpartitioned_root
    )
    assert AssetKeyPartitionKey(AssetKey("a"), "1") in backfill_data.requested_subset
    assert AssetKeyPartitionKey(AssetKey("b"), "1") in backfill_data.requested_subset
    assert AssetKeyPartitionKey(AssetKey("c"), "1") in backfill_data.requested_subset


def test_multi_asset_internal_deps_different_partitions_asset_backfill() -> None:
    @multi_asset(
        specs=[
            AssetSpec(
                "asset1", partitions_def=StaticPartitionsDefinition(["a", "b"]), skippable=True
            ),
            AssetSpec(
                "asset2",
                partitions_def=StaticPartitionsDefinition(["1"]),
                deps=[
                    AssetDep(
                        "asset1",
                        partition_mapping=StaticPartitionMapping({"a": {"1"}, "b": {"1"}}),
                    )
                ],
                skippable=True,
            ),
        ],
        can_subset=True,
    )
    def my_multi_asset(context):
        for asset_key in context.selected_asset_keys:
            yield MaterializeResult(asset_key=asset_key)

    instance = DagsterInstance.ephemeral()
    repo_dict = {"repo": [my_multi_asset]}
    asset_graph = get_asset_graph(repo_dict)
    current_time = create_datetime(2024, 1, 9, 0, 0, 0)
    asset_backfill_data = AssetBackfillData.from_asset_graph_subset(
        asset_graph_subset=AssetGraphSubset.all(
            asset_graph, dynamic_partitions_store=MagicMock(), current_time=current_time
        ),
        backfill_start_timestamp=current_time.timestamp(),
        dynamic_partitions_store=MagicMock(),
    )
    backfill_data_after_iter1 = _single_backfill_iteration(
        "fake_id", asset_backfill_data, asset_graph, instance, repo_dict
    )
    after_iter1_requested_subset = backfill_data_after_iter1.requested_subset
    assert AssetKeyPartitionKey(AssetKey("asset1"), "a") in after_iter1_requested_subset
    assert AssetKeyPartitionKey(AssetKey("asset1"), "b") in after_iter1_requested_subset
    assert AssetKeyPartitionKey(AssetKey("asset2"), "1") not in after_iter1_requested_subset

    backfill_data_after_iter2 = _single_backfill_iteration(
        "fake_id", backfill_data_after_iter1, asset_graph, instance, repo_dict
    )
    after_iter2_requested_subset = backfill_data_after_iter2.requested_subset
    assert AssetKeyPartitionKey(AssetKey("asset2"), "1") in after_iter2_requested_subset


def test_multi_asset_internal_and_external_deps_asset_backfill() -> None:
    pd = StaticPartitionsDefinition(["1", "2", "3"])

    @asset(partitions_def=pd)
    def upstream():
        pass

    @multi_asset(
        deps={upstream},
        outs={"a": AssetOut(key="a"), "b": AssetOut(key="b"), "c": AssetOut(key="c")},
        internal_asset_deps={
            "c": {AssetKey("a"), AssetKey("upstream")},
            "b": {AssetKey("a")},
            "a": set(),
        },
        partitions_def=pd,
    )
    def my_multi_asset():
        pass

    instance = DagsterInstance.ephemeral()
    repo_with_unpartitioned_root = {"repo": [my_multi_asset, upstream]}
    asset_graph = get_asset_graph(repo_with_unpartitioned_root)
    asset_backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=["1"],
        asset_selection=[AssetKey("a"), AssetKey("b"), AssetKey("c")],
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=create_datetime(2024, 1, 9, 0, 0, 0).timestamp(),
    )
    backfill_data = _single_backfill_iteration(
        "fake_id", asset_backfill_data, asset_graph, instance, repo_with_unpartitioned_root
    )
    assert AssetKeyPartitionKey(AssetKey("a"), "1") in backfill_data.requested_subset
    assert AssetKeyPartitionKey(AssetKey("b"), "1") in backfill_data.requested_subset
    assert AssetKeyPartitionKey(AssetKey("c"), "1") in backfill_data.requested_subset


def test_run_request_partition_order():
    @asset(partitions_def=DailyPartitionsDefinition("2023-10-01"))
    def foo():
        pass

    @asset(partitions_def=DailyPartitionsDefinition("2023-10-01"), deps={foo})
    def foo_child():
        pass

    assets_by_repo_name = {"repo1": [foo], "repo2": [foo_child]}
    asset_graph = get_asset_graph(assets_by_repo_name)

    asset_backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=["2023-10-02", "2023-10-01", "2023-10-03"],
        asset_selection=[foo.key, foo_child.key],
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=create_datetime(2023, 10, 4, 0, 0, 0).timestamp(),
    )

    result = execute_asset_backfill_iteration_consume_generator(
        "apple", asset_backfill_data, asset_graph, DagsterInstance.ephemeral()
    )

    assert [run_request.partition_key for run_request in result.run_requests] == [
        "2023-10-01",
        "2023-10-02",
        "2023-10-03",
    ]


def test_asset_backfill_multiple_partition_ranges():
    instance = DagsterInstance.ephemeral()
    partitions_def = DailyPartitionsDefinition("2023-10-01")

    @asset(partitions_def=partitions_def)
    def foo():
        pass

    @asset(partitions_def=partitions_def, deps=[foo])
    def foo_child():
        pass

    assets_by_repo_name = {"repo": [foo, foo_child]}
    asset_graph = get_asset_graph(assets_by_repo_name)

    target_partitions_subset = (
        partitions_def.empty_subset()
        .with_partition_key_range(partitions_def, PartitionKeyRange("2023-11-01", "2023-11-03"))
        .with_partition_key_range(partitions_def, PartitionKeyRange("2023-11-06", "2023-11-07"))
    )
    asset_backfill_data = AssetBackfillData.from_asset_graph_subset(
        asset_graph_subset=AssetGraphSubset(
            partitions_subsets_by_asset_key={
                foo.key: target_partitions_subset,
                foo_child.key: target_partitions_subset,
            }
        ),
        dynamic_partitions_store=MagicMock(),
        backfill_start_timestamp=create_datetime(2023, 12, 5, 0, 0, 0).timestamp(),
    )
    assert set(asset_backfill_data.target_subset.iterate_asset_partitions()) == {
        AssetKeyPartitionKey(foo.key, "2023-11-01"),
        AssetKeyPartitionKey(foo.key, "2023-11-02"),
        AssetKeyPartitionKey(foo.key, "2023-11-03"),
        AssetKeyPartitionKey(foo.key, "2023-11-06"),
        AssetKeyPartitionKey(foo.key, "2023-11-07"),
        AssetKeyPartitionKey(foo_child.key, "2023-11-01"),
        AssetKeyPartitionKey(foo_child.key, "2023-11-02"),
        AssetKeyPartitionKey(foo_child.key, "2023-11-03"),
        AssetKeyPartitionKey(foo_child.key, "2023-11-06"),
        AssetKeyPartitionKey(foo_child.key, "2023-11-07"),
    }

    asset_backfill_data = _single_backfill_iteration(
        "fake_id", asset_backfill_data, asset_graph, instance, assets_by_repo_name
    )
    assert asset_backfill_data.requested_subset == asset_backfill_data.target_subset


def test_asset_backfill_with_asset_check():
    instance = DagsterInstance.ephemeral()
    partitions_def = DailyPartitionsDefinition("2023-10-01")

    @asset(partitions_def=partitions_def, backfill_policy=BackfillPolicy.single_run())
    def foo():
        pass

    @asset_check(asset=foo)
    def foo_check():
        return AssetCheckResult(passed=True)

    assets_by_repo_name = {"repo": [foo, foo_check]}
    asset_graph = get_asset_graph(assets_by_repo_name)

    target_partitions_subset = partitions_def.empty_subset().with_partition_key_range(
        partitions_def, PartitionKeyRange("2023-11-01", "2023-11-03")
    )
    asset_backfill_data = AssetBackfillData.from_asset_graph_subset(
        asset_graph_subset=AssetGraphSubset(
            partitions_subsets_by_asset_key={foo.key: target_partitions_subset}
        ),
        dynamic_partitions_store=MagicMock(),
        backfill_start_timestamp=create_datetime(2023, 12, 5, 0, 0, 0).timestamp(),
    )
    assert set(asset_backfill_data.target_subset.iterate_asset_partitions()) == {
        AssetKeyPartitionKey(foo.key, "2023-11-01"),
        AssetKeyPartitionKey(foo.key, "2023-11-02"),
        AssetKeyPartitionKey(foo.key, "2023-11-03"),
    }

    result = execute_asset_backfill_iteration_consume_generator(
        backfill_id="fake_id",
        asset_backfill_data=asset_backfill_data,
        asset_graph=asset_graph,
        instance=instance,
    )
    assert len(result.run_requests) == 1
    run_request = result.run_requests[0]
    assert run_request.asset_selection == [foo.key]
    assert run_request.asset_check_keys == [foo_check.check_key]
