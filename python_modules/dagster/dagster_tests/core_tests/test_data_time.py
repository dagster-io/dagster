import datetime
import random
from collections import defaultdict
from typing import List, NamedTuple, Optional

import mock
import pendulum
import pytest
from dagster import (
    AssetKey,
    AssetOut,
    AssetSelection,
    DagsterEventType,
    DagsterInstance,
    Output,
    asset,
    multi_asset,
    repository,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_layer import build_asset_selection_job
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.decorators.source_asset_decorator import observable_source_asset
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.materialize import materialize_to_memory
from dagster._core.definitions.observe import observe
from dagster._core.definitions.time_window_partitions import DailyPartitionsDefinition
from dagster._core.event_api import EventRecordsFilter
from dagster._seven.compat.pendulum import create_pendulum_time, pendulum_freeze_time
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer


@pytest.mark.parametrize("ignore_asset_tags", [True, False])
@pytest.mark.parametrize(
    ["runs_to_expected_data_times_index"],
    [
        (
            [
                # EXPLANATION FOR THIS FORMAT:
                #
                # run assets a,c,e
                # expect assets a,c,e to have upstream materialization times:
                #    {AssetKey("a"): <timestamp of a's asset materialization in run 0 (this run)>}
                ("ace", {"ace": {"a": 0}}),
                #
                # run assets a,b,d
                # expect assets a,b to have upstream materialization times:
                #    {AssetKey("a"): <timestamp of a's asset materialization in run 1 (this run)>}
                # expect assets c,d,e to have upstream materialization times:
                #    {AssetKey("a"): <timestamp of a's asset materialization in run 0 (previous run)>}
                ("abd", {"ab": {"a": 1}, "cde": {"a": 0}}),
                ("ac", {"ac": {"a": 2}, "b": {"a": 1}, "ed": {"a": 0}}),
                ("e", {"ace": {"a": 2}, "b": {"a": 1}, "d": {"a": 0}}),
            ],
        ),
        (
            [
                ("abcf", {"abc": {"a": 0}}),
                ("bd", {"abd": {"a": 0}}),
                ("a", {"a": {"a": 2}, "bcd": {"a": 0}}),
                ("f", {"a": {"a": 2}, "bcdf": {"a": 0}}),
                ("bdf", {"ab": {"a": 2}, "cdf": {"a": 0}}),
                ("c", {"abc": {"a": 2}, "df": {"a": 0}}),
                ("df", {"abcdf": {"a": 2}}),
            ],
        ),
    ],
)
def test_calculate_data_time_unpartitioned(ignore_asset_tags, runs_to_expected_data_times_index):
    r"""A = B = D = F
     \\  //
       C = E
    B,C,D share an op.
    """

    @asset
    def a():
        return 1

    @multi_asset(
        deps=[AssetKey("a")],
        outs={
            "b": AssetOut(is_required=False),
            "c": AssetOut(is_required=False),
            "d": AssetOut(is_required=False),
        },
        can_subset=True,
        internal_asset_deps={
            "b": {AssetKey("a")},
            "c": {AssetKey("a")},
            "d": {AssetKey("b"), AssetKey("c")},
        },
    )
    def bcd(context):
        for output_name in sorted(context.op_execution_context.selected_output_names):
            yield Output(output_name, output_name)

    @asset(deps=[AssetKey("c")])
    def e():
        return 1

    @asset(deps=[AssetKey("d")])
    def f():
        return 1

    all_assets = [a, bcd, e, f]

    asset_graph = AssetGraph.from_assets(all_assets)

    with DagsterInstance.ephemeral() as instance:
        # mapping from asset key to a mapping of materialization timestamp to run index
        materialization_times_index = defaultdict(dict)

        for idx, (to_materialize, expected_index_mapping) in enumerate(
            runs_to_expected_data_times_index
        ):
            # materialize selected assets
            result = build_asset_selection_job(
                "materialize_job",
                assets=all_assets,
                asset_selection=AssetSelection.keys(*(AssetKey(c) for c in to_materialize)).resolve(
                    all_assets
                ),
            ).execute_in_process(instance=instance)

            assert result.success

            # rebuild the data time queryer after each run
            data_time_queryer = CachingDataTimeResolver(
                instance_queryer=CachingInstanceQueryer(instance, asset_graph)
            )

            # build mapping of expected timestamps
            for entry in instance.all_logs(
                result.run_id, of_type=DagsterEventType.ASSET_MATERIALIZATION
            ):
                asset_key = entry.dagster_event.event_specific_data.materialization.asset_key
                materialization_times_index[asset_key][idx] = datetime.datetime.fromtimestamp(
                    entry.timestamp, tz=datetime.timezone.utc
                )

            for asset_keys, expected_data_times in expected_index_mapping.items():
                for ak in asset_keys:
                    latest_asset_record = data_time_queryer.instance_queryer.get_latest_materialization_or_observation_record(
                        AssetKeyPartitionKey(AssetKey(ak))
                    )
                    if ignore_asset_tags:
                        # simulate an environment where materialization tags were not populated
                        with mock.patch(
                            "dagster.AssetMaterialization.tags", new_callable=mock.PropertyMock
                        ) as tags_property:
                            tags_property.return_value = None
                            upstream_data_times = data_time_queryer.get_data_time_by_key_for_record(
                                record=latest_asset_record,
                            )
                    else:
                        upstream_data_times = data_time_queryer.get_data_time_by_key_for_record(
                            record=latest_asset_record,
                        )
                    assert upstream_data_times == {
                        AssetKey(k): materialization_times_index[AssetKey(k)][v]
                        for k, v in expected_data_times.items()
                    }


@asset(partitions_def=DailyPartitionsDefinition(start_date="2023-01-01"))
def partitioned_asset():
    pass


@asset(deps=[AssetKey("partitioned_asset")])
def unpartitioned_asset():
    pass


@repository
def partition_repo():
    return [partitioned_asset, unpartitioned_asset]


def _materialize_partitions(instance, partitions):
    for partition in partitions:
        result = materialize_to_memory(
            assets=[partitioned_asset],
            instance=instance,
            partition_key=partition,
        )
        assert result.success


def _get_record(instance):
    result = materialize_to_memory(
        assets=[unpartitioned_asset, *partitioned_asset.to_source_assets()],
        instance=instance,
    )
    assert result.success
    return next(
        iter(
            instance.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=AssetKey("unpartitioned_asset"),
                ),
                ascending=False,
                limit=1,
            )
        )
    )


