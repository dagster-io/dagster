import math
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest
from dagster import (
    AssetDep,
    BackfillPolicy,
    DagsterInstance,
    DailyPartitionsDefinition,
    DynamicPartitionsDefinition,
    PartitionKeyRange,
    TimeWindowPartitionMapping,
    WeeklyPartitionsDefinition,
    asset,
)
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.execution.asset_backfill import AssetBackfillData, AssetBackfillStatus
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from dagster._core.test_utils import freeze_time
from dagster._time import (
    create_datetime,
    get_current_datetime,
    get_current_timestamp,
    parse_time_string,
)

from dagster_tests.core_tests.execution_tests.test_asset_backfill import (
    execute_asset_backfill_iteration_consume_generator,
    get_asset_graph,
    run_backfill_to_completion,
)


def test_asset_backfill_not_all_asset_have_backfill_policy() -> None:
    @asset(backfill_policy=None)
    def unpartitioned_upstream_of_partitioned():
        return 1

    @asset(
        partitions_def=DailyPartitionsDefinition("2023-01-01"),
        backfill_policy=BackfillPolicy.single_run(),
        deps=[unpartitioned_upstream_of_partitioned],
    )
    def upstream_daily_partitioned_asset():
        return 1

    assets_by_repo_name = {
        "repo": [
            unpartitioned_upstream_of_partitioned,
            upstream_daily_partitioned_asset,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=None,
        asset_graph=asset_graph,
        asset_selection=[
            unpartitioned_upstream_of_partitioned.key,
            upstream_daily_partitioned_asset.key,
        ],
        dynamic_partitions_store=MagicMock(),
        all_partitions=True,
        backfill_start_timestamp=get_current_timestamp(),
    )

    instance = DagsterInstance.ephemeral()
    _, materialized, failed = run_backfill_to_completion(
        asset_graph,
        assets_by_repo_name,
        backfill_data=backfill_data,
        fail_asset_partitions=set(),
        instance=instance,
    )

    assert len(failed) == 0
    assert {akpk.asset_key for akpk in materialized} == {
        unpartitioned_upstream_of_partitioned.key,
        upstream_daily_partitioned_asset.key,
    }

    runs = instance.get_runs(ascending=True)

    # separate runs for the assets (different partitions_def / backfill policy)
    assert len(runs) == 2

    unpartitioned = runs[0]
    assert unpartitioned.tags == {"dagster/backfill": "backfillid_x"}

    partitioned = runs[1]
    assert partitioned.tags.keys() == {
        "dagster/asset_partition_range_end",
        "dagster/asset_partition_range_start",
        "dagster/backfill",
    }


def test_asset_backfill_parent_and_children_have_different_backfill_policy():
    time_now = get_current_datetime()
    daily_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition("2023-01-01")

    @asset(partitions_def=daily_partitions_def, backfill_policy=BackfillPolicy.single_run())
    def upstream_daily_partitioned_asset():
        return 1

    @asset(partitions_def=daily_partitions_def, backfill_policy=BackfillPolicy.multi_run())
    def downstream_daily_partitioned_asset(upstream_daily_partitioned_asset):
        return upstream_daily_partitioned_asset + 1

    assets_by_repo_name = {
        "repo": [
            upstream_daily_partitioned_asset,
            downstream_daily_partitioned_asset,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)

    backfill_id = "test_backfill_id"
    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=None,
        asset_graph=asset_graph,
        asset_selection=[
            upstream_daily_partitioned_asset.key,
            downstream_daily_partitioned_asset.key,
        ],
        dynamic_partitions_store=MagicMock(),
        all_partitions=True,
        backfill_start_timestamp=time_now.timestamp(),
    )

    result1 = execute_asset_backfill_iteration_consume_generator(
        backfill_id=backfill_id,
        asset_backfill_data=backfill_data,
        asset_graph=asset_graph,
        instance=DagsterInstance.ephemeral(),
    )
    assert result1.backfill_data != backfill_data
    assert len(result1.run_requests) == 1
    # The first iteration of backfill should only create run request for the upstream asset since
    # the downstream does not have same backfill policy as the upstream.
    assert result1.run_requests[0].asset_selection == [upstream_daily_partitioned_asset.key]


def test_asset_backfill_parent_and_children_have_same_backfill_policy():
    time_now = get_current_datetime()
    daily_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition("2023-01-01")

    @asset(backfill_policy=BackfillPolicy.single_run())
    def upstream_non_partitioned_asset():
        return 1

    @asset(partitions_def=daily_partitions_def, backfill_policy=BackfillPolicy.single_run())
    def upstream_daily_partitioned_asset():
        return 1

    @asset(partitions_def=daily_partitions_def, backfill_policy=BackfillPolicy.single_run())
    def downstream_daily_partitioned_asset(upstream_daily_partitioned_asset):
        return upstream_daily_partitioned_asset + 1

    assets_by_repo_name = {
        "repo": [
            upstream_non_partitioned_asset,
            upstream_daily_partitioned_asset,
            downstream_daily_partitioned_asset,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=None,
        asset_graph=asset_graph,
        asset_selection=[
            upstream_daily_partitioned_asset.key,
            downstream_daily_partitioned_asset.key,
            upstream_non_partitioned_asset.key,
        ],
        dynamic_partitions_store=MagicMock(),
        all_partitions=True,
        backfill_start_timestamp=time_now.timestamp(),
    )

    result = execute_asset_backfill_iteration_consume_generator(
        backfill_id="test_backfill_id",
        asset_backfill_data=backfill_data,
        asset_graph=asset_graph,
        instance=DagsterInstance.ephemeral(),
    )
    assert result.backfill_data != backfill_data
    assert len(result.run_requests) == 2

    for run_request in result.run_requests:
        if run_request.tags.__contains__(ASSET_PARTITION_RANGE_START_TAG):
            # single run request for partitioned asset, both parent and the children somce they share same
            # partitions def and backfill policy
            assert run_request.partition_key is None
            assert upstream_daily_partitioned_asset.key in run_request.asset_selection  # pyright: ignore[reportOperatorIssue]
            assert downstream_daily_partitioned_asset.key in run_request.asset_selection  # pyright: ignore[reportOperatorIssue]
            assert run_request.tags.get(ASSET_PARTITION_RANGE_START_TAG) == "2023-01-01"
            assert (
                run_request.tags.get(ASSET_PARTITION_RANGE_END_TAG)
                == daily_partitions_def.get_partition_keys(time_now)[-1]
            )
        else:
            assert run_request.partition_key is None
            assert run_request.asset_selection == [upstream_non_partitioned_asset.key]
            assert run_request.tags.get(ASSET_PARTITION_RANGE_START_TAG) is None
            assert run_request.tags.get(ASSET_PARTITION_RANGE_END_TAG) is None


def test_asset_backfill_parent_and_children_have_same_backfill_policy_but_third_asset_has_different_policy():
    """Tests that when a backfill contains multiple backfill policies, we still group assets with the
    same backfill policy in a single run.
    """
    time_now = get_current_datetime()
    daily_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition("2023-01-01")

    @asset(partitions_def=daily_partitions_def, backfill_policy=BackfillPolicy.multi_run(10))
    def has_different_backfill_policy():
        return 1

    @asset(partitions_def=daily_partitions_def, backfill_policy=BackfillPolicy.multi_run(5))
    def upstream_daily_partitioned_asset():
        return 1

    @asset(partitions_def=daily_partitions_def, backfill_policy=BackfillPolicy.multi_run(5))
    def downstream_daily_partitioned_asset(upstream_daily_partitioned_asset):
        return upstream_daily_partitioned_asset + 1

    assets_by_repo_name = {
        "repo": [
            has_different_backfill_policy,
            upstream_daily_partitioned_asset,
            downstream_daily_partitioned_asset,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=[
            "2023-03-01",
            "2023-03-02",
            "2023-03-03",
        ],
        asset_graph=asset_graph,
        asset_selection=[
            upstream_daily_partitioned_asset.key,
            downstream_daily_partitioned_asset.key,
            has_different_backfill_policy.key,
        ],
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=time_now.timestamp(),
    )

    result = execute_asset_backfill_iteration_consume_generator(
        backfill_id="test_backfill_id",
        asset_backfill_data=backfill_data,
        asset_graph=asset_graph,
        instance=DagsterInstance.ephemeral(),
    )
    assert result.backfill_data != backfill_data
    assert len(result.run_requests) == 2

    for run_request in result.run_requests:
        if upstream_daily_partitioned_asset.key in run_request.asset_selection:  # pyright: ignore[reportOperatorIssue]
            assert downstream_daily_partitioned_asset.key in run_request.asset_selection  # pyright: ignore[reportOperatorIssue]
            assert has_different_backfill_policy.key not in run_request.asset_selection  # pyright: ignore[reportOperatorIssue]


def test_asset_backfill_return_single_run_request_for_non_partitioned():
    @asset(backfill_policy=BackfillPolicy.single_run())
    def unpartitioned_upstream_of_partitioned():
        return 1

    assets_by_repo_name = {
        "repo": [
            unpartitioned_upstream_of_partitioned,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=None,
        asset_graph=asset_graph,
        asset_selection=[
            unpartitioned_upstream_of_partitioned.key,
        ],
        dynamic_partitions_store=MagicMock(),
        all_partitions=True,
        backfill_start_timestamp=get_current_timestamp(),
    )
    backfill_id = "test_backfill_id"
    result = execute_asset_backfill_iteration_consume_generator(
        backfill_id=backfill_id,
        asset_backfill_data=backfill_data,
        asset_graph=asset_graph,
        instance=DagsterInstance.ephemeral(),
    )
    assert result.backfill_data != backfill_data
    assert len(result.run_requests) == 1
    assert result.run_requests[0].partition_key is None
    assert result.run_requests[0].tags == {}


def test_asset_backfill_return_single_run_request_for_partitioned():
    time_now = get_current_datetime()
    daily_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition("2023-01-01")

    @asset(partitions_def=daily_partitions_def, backfill_policy=BackfillPolicy.single_run())
    def upstream_daily_partitioned_asset():
        return 1

    assets_by_repo_name = {
        "repo": [
            upstream_daily_partitioned_asset,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=None,
        asset_graph=asset_graph,
        asset_selection=[
            upstream_daily_partitioned_asset.key,
        ],
        dynamic_partitions_store=MagicMock(),
        all_partitions=True,
        backfill_start_timestamp=time_now.timestamp(),
    )

    result = execute_asset_backfill_iteration_consume_generator(
        backfill_id="test_backfill_id",
        asset_backfill_data=backfill_data,
        asset_graph=asset_graph,
        instance=DagsterInstance.ephemeral(),
    )
    assert result.backfill_data != backfill_data
    assert len(result.run_requests) == 1
    assert result.run_requests[0].partition_key is None
    assert result.run_requests[0].tags.get(ASSET_PARTITION_RANGE_START_TAG) == "2023-01-01"
    assert (
        result.run_requests[0].tags.get(ASSET_PARTITION_RANGE_END_TAG)
        == daily_partitions_def.get_partition_keys(time_now)[-1]
    )


def test_asset_backfill_return_multiple_run_request_for_partitioned():
    time_now = get_current_datetime()
    daily_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition(
        "2023-01-01", end_date="2023-08-11"
    )
    num_of_daily_partitions = daily_partitions_def.get_num_partitions(time_now)

    @asset(partitions_def=daily_partitions_def, backfill_policy=BackfillPolicy.multi_run(7))
    def upstream_daily_partitioned_asset():
        return 1

    assets_by_repo_name = {
        "repo": [
            upstream_daily_partitioned_asset,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=None,
        asset_graph=asset_graph,
        asset_selection=[
            upstream_daily_partitioned_asset.key,
        ],
        dynamic_partitions_store=MagicMock(),
        all_partitions=True,
        backfill_start_timestamp=time_now.timestamp(),
    )

    result = execute_asset_backfill_iteration_consume_generator(
        backfill_id="test_backfill_id",
        asset_backfill_data=backfill_data,
        asset_graph=asset_graph,
        instance=DagsterInstance.ephemeral(),
    )
    assert result.backfill_data != backfill_data
    assert len(result.run_requests) == math.ceil(num_of_daily_partitions / 7)
    assert result.run_requests[0].partition_key is None
    assert result.run_requests[0].tags.get(ASSET_PARTITION_RANGE_START_TAG) == "2023-01-01"
    assert (
        result.run_requests[-1].tags.get(ASSET_PARTITION_RANGE_END_TAG)
        == daily_partitions_def.get_partition_keys(time_now)[-1]
    )


def test_asset_backfill_status_count_with_backfill_policies():
    daily_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition("2023-01-01")
    weekly_partitions_def = WeeklyPartitionsDefinition("2023-01-01")

    time_now = get_current_datetime()
    num_of_daily_partitions = daily_partitions_def.get_num_partitions(time_now)
    num_of_weekly_partitions = weekly_partitions_def.get_num_partitions(time_now)

    @asset(backfill_policy=BackfillPolicy.single_run())
    def unpartitioned_upstream_of_partitioned():
        return 1

    @asset(
        partitions_def=daily_partitions_def,
        backfill_policy=BackfillPolicy.single_run(),
        deps={unpartitioned_upstream_of_partitioned},
    )
    def upstream_daily_partitioned_asset():
        return 2

    @asset(
        partitions_def=weekly_partitions_def,
        backfill_policy=BackfillPolicy.single_run(),
        deps={upstream_daily_partitioned_asset},
    )
    def downstream_weekly_partitioned_asset():
        return 3

    assets_by_repo_name = {
        "repo": [
            unpartitioned_upstream_of_partitioned,
            upstream_daily_partitioned_asset,
            downstream_weekly_partitioned_asset,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)
    instance = DagsterInstance.ephemeral()

    # Construct a backfill data with all_partitions=True on assets with single run backfill policies.
    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=None,
        asset_graph=asset_graph,
        asset_selection=[
            unpartitioned_upstream_of_partitioned.key,
            upstream_daily_partitioned_asset.key,
            downstream_weekly_partitioned_asset.key,
        ],
        dynamic_partitions_store=MagicMock(),
        all_partitions=True,
        backfill_start_timestamp=time_now.timestamp(),
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
        fail_asset_partitions=set(),
    )

    counts = completed_backfill_data.get_backfill_status_per_asset_key(asset_graph)

    assert counts[0].asset_key == unpartitioned_upstream_of_partitioned.key
    assert counts[0].backfill_status == AssetBackfillStatus.MATERIALIZED  # pyright: ignore[reportAttributeAccessIssue]

    assert counts[1].asset_key == upstream_daily_partitioned_asset.key
    assert (
        counts[1].partitions_counts_by_status[AssetBackfillStatus.MATERIALIZED]  # pyright: ignore[reportAttributeAccessIssue]
        == num_of_daily_partitions
    )
    assert counts[1].num_targeted_partitions == num_of_daily_partitions  # pyright: ignore[reportAttributeAccessIssue]

    assert counts[2].asset_key == downstream_weekly_partitioned_asset.key
    assert (
        counts[2].partitions_counts_by_status[AssetBackfillStatus.MATERIALIZED]  # pyright: ignore[reportAttributeAccessIssue]
        == num_of_weekly_partitions
    )
    assert counts[2].num_targeted_partitions == num_of_weekly_partitions  # pyright: ignore[reportAttributeAccessIssue]


def test_backfill_run_contains_more_than_one_asset():
    upstream_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition("2023-01-01")
    downstream_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition("2023-01-02")

    time_now = get_current_datetime()
    upstream_num_of_partitions = upstream_partitions_def.get_num_partitions(time_now)
    downstream_num_of_partitions = downstream_partitions_def.get_num_partitions(time_now)

    @asset(partitions_def=upstream_partitions_def, backfill_policy=BackfillPolicy.single_run())
    def upstream_a():
        return 1

    @asset(partitions_def=upstream_partitions_def, backfill_policy=BackfillPolicy.single_run())
    def upstream_b():
        return 2

    @asset(
        partitions_def=downstream_partitions_def,
        backfill_policy=BackfillPolicy.single_run(),
        deps={"upstream_a"},
    )
    def downstream_a():
        return 1

    @asset(
        partitions_def=downstream_partitions_def,
        backfill_policy=BackfillPolicy.single_run(),
        deps={"upstream_b"},
    )
    def downstream_b():
        return 2

    assets_by_repo_name = {"repo": [upstream_a, upstream_b, downstream_a, downstream_b]}
    asset_graph = get_asset_graph(assets_by_repo_name)
    instance = DagsterInstance.ephemeral()

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=None,
        asset_graph=asset_graph,
        asset_selection=[
            upstream_a.key,
            upstream_b.key,
            downstream_a.key,
            downstream_b.key,
        ],
        dynamic_partitions_store=MagicMock(),
        all_partitions=True,
        backfill_start_timestamp=time_now.timestamp(),
    )

    (
        completed_backfill_data,
        _,
        _,
    ) = run_backfill_to_completion(
        instance=instance,
        asset_graph=asset_graph,
        assets_by_repo_name=assets_by_repo_name,
        backfill_data=backfill_data,
        fail_asset_partitions=set(),
    )

    counts = completed_backfill_data.get_backfill_status_per_asset_key(asset_graph)

    assert counts[0].asset_key == upstream_a.key
    assert (
        counts[0].partitions_counts_by_status[AssetBackfillStatus.MATERIALIZED]  # pyright: ignore[reportAttributeAccessIssue]
        == upstream_num_of_partitions
    )
    assert counts[0].partitions_counts_by_status[AssetBackfillStatus.FAILED] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[0].partitions_counts_by_status[AssetBackfillStatus.IN_PROGRESS] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[0].num_targeted_partitions == upstream_num_of_partitions  # pyright: ignore[reportAttributeAccessIssue]

    assert counts[1].asset_key == upstream_b.key
    assert (
        counts[1].partitions_counts_by_status[AssetBackfillStatus.MATERIALIZED]  # pyright: ignore[reportAttributeAccessIssue]
        == upstream_num_of_partitions
    )
    assert counts[1].partitions_counts_by_status[AssetBackfillStatus.FAILED] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[1].partitions_counts_by_status[AssetBackfillStatus.IN_PROGRESS] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[1].num_targeted_partitions == upstream_num_of_partitions  # pyright: ignore[reportAttributeAccessIssue]

    assert counts[2].asset_key == downstream_a.key
    assert (
        counts[2].partitions_counts_by_status[AssetBackfillStatus.MATERIALIZED]  # pyright: ignore[reportAttributeAccessIssue]
        == downstream_num_of_partitions
    )
    assert counts[2].partitions_counts_by_status[AssetBackfillStatus.FAILED] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[2].partitions_counts_by_status[AssetBackfillStatus.IN_PROGRESS] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[2].num_targeted_partitions == downstream_num_of_partitions  # pyright: ignore[reportAttributeAccessIssue]

    assert counts[3].asset_key == downstream_b.key
    assert (
        counts[3].partitions_counts_by_status[AssetBackfillStatus.MATERIALIZED]  # pyright: ignore[reportAttributeAccessIssue]
        == downstream_num_of_partitions
    )
    assert counts[3].partitions_counts_by_status[AssetBackfillStatus.FAILED] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[3].partitions_counts_by_status[AssetBackfillStatus.IN_PROGRESS] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[3].num_targeted_partitions == downstream_num_of_partitions  # pyright: ignore[reportAttributeAccessIssue]


def test_dynamic_partitions_multi_run_backfill_policy():
    @asset(
        backfill_policy=BackfillPolicy.multi_run(),
        partitions_def=DynamicPartitionsDefinition(name="apple"),
    )
    def asset1() -> None: ...

    assets_by_repo_name = {"repo": [asset1]}
    asset_graph = get_asset_graph(assets_by_repo_name)

    instance = DagsterInstance.ephemeral()
    instance.add_dynamic_partitions("apple", ["foo", "bar"])

    backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        asset_selection=[asset1.key],
        dynamic_partitions_store=instance,
        partition_names=["foo", "bar"],
        backfill_start_timestamp=get_current_timestamp(),
        all_partitions=False,
    )

    result = execute_asset_backfill_iteration_consume_generator(
        backfill_id="test_backfill_id",
        asset_backfill_data=backfill_data,
        asset_graph=asset_graph,
        instance=instance,
    )
    assert result.backfill_data != backfill_data
    assert len(result.run_requests) == 2
    assert any(
        run_request.tags.get(ASSET_PARTITION_RANGE_START_TAG) == "foo"
        and run_request.tags.get(ASSET_PARTITION_RANGE_END_TAG) == "foo"
        for run_request in result.run_requests
    )
    assert any(
        run_request.tags.get(ASSET_PARTITION_RANGE_START_TAG) == "bar"
        and run_request.tags.get(ASSET_PARTITION_RANGE_END_TAG) == "bar"
        for run_request in result.run_requests
    )


def test_dynamic_partitions_single_run_backfill_policy():
    @asset(
        backfill_policy=BackfillPolicy.single_run(),
        partitions_def=DynamicPartitionsDefinition(name="apple"),
    )
    def asset1() -> None: ...

    assets_by_repo_name = {"repo": [asset1]}
    asset_graph = get_asset_graph(assets_by_repo_name)

    instance = DagsterInstance.ephemeral()
    instance.add_dynamic_partitions("apple", ["foo", "bar"])

    backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        asset_selection=[asset1.key],
        dynamic_partitions_store=instance,
        partition_names=["foo", "bar"],
        backfill_start_timestamp=get_current_timestamp(),
        all_partitions=False,
    )

    result = execute_asset_backfill_iteration_consume_generator(
        backfill_id="test_backfill_id",
        asset_backfill_data=backfill_data,
        asset_graph=asset_graph,
        instance=instance,
    )
    assert result.backfill_data != backfill_data
    assert len(result.run_requests) == 1
    assert result.run_requests[0].tags.get(ASSET_PARTITION_RANGE_START_TAG) == "foo"
    assert result.run_requests[0].tags.get(ASSET_PARTITION_RANGE_END_TAG) == "bar"


@pytest.mark.parametrize("same_partitions", [True, False])
def test_assets_backfill_with_partition_mapping(same_partitions):
    daily_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition("2023-01-01")
    if same_partitions:
        # time at which there will be an identical set of partitions for the downstream asset
        test_time = parse_time_string("2023-03-04T00:00:00")
    else:
        test_time = get_current_datetime()

    @asset(
        name="upstream_a",
        partitions_def=daily_partitions_def,
        backfill_policy=BackfillPolicy.multi_run(30),
    )
    def upstream_a():
        return 1

    @asset(
        name="downstream_b",
        partitions_def=daily_partitions_def,
        backfill_policy=BackfillPolicy.multi_run(30),
        deps=[
            AssetDep(
                upstream_a,
                partition_mapping=TimeWindowPartitionMapping(
                    start_offset=-3, end_offset=0, allow_nonexistent_upstream_partitions=True
                ),
            )
        ],
    )
    def downstream_b():
        return 2

    assets_by_repo_name = {"repo": [upstream_a, downstream_b]}
    asset_graph = get_asset_graph(assets_by_repo_name)
    instance = DagsterInstance.ephemeral()

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=[
            "2023-03-01",
            "2023-03-02",
            "2023-03-03",
        ],
        asset_graph=asset_graph,
        asset_selection=[upstream_a.key, downstream_b.key],
        dynamic_partitions_store=MagicMock(),
        backfill_start_timestamp=test_time.timestamp(),
        all_partitions=False,
    )
    assert backfill_data
    with freeze_time(test_time):
        result = execute_asset_backfill_iteration_consume_generator(
            backfill_id="test_backfill_id",
            asset_backfill_data=backfill_data,
            asset_graph=asset_graph,
            instance=instance,
        )
    assert len(result.run_requests) == 1

    if same_partitions:
        assert set(result.run_requests[0].asset_selection) == {upstream_a.key, downstream_b.key}  # pyright: ignore[reportArgumentType]
    else:
        assert set(result.run_requests[0].asset_selection) == {upstream_a.key}  # pyright: ignore[reportArgumentType]

    assert result.run_requests[0].tags.get(ASSET_PARTITION_RANGE_START_TAG) == "2023-03-01"
    assert result.run_requests[0].tags.get(ASSET_PARTITION_RANGE_END_TAG) == "2023-03-03"


@pytest.mark.parametrize("same_partitions", [True, False])
def test_assets_backfill_with_partition_mapping_run_to_complete(same_partitions):
    daily_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition("2023-01-01")
    if same_partitions:
        # time at which there will be an identical set of partitions for the downstream asset
        test_time = parse_time_string("2023-03-04T00:00:00")
    else:
        test_time = get_current_datetime()

    @asset(
        name="upstream_a",
        partitions_def=daily_partitions_def,
        backfill_policy=BackfillPolicy.multi_run(30),
    )
    def upstream_a():
        return 1

    @asset(
        name="downstream_b",
        partitions_def=daily_partitions_def,
        backfill_policy=BackfillPolicy.multi_run(30),
        deps=[
            AssetDep(
                upstream_a,
                partition_mapping=TimeWindowPartitionMapping(
                    start_offset=-3, end_offset=0, allow_nonexistent_upstream_partitions=True
                ),
            )
        ],
    )
    def downstream_b():
        return 2

    assets_by_repo_name = {"repo": [upstream_a, downstream_b]}
    asset_graph = get_asset_graph(assets_by_repo_name)
    instance = DagsterInstance.ephemeral()

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=[
            "2023-03-01",
            "2023-03-02",
            "2023-03-03",
        ],
        asset_graph=asset_graph,
        asset_selection=[upstream_a.key, downstream_b.key],
        dynamic_partitions_store=MagicMock(),
        backfill_start_timestamp=test_time.timestamp(),
        all_partitions=False,
    )

    (
        completed_backfill_data,
        _,
        _,
    ) = run_backfill_to_completion(
        instance=instance,
        asset_graph=asset_graph,
        assets_by_repo_name=assets_by_repo_name,
        backfill_data=backfill_data,
        fail_asset_partitions=set(),
    )

    counts = completed_backfill_data.get_backfill_status_per_asset_key(asset_graph)
    assert counts[0].asset_key == upstream_a.key
    assert counts[0].partitions_counts_by_status[AssetBackfillStatus.MATERIALIZED] == 3  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[0].partitions_counts_by_status[AssetBackfillStatus.FAILED] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[0].partitions_counts_by_status[AssetBackfillStatus.IN_PROGRESS] == 0  # pyright: ignore[reportAttributeAccessIssue]

    assert counts[1].asset_key == downstream_b.key
    assert (
        counts[1].partitions_counts_by_status[AssetBackfillStatus.MATERIALIZED] == 3  # pyright: ignore[reportAttributeAccessIssue]
        if same_partitions
        else 6
    )
    assert counts[1].partitions_counts_by_status[AssetBackfillStatus.FAILED] == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert counts[1].partitions_counts_by_status[AssetBackfillStatus.IN_PROGRESS] == 0  # pyright: ignore[reportAttributeAccessIssue]


def test_assets_backfill_with_partition_mapping_without_backfill_policy():
    daily_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition("2023-01-01")
    time_now = get_current_datetime()

    @asset(
        name="upstream_a",
        partitions_def=daily_partitions_def,
    )
    def upstream_a():
        return 1

    @asset(
        name="downstream_b",
        partitions_def=daily_partitions_def,
        deps=[
            AssetDep(
                upstream_a,
                partition_mapping=TimeWindowPartitionMapping(
                    start_offset=-1, end_offset=0, allow_nonexistent_upstream_partitions=True
                ),
            )
        ],
    )
    def downstream_b():
        return 2

    assets_by_repo_name = {"repo": [upstream_a, downstream_b]}
    asset_graph = get_asset_graph(assets_by_repo_name)
    instance = DagsterInstance.ephemeral()

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=[
            "2023-03-02",
            "2023-03-03",
        ],
        asset_graph=asset_graph,
        asset_selection=[upstream_a.key, downstream_b.key],
        dynamic_partitions_store=MagicMock(),
        backfill_start_timestamp=time_now.timestamp(),
        all_partitions=False,
    )
    assert backfill_data
    result = execute_asset_backfill_iteration_consume_generator(
        backfill_id="test_backfill_id",
        asset_backfill_data=backfill_data,
        asset_graph=asset_graph,
        instance=instance,
    )
    assert len(result.run_requests) == 2

    for run_request in result.run_requests:
        # b should not be materialized in the same run as a
        if run_request.partition_key == "2023-03-02":
            assert set(run_request.asset_selection) == {upstream_a.key}  # pyright: ignore[reportArgumentType]
        elif run_request.partition_key == "2023-03-03":
            assert set(run_request.asset_selection) == {upstream_a.key}  # pyright: ignore[reportArgumentType]
        else:
            # should only have the above 2 partitions
            assert False


