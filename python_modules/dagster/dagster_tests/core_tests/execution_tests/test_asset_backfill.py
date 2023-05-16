import datetime
from typing import Iterable, Mapping, NamedTuple, Optional, Sequence, Set, Union, cast
from unittest.mock import MagicMock, patch

import pendulum
import pytest
from dagster import (
    AssetKey,
    AssetsDefinition,
    DagsterInstance,
    DailyPartitionsDefinition,
    Definitions,
    HourlyPartitionsDefinition,
    PartitionsDefinition,
    StaticPartitionsDefinition,
    WeeklyPartitionsDefinition,
    asset,
)
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.execution.asset_backfill import (
    AssetBackfillData,
    AssetBackfillIterationResult,
    AssetBackfillStatus,
    execute_asset_backfill_iteration_inner,
)
from dagster._core.host_representation.external_data import external_asset_graph_from_defs
from dagster._core.test_utils import instance_for_test
from dagster._seven.compat.pendulum import create_pendulum_time
from dagster._utils import Counter, traced_counter

from dagster_tests.definitions_tests.asset_reconciliation_tests.asset_reconciliation_scenario import (
    do_run,
)
from dagster_tests.definitions_tests.asset_reconciliation_tests.exotic_partition_mapping_scenarios import (
    one_asset_self_dependency,
    root_assets_different_partitions_same_downstream,
    two_assets_in_sequence_fan_in_partitions,
    two_assets_in_sequence_fan_out_partitions,
)
from dagster_tests.definitions_tests.asset_reconciliation_tests.partition_scenarios import (
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


class AssetBackfillScenario(NamedTuple):
    assets_by_repo_name: Mapping[str, Sequence[AssetsDefinition]]
    evaluation_time: datetime.datetime
    # when backfilling "some" partitions, the subset of partitions of root assets in the backfill
    # to target:
    target_root_partition_keys: Optional[Sequence[str]]


def scenario(
    assets: Union[Mapping[str, Sequence[AssetsDefinition]], Sequence[AssetsDefinition]],
    evaluation_time: Optional[datetime.datetime] = None,
    target_root_partition_keys: Optional[Sequence[str]] = None,
) -> AssetBackfillScenario:
    if isinstance(assets, list):
        assets_by_repo_name = {"repo": assets}
    else:
        assets_by_repo_name = assets

    return AssetBackfillScenario(
        assets_by_repo_name=cast(Mapping[str, Sequence[AssetsDefinition]], assets_by_repo_name),
        evaluation_time=evaluation_time if evaluation_time else pendulum.now("UTC"),
        target_root_partition_keys=target_root_partition_keys,
    )


scenarios = {
    "one_asset_one_partition": scenario(one_asset_one_partition),
    "one_asset_two_partitions": scenario(one_asset_two_partitions),
    "two_assets_in_sequence_one_partition": scenario(two_assets_in_sequence_one_partition),
    "two_assets_in_sequence_one_partition_cross_repo": scenario(
        {
            "repo1": [two_assets_in_sequence_one_partition[0]],
            "repo2": [two_assets_in_sequence_one_partition[1]],
        },
    ),
    "two_assets_in_sequence_two_partitions": scenario(two_assets_in_sequence_two_partitions),
    "two_assets_in_sequence_fan_in_partitions": scenario(two_assets_in_sequence_fan_in_partitions),
    "two_assets_in_sequence_fan_out_partitions": scenario(
        two_assets_in_sequence_fan_out_partitions
    ),
    "one_asset_self_dependency": scenario(
        one_asset_self_dependency, create_pendulum_time(year=2020, month=1, day=7, hour=4)
    ),
    "non_partitioned_after_partitioned": scenario(
        non_partitioned_after_partitioned, create_pendulum_time(year=2020, month=1, day=7, hour=4)
    ),
    "partitioned_after_non_partitioned": scenario(
        partitioned_after_non_partitioned, create_pendulum_time(year=2020, month=1, day=7, hour=4)
    ),
    "unpartitioned_after_dynamic_asset": scenario(unpartitioned_after_dynamic_asset),
    "two_dynamic_assets": scenario(two_dynamic_assets),
    "hourly_to_daily_partiitons": scenario(
        hourly_to_daily_partitions,
        create_pendulum_time(year=2013, month=1, day=7, hour=0),
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
        create_pendulum_time(year=2013, month=1, day=7, hour=10),
        target_root_partition_keys=[
            "2013-01-07-05:00",
        ],
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
            [("asset1", None), ("asset2", "2022-01-01"), ("asset2", "2022-01-02")],
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
        asset_selection=list(asset_graph.all_asset_keys),
        dynamic_partitions_store=MagicMock(),
        all_partitions=False,
        backfill_start_time=scenarios[scenario_name].evaluation_time,
    )
    assert backfill_data.target_subset == AssetGraphSubset.from_asset_partition_set(
        {
            AssetKeyPartitionKey(AssetKey(asset_key_str), partition_key)
            for asset_key_str, partition_key in expected_target_asset_partitions
        },
        asset_graph=asset_graph,
    )


@pytest.mark.parametrize("some_or_all", ["all", "some"])
@pytest.mark.parametrize("failures", ["no_failures", "root_failures", "random_half_failures"])
@pytest.mark.parametrize("scenario", list(scenarios.values()), ids=list(scenarios.keys()))
def test_scenario_to_completion(scenario: AssetBackfillScenario, failures: str, some_or_all: str):
    with instance_for_test() as instance:
        instance.add_dynamic_partitions("foo", ["a", "b"])

        with pendulum.test(scenario.evaluation_time):
            assets_by_repo_name = scenario.assets_by_repo_name

            asset_graph = get_asset_graph(assets_by_repo_name)
            if some_or_all == "all":
                target_subset = AssetGraphSubset.all(asset_graph, dynamic_partitions_store=instance)
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

            backfill_data = AssetBackfillData.empty(target_subset, scenario.evaluation_time)

            if failures == "no_failures":
                fail_asset_partitions: Set[AssetKeyPartitionKey] = set()
            elif failures == "root_failures":
                fail_asset_partitions = set(
                    (
                        backfill_data.target_subset.filter_asset_keys(asset_graph.root_asset_keys)
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
        backfill_data=make_backfill_data("all", asset_graph, instance, None),
        fail_asset_partitions=set(),
    )


def make_backfill_data(
    some_or_all: str,
    asset_graph: ExternalAssetGraph,
    instance: DagsterInstance,
    current_time: datetime.datetime,
) -> AssetBackfillData:
    if some_or_all == "all":
        target_subset = AssetGraphSubset.all(asset_graph, dynamic_partitions_store=instance)
    elif some_or_all == "some":
        target_subset = make_random_subset(asset_graph, instance, current_time)
    else:
        assert False

    return AssetBackfillData.empty(target_subset, current_time or pendulum.now("UTC"))


def make_random_subset(
    asset_graph: ExternalAssetGraph,
    instance: DagsterInstance,
    evaluation_time: datetime.datetime,
) -> AssetGraphSubset:
    # all partitions downstream of half of the partitions in each partitioned root asset
    root_asset_partitions: Set[AssetKeyPartitionKey] = set()
    for i, root_asset_key in enumerate(sorted(asset_graph.root_asset_keys)):
        partitions_def = asset_graph.get_partitions_def(root_asset_key)

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

    target_asset_partitions = asset_graph.bfs_filter_asset_partitions(
        instance, lambda _a, _b: True, root_asset_partitions, evaluation_time=evaluation_time
    )

    return AssetGraphSubset.from_asset_partition_set(target_asset_partitions, asset_graph)


def make_subset_from_partition_keys(
    partition_keys: Sequence[str],
    asset_graph: ExternalAssetGraph,
    instance: DagsterInstance,
    evaluation_time: datetime.datetime,
) -> AssetGraphSubset:
    root_asset_partitions: Set[AssetKeyPartitionKey] = set()
    for i, root_asset_key in enumerate(sorted(asset_graph.root_asset_keys)):
        if asset_graph.get_partitions_def(root_asset_key) is not None:
            root_asset_partitions.update(
                AssetKeyPartitionKey(root_asset_key, partition_key)
                for partition_key in partition_keys
            )
        else:
            root_asset_partitions.add(AssetKeyPartitionKey(root_asset_key, None))

    target_asset_partitions = asset_graph.bfs_filter_asset_partitions(
        instance, lambda _a, _b: True, root_asset_partitions, evaluation_time=evaluation_time
    )

    return AssetGraphSubset.from_asset_partition_set(target_asset_partitions, asset_graph)


def get_asset_graph(
    assets_by_repo_name: Mapping[str, Sequence[AssetsDefinition]]
) -> ExternalAssetGraph:
    assets_defs_by_key = {
        assets_def.key: assets_def
        for assets in assets_by_repo_name.values()
        for assets_def in assets
    }
    with patch(
        "dagster._core.host_representation.external_data.get_builtin_partition_mapping_types"
    ) as get_builtin_partition_mapping_types:
        get_builtin_partition_mapping_types.return_value = tuple(
            assets_def.infer_partition_mapping(
                dep_key, assets_defs_by_key[dep_key].partitions_def
            ).__class__
            for assets in assets_by_repo_name.values()
            for assets_def in assets
            for dep_key in assets_def.dependency_keys
        )
        return external_asset_graph_from_assets_by_repo_name(assets_by_repo_name)


def execute_asset_backfill_iteration_consume_generator(
    backfill_id: str,
    asset_backfill_data: AssetBackfillData,
    asset_graph: ExternalAssetGraph,
    instance: DagsterInstance,
) -> AssetBackfillIterationResult:
    traced_counter.set(Counter())
    for result in execute_asset_backfill_iteration_inner(
        backfill_id=backfill_id,
        asset_backfill_data=asset_backfill_data,
        instance=instance,
        asset_graph=asset_graph,
        run_tags={},
        backfill_start_time=asset_backfill_data.backfill_start_time,
    ):
        if isinstance(result, AssetBackfillIterationResult):
            counts = traced_counter.get().counts()
            assert counts.get("DagsterInstance.get_dynamic_partitions", 0) <= 1
            return result

    assert False


def run_backfill_to_completion(
    asset_graph: ExternalAssetGraph,
    assets_by_repo_name: Mapping[str, Sequence[AssetsDefinition]],
    backfill_data: AssetBackfillData,
    fail_asset_partitions: Iterable[AssetKeyPartitionKey],
    instance: DagsterInstance,
) -> AssetBackfillData:
    iteration_count = 0
    instance = instance or DagsterInstance.ephemeral()
    backfill_id = "backfillid_x"

    # assert each asset partition only targeted once
    requested_asset_partitions: Set[AssetKeyPartitionKey] = set()

    fail_and_downstream_asset_partitions = asset_graph.bfs_filter_asset_partitions(
        instance,
        lambda _a, _b: True,
        fail_asset_partitions,
        evaluation_time=backfill_data.backfill_start_time,
    )

    while not backfill_data.is_complete():
        iteration_count += 1
        result1 = execute_asset_backfill_iteration_consume_generator(
            backfill_id=backfill_id,
            asset_backfill_data=backfill_data,
            asset_graph=asset_graph,
            instance=instance,
        )
        # iteration_count += 1
        assert result1.backfill_data != backfill_data

        # if nothing changes, nothing should happen in the iteration
        result2 = execute_asset_backfill_iteration_consume_generator(
            backfill_id=backfill_id,
            asset_backfill_data=result1.backfill_data,
            asset_graph=asset_graph,
            instance=instance,
        )
        assert result2.backfill_data == result1.backfill_data
        assert result2.run_requests == []

        backfill_data = result2.backfill_data

        for asset_partition in backfill_data.materialized_subset.iterate_asset_partitions():
            assert asset_partition not in fail_and_downstream_asset_partitions

            for parent_asset_partition in asset_graph.get_parents_partitions(
                instance,
                backfill_data.backfill_start_time,
                *asset_partition,
            ):
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

            for asset_key in asset_keys:
                asset_partition = AssetKeyPartitionKey(asset_key, run_request.partition_key)
                assert (
                    asset_partition not in requested_asset_partitions
                ), f"{asset_partition} requested twice. Requested: {requested_asset_partitions}."
                requested_asset_partitions.add(asset_partition)

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
                tags=run_request.tags,
            )

        assert iteration_count <= len(requested_asset_partitions) + 1

    assert (
        len(requested_asset_partitions | fail_and_downstream_asset_partitions)
        == backfill_data.target_subset.num_partitions_and_non_partitioned_assets
    )
    return backfill_data


def external_asset_graph_from_assets_by_repo_name(
    assets_by_repo_name: Mapping[str, Sequence[AssetsDefinition]],
) -> ExternalAssetGraph:
    from_repository_handles_and_external_asset_nodes = []

    for repo_name, assets in assets_by_repo_name.items():
        repo = Definitions(assets=assets).get_repository_def()

        external_asset_nodes = external_asset_graph_from_defs(
            repo.get_all_jobs(), source_assets_by_key=repo.source_assets_by_key
        )
        repo_handle = MagicMock(repository_name=repo_name)
        from_repository_handles_and_external_asset_nodes.extend(
            [(repo_handle, asset_node) for asset_node in external_asset_nodes]
        )

    return ExternalAssetGraph.from_repository_handles_and_external_asset_nodes(
        from_repository_handles_and_external_asset_nodes
    )


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
            r' "9fd02488f5859c7b2fb25f77f2a25dce938897d3"},'
            r' "partitions_def_class_names_by_asset_key": {"daily_asset":'
            r' "TimeWindowPartitionsDefinition"}, "non_partitioned_asset_keys": []},'
            r' "latest_storage_id": 235, "serialized_requested_subset":'
            r' {"partitions_subsets_by_asset_key": {"daily_asset": "{\"version\": 1,'
            r' \"time_windows\": [[1571356800.0, 1571529600.0]], \"num_partitions\": 2}"},'
            r' "serializable_partitions_def_ids_by_asset_key": {"daily_asset":'
            r' "9fd02488f5859c7b2fb25f77f2a25dce938897d3"},'
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

    @asset(partitions_def=time_window_partitions)
    def daily_asset():
        return 1

    keys = ["a", "b", "c", "d", "e", "f"]
    static_partitions = StaticPartitionsDefinition(keys)

    @asset(partitions_def=static_partitions)
    def static_asset():
        return 1

    asset_graph = external_asset_graph_from_assets_by_repo_name(
        {"repo": [daily_asset, static_asset]}
    )

    assert AssetBackfillData.is_valid_serialization(time_window_serialization, asset_graph) is True
    assert AssetBackfillData.is_valid_serialization(static_serialization, asset_graph) is True

    daily_asset._partitions_def = static_partitions  # noqa: SLF001
    static_asset._partitions_def = time_window_partitions  # noqa: SLF001

    asset_graph = external_asset_graph_from_assets_by_repo_name(
        {"repo": [daily_asset, static_asset]}
    )

    assert AssetBackfillData.is_valid_serialization(time_window_serialization, asset_graph) is False
    assert AssetBackfillData.is_valid_serialization(static_serialization, asset_graph) is False

    static_asset._partitions_def = StaticPartitionsDefinition(keys + ["x"])  # noqa: SLF001

    asset_graph = external_asset_graph_from_assets_by_repo_name(
        {"repo": [daily_asset, static_asset]}
    )

    assert AssetBackfillData.is_valid_serialization(static_serialization, asset_graph) is True


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
        backfill_start_time=pendulum.now("UTC"),
    )

    completed_backfill_data = run_backfill_to_completion(
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

    counts = completed_backfill_data.get_backfill_status_per_asset_key()

    assert counts[0].asset_key == unpartitioned_upstream_of_partitioned.key
    assert counts[0].backfill_status == AssetBackfillStatus.MATERIALIZED

    assert counts[1].asset_key == upstream_daily_partitioned_asset.key
    assert counts[1].partitions_counts_by_status[AssetBackfillStatus.MATERIALIZED] == 0
    assert counts[1].partitions_counts_by_status[AssetBackfillStatus.FAILED] == 1
    assert counts[1].partitions_counts_by_status[AssetBackfillStatus.IN_PROGRESS] == 0
    assert counts[1].num_targeted_partitions == 1

    assert counts[2].asset_key == downstream_weekly_partitioned_asset.key
    assert counts[2].partitions_counts_by_status[AssetBackfillStatus.MATERIALIZED] == 0
    assert counts[2].partitions_counts_by_status[AssetBackfillStatus.FAILED] == 1
    assert counts[2].partitions_counts_by_status[AssetBackfillStatus.IN_PROGRESS] == 0
    assert counts[2].num_targeted_partitions == 1


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
        backfill_start_time=pendulum.datetime(2023, 1, 9, 0, 0, 0),
    )

    target_subset = backfill_data.target_subset
    assert target_subset.get_partitions_subset(
        upstream_hourly_partitioned_asset.key
    ).get_partition_keys() == ["2023-01-09-00:00"]
    assert len(target_subset.get_partitions_subset(downstream_daily_partitioned_asset.key)) == 0