class PartitionedDataTimeScenario(NamedTuple):
    before_partitions: List[str]
    after_partitions: List[str]
    expected_time: Optional[datetime.datetime]


scenarios = {
    "empty": PartitionedDataTimeScenario(
        before_partitions=[],
        after_partitions=[],
        expected_time=None,
    ),
    "first_missing": PartitionedDataTimeScenario(
        before_partitions=["2023-01-02", "2023-01-03"],
        after_partitions=[],
        expected_time=None,
    ),
    "some_filled": PartitionedDataTimeScenario(
        before_partitions=["2023-01-01", "2023-01-02", "2023-01-03"],
        after_partitions=[],
        expected_time=datetime.datetime(2023, 1, 4, tzinfo=datetime.timezone.utc),
    ),
    "middle_missing": PartitionedDataTimeScenario(
        # 2023-01-04 is missing
        before_partitions=["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-05", "2023-01-06"],
        after_partitions=[],
        expected_time=datetime.datetime(2023, 1, 4, tzinfo=datetime.timezone.utc),
    ),
    "new_duplicate_partitions": PartitionedDataTimeScenario(
        before_partitions=["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
        after_partitions=["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-03"],
        expected_time=datetime.datetime(2023, 1, 5, tzinfo=datetime.timezone.utc),
    ),
    "new_duplicate_partitions2": PartitionedDataTimeScenario(
        before_partitions=["2023-01-01", "2023-01-02"],
        after_partitions=["2023-01-01", "2023-01-01", "2023-01-01", "2023-01-01"],
        expected_time=datetime.datetime(2023, 1, 3, tzinfo=datetime.timezone.utc),
    ),
    "net_new_partitions": PartitionedDataTimeScenario(
        before_partitions=["2023-01-01", "2023-01-02", "2023-01-03"],
        after_partitions=["2023-01-04", "2023-01-05", "2023-01-06"],
        expected_time=datetime.datetime(2023, 1, 4, tzinfo=datetime.timezone.utc),
    ),
    "net_new_partitions2": PartitionedDataTimeScenario(
        before_partitions=["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
        after_partitions=[
            "2023-01-01",
            "2023-01-01",
            "2023-01-01",
            "2023-01-06",
            "2023-01-06",
            "2023-01-06",
        ],
        expected_time=datetime.datetime(2023, 1, 5, tzinfo=datetime.timezone.utc),
    ),
    "net_new_partitions_with_middle_missing": PartitionedDataTimeScenario(
        before_partitions=["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-05", "2023-01-06"],
        after_partitions=["2023-01-04", "2023-01-04"],
        expected_time=datetime.datetime(2023, 1, 4, tzinfo=datetime.timezone.utc),
    ),
}


@pytest.mark.parametrize("scenario", list(scenarios.values()), ids=list(scenarios.keys()))
def test_partitioned_data_time(scenario):
    with DagsterInstance.ephemeral() as instance, pendulum_freeze_time(
        create_pendulum_time(2023, 1, 7)
    ):
        _materialize_partitions(instance, scenario.before_partitions)
        record = _get_record(instance=instance)
        _materialize_partitions(instance, scenario.after_partitions)
        data_time_queryer = CachingDataTimeResolver(
            instance_queryer=CachingInstanceQueryer(instance, partition_repo.asset_graph),
        )

        data_time = data_time_queryer.get_data_time_by_key_for_record(record=record)

        if scenario.expected_time is None:
            assert data_time == {} or data_time == {AssetKey("partitioned_asset"): None}
        else:
            assert data_time == {AssetKey("partitioned_asset"): scenario.expected_time}


@observable_source_asset
def sA():
    return DataVersion(str(random.random()))


@observable_source_asset
def sB():
    return DataVersion(str(random.random()))


@asset(deps=[sA])
def A():
    pass


@asset(deps=[sB])
def B():
    pass


@asset(deps=[B])
def B2():
    pass


@asset(deps=[sA, sB])
def AB():
    pass


@repository
def versioned_repo():
    return [sA, sB, A, B, AB, B2]


def observe_sources(*args):
    def observe_sources_fn(*, instance, times_by_key, **kwargs):
        for arg in args:
            key = AssetKey(arg)
            observe(assets=[versioned_repo.asset_graph.get(key).assets_def], instance=instance)
            latest_record = instance.get_latest_data_version_record(key, is_source=True)
            latest_timestamp = latest_record.timestamp
            times_by_key[key].append(
                datetime.datetime.fromtimestamp(latest_timestamp, tz=datetime.timezone.utc)
            )

    return observe_sources_fn


def run_assets(*args):
    def run_assets_fn(*, instance, **kwargs):
        assets = [versioned_repo.asset_graph.get(AssetKey(arg)).assets_def for arg in args]
        materialize_to_memory(assets=assets, instance=instance)

    return run_assets_fn


def assert_has_current_time(key_str):
    def assert_has_current_time_fn(*, instance, evaluation_time, **kwargs):
        resolver = CachingDataTimeResolver(
            instance_queryer=CachingInstanceQueryer(instance, versioned_repo.asset_graph),
        )
        data_time = resolver.get_current_data_time(AssetKey(key_str), current_time=evaluation_time)
        assert data_time == evaluation_time

    return assert_has_current_time_fn


def assert_has_index_time(key_str, source_key_str, index):
    def assert_has_index_time_fn(*, instance, times_by_key, evaluation_time, **kwargs):
        resolver = CachingDataTimeResolver(
            instance_queryer=CachingInstanceQueryer(instance, versioned_repo.asset_graph),
        )
        data_time = resolver.get_current_data_time(AssetKey(key_str), current_time=evaluation_time)
        if index is None:
            assert data_time is None
        else:
            assert data_time == times_by_key[AssetKey(source_key_str)][index]

    return assert_has_index_time_fn


timelines = {
    "basic_one_parent": [
        observe_sources("sA"),
        assert_has_index_time("A", None, None),
        # run A, make sure it knows it's current
        run_assets("A"),
        assert_has_current_time("A"),
        # new version of sA, A now points at the timestamp of that new version
        observe_sources("sA"),
        assert_has_index_time("A", "sA", 1),
        # run A again, make sure it knows it's current
        run_assets("A"),
        assert_has_current_time("A"),
    ],
    "basic_two_parents": [
        observe_sources("sA", "sB"),
        assert_has_index_time("AB", None, None),
        # run AB, make sure it knows it's current
        run_assets("AB"),
        assert_has_current_time("AB"),
        # new version of sA, AB now points at the timestamp of that new version
        observe_sources("sA"),
        assert_has_index_time("AB", "sA", 1),
        # run AB again, make sure it knows it's current
        run_assets("AB"),
        assert_has_current_time("AB"),
        # new version of sA and sB, AB now points at the timestamp of the older new version
        observe_sources("sA"),
        assert_has_index_time("AB", "sA", 2),
        observe_sources("sB"),
        assert_has_index_time("AB", "sA", 2),
        # run AB again, make sure it knows it's current
        run_assets("AB"),
        assert_has_current_time("AB"),
    ],
    "chained": [
        observe_sources("sA", "sB"),
        run_assets("B"),
        assert_has_current_time("B"),
        run_assets("B2"),
        assert_has_current_time("B2"),
        observe_sources("sA"),
        assert_has_current_time("B"),
        assert_has_current_time("B2"),
        observe_sources("sB"),
        assert_has_index_time("B", "sB", 1),
        assert_has_index_time("B2", "sB", 1),
        run_assets("B"),
        assert_has_current_time("B"),
        assert_has_index_time("B2", "sB", 1),
        run_assets("B2"),
        assert_has_current_time("B2"),
    ],
    "chained_multiple_observations": [
        observe_sources("sB"),
        run_assets("B", "B2"),
        assert_has_current_time("B"),
        assert_has_current_time("B2"),
        # after getting current, get a bunch of new versions
        observe_sources("sB"),
        observe_sources("sB"),
        observe_sources("sB"),
        observe_sources("sB"),
        observe_sources("sB"),
        # should point to the time at which the version changed
        assert_has_index_time("B", "sB", 1),
        assert_has_index_time("B2", "sB", 1),
        # run B, make sure it knows it's current
        run_assets("B"),
        assert_has_current_time("B"),
        # after getting current, get a bunch of new versions
        observe_sources("sB"),
        observe_sources("sB"),
        observe_sources("sB"),
        observe_sources("sB"),
        observe_sources("sB"),
        # should point to the time at which the version changed
        assert_has_index_time("B", "sB", 6),
        assert_has_index_time("B2", "sB", 1),
    ],
}


@pytest.mark.parametrize("timeline", list(timelines.values()), ids=list(timelines.keys()))
def test_non_volatile_data_time(timeline):
    with DagsterInstance.ephemeral() as instance:
        times_by_key = defaultdict(list)
        for action in timeline:
            action(
                instance=instance,
                times_by_key=times_by_key,
                evaluation_time=pendulum.now("UTC"),
            )