def test_assets_backfill_with_partition_mapping_with_one_partition_multi_run_backfill_policy():
    daily_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition("2023-01-01")
    time_now = get_current_datetime()

    @asset(
        name="upstream_a",
        partitions_def=daily_partitions_def,
        backfill_policy=BackfillPolicy.multi_run(1),
    )
    def upstream_a():
        return 1

    @asset(
        name="downstream_b",
        partitions_def=daily_partitions_def,
        backfill_policy=BackfillPolicy.multi_run(1),
        deps=[
            AssetDep(
                upstream_a,
                partition_mapping=TimeWindowPartitionMapping(
                    start_offset=-1, end_offset=0, allow_nonexistent_upstream_partitions=True
                ),
            )
        ],
    )
    def downstream_b():
        return 2

    assets_by_repo_name = {"repo": [upstream_a, downstream_b]}
    asset_graph = get_asset_graph(assets_by_repo_name)
    instance = DagsterInstance.ephemeral()

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=[
            "2023-03-02",
            "2023-03-03",
        ],
        asset_graph=asset_graph,
        asset_selection=[upstream_a.key, downstream_b.key],
        dynamic_partitions_store=MagicMock(),
        backfill_start_timestamp=time_now.timestamp(),
        all_partitions=False,
    )
    assert backfill_data
    result = execute_asset_backfill_iteration_consume_generator(
        backfill_id="test_backfill_id",
        asset_backfill_data=backfill_data,
        asset_graph=asset_graph,
        instance=instance,
    )
    assert len(result.run_requests) == 2


def test_assets_backfill_with_partition_mapping_with_multi_partitions_multi_run_backfill_policy():
    daily_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition("2023-01-01")
    time_now = get_current_datetime()

    @asset(
        name="upstream_a",
        partitions_def=daily_partitions_def,
        backfill_policy=BackfillPolicy.multi_run(2),
    )
    def upstream_a():
        return 1

    @asset(
        name="downstream_b",
        partitions_def=daily_partitions_def,
        backfill_policy=BackfillPolicy.multi_run(2),
        deps=[
            AssetDep(
                upstream_a,
                partition_mapping=TimeWindowPartitionMapping(
                    start_offset=-1, end_offset=0, allow_nonexistent_upstream_partitions=True
                ),
            )
        ],
    )
    def downstream_b():
        return 2

    assets_by_repo_name = {"repo": [upstream_a, downstream_b]}
    asset_graph = get_asset_graph(assets_by_repo_name)
    instance = DagsterInstance.ephemeral()

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=[
            "2023-03-02",
            "2023-03-03",
            "2023-03-04",
            "2023-03-05",
            "2023-03-06",
            "2023-03-07",
            "2023-03-08",
            "2023-03-09",
        ],
        asset_graph=asset_graph,
        asset_selection=[upstream_a.key, downstream_b.key],
        dynamic_partitions_store=MagicMock(),
        backfill_start_timestamp=time_now.timestamp(),
        all_partitions=False,
    )
    assert backfill_data
    result = execute_asset_backfill_iteration_consume_generator(
        backfill_id="test_backfill_id",
        asset_backfill_data=backfill_data,
        asset_graph=asset_graph,
        instance=instance,
    )
    assert len(result.run_requests) == 4

    for run_request in result.run_requests:
        # there is no parallel runs for downstream_b before upstream_a's targeted partitions are materialized
        assert set(run_request.asset_selection) == {upstream_a.key}  # pyright: ignore[reportArgumentType]


def test_assets_backfill_with_partition_mapping_with_single_run_backfill_policy():
    daily_partitions_def: DailyPartitionsDefinition = DailyPartitionsDefinition("2023-01-01")
    test_time = parse_time_string("2023-03-10T00:00:00")

    @asset(
        name="upstream_a",
        partitions_def=daily_partitions_def,
        backfill_policy=BackfillPolicy.single_run(),
    )
    def upstream_a():
        return 1

    @asset(
        name="downstream_b",
        partitions_def=daily_partitions_def,
        backfill_policy=BackfillPolicy.single_run(),
        deps=[
            AssetDep(
                upstream_a,
                partition_mapping=TimeWindowPartitionMapping(
                    start_offset=-1, end_offset=0, allow_nonexistent_upstream_partitions=True
                ),
            )
        ],
    )
    def downstream_b():
        return 2

    assets_by_repo_name = {"repo": [upstream_a, downstream_b]}
    asset_graph = get_asset_graph(assets_by_repo_name)
    instance = DagsterInstance.ephemeral()

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=[
            "2023-03-02",
            "2023-03-03",
            "2023-03-04",
            "2023-03-05",
            "2023-03-06",
            "2023-03-07",
            "2023-03-08",
            "2023-03-09",
        ],
        asset_graph=asset_graph,
        asset_selection=[upstream_a.key, downstream_b.key],
        dynamic_partitions_store=MagicMock(),
        backfill_start_timestamp=test_time.timestamp(),
        all_partitions=False,
    )
    assert backfill_data
    with freeze_time(test_time):
        result = execute_asset_backfill_iteration_consume_generator(
            backfill_id="test_backfill_id",
            asset_backfill_data=backfill_data,
            asset_graph=asset_graph,
            instance=instance,
        )

    assert len(result.run_requests) == 1
    assert set(result.run_requests[0].asset_selection) == {upstream_a.key, downstream_b.key}  # pyright: ignore[reportArgumentType]
    assert result.run_requests[0].tags.get(ASSET_PARTITION_RANGE_START_TAG) == "2023-03-02"
    assert result.run_requests[0].tags.get(ASSET_PARTITION_RANGE_END_TAG) == "2023-03-09"


def test_run_request_partition_order():
    @asset(
        partitions_def=DailyPartitionsDefinition("2023-10-01"),
        backfill_policy=BackfillPolicy.multi_run(2),
    )
    def foo():
        pass

    @asset(
        partitions_def=DailyPartitionsDefinition("2023-10-01"),
        backfill_policy=BackfillPolicy.multi_run(2),
        deps={foo},
    )
    def foo_child():
        pass

    assets_by_repo_name = {"repo1": [foo], "repo2": [foo_child]}
    asset_graph = get_asset_graph(assets_by_repo_name)

    asset_backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=[
            "2023-10-05",
            "2023-10-06",
            "2023-10-02",
            "2023-10-01",
            "2023-10-03",
            "2023-10-04",
        ],
        asset_selection=[foo.key, foo_child.key],
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=create_datetime(2023, 10, 7, 0, 0, 0).timestamp(),
    )

    result = execute_asset_backfill_iteration_consume_generator(
        "apple", asset_backfill_data, asset_graph, DagsterInstance.ephemeral()
    )

    assert [run_request.partition_key_range for run_request in result.run_requests] == [
        PartitionKeyRange("2023-10-01", "2023-10-02"),
        PartitionKeyRange("2023-10-03", "2023-10-04"),
        PartitionKeyRange("2023-10-05", "2023-10-06"),
    ]


def test_max_partitions_per_range_1_sets_run_request_partition_key():
    @asset(
        partitions_def=DailyPartitionsDefinition("2023-10-01"),
        backfill_policy=BackfillPolicy.multi_run(1),
    )
    def foo():
        pass

    asset_graph = get_asset_graph({"repo1": [foo]})

    asset_backfill_data = AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=[
            "2023-10-05",
            "2023-10-06",
        ],
        asset_selection=[foo.key],
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_timestamp=create_datetime(2023, 10, 7, 0, 0, 0).timestamp(),
    )

    result = execute_asset_backfill_iteration_consume_generator(
        "apple", asset_backfill_data, asset_graph, DagsterInstance.ephemeral()
    )

    assert [run_request.partition_key for run_request in result.run_requests] == [
        "2023-10-05",
        "2023-10-06",
    ]

    assert [run_request.partition_key_range for run_request in result.run_requests] == [
        PartitionKeyRange("2023-10-05", "2023-10-05"),
        PartitionKeyRange("2023-10-06", "2023-10-06"),
    ]


# 0 turns off batching
# 2 will require multiple batches to fulfill the backfill
# 10 will require a single to fulfill the backfill
@pytest.mark.parametrize("batch_size", [0, 2, 10])
@pytest.mark.parametrize("throw_store_event_batch_error", [False, True])
def test_single_run_backfill_full_execution(
    batch_size: int, throw_store_event_batch_error: bool, capsys, monkeypatch
):
    time_now = get_current_datetime()

    partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])

    @asset(partitions_def=partitions_def, backfill_policy=BackfillPolicy.single_run())
    def partitioned_asset():
        return {"a": 1, "b": 2}

    assets_by_repo_name = {
        "repo": [
            partitioned_asset,
        ]
    }
    asset_graph = get_asset_graph(assets_by_repo_name)

    backfill_data = AssetBackfillData.from_asset_partitions(
        partition_names=None,
        asset_graph=asset_graph,
        asset_selection=[
            partitioned_asset.key,
        ],
        dynamic_partitions_store=MagicMock(),
        all_partitions=True,
        backfill_start_timestamp=time_now.timestamp(),
    )

    with instance_for_test() as instance:
        with ExitStack() as stack:
            monkeypatch.setenv("DAGSTER_EVENT_BATCH_SIZE", str(batch_size))
            if throw_store_event_batch_error:
                stack.enter_context(
                    patch(
                        "dagster._core.storage.event_log.base.EventLogStorage.store_event_batch",
                        side_effect=Exception("failed"),
                    )
                )
            run_backfill_to_completion(
                asset_graph,
                assets_by_repo_name,
                backfill_data,
                [],
                instance,
            )
            events = instance.fetch_materializations(partitioned_asset.key, limit=5000).records
            assert len(events) == 4

            if batch_size > 0 and throw_store_event_batch_error:
                stderr = capsys.readouterr().err
                assert "Exception while storing event batch" in stderr
                assert (
                    "Falling back to storing multiple single-event storage requests...\n" in stderr
                )
