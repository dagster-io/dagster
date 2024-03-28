from datetime import datetime
from typing import Sequence

import pytest
from dagster import (
    AssetKey,
    AssetOut,
    AssetsDefinition,
    DailyPartitionsDefinition,
    GraphOut,
    HourlyPartitionsDefinition,
    Out,
    StaticPartitionsDefinition,
    define_asset_job,
    graph,
    graph_asset,
    graph_multi_asset,
    op,
)
from dagster._check import ParameterCheckError
from dagster._core.definitions import AssetIn, SourceAsset, asset, multi_asset
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_spec import AssetExecutionType, AssetSpec
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.external_asset import external_assets_from_specs
from dagster._core.definitions.metadata import MetadataValue, TextMetadataValue, normalize_metadata
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.partition import ScheduleType
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._core.definitions.utils import DEFAULT_GROUP_NAME
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.remote_representation.external_data import (
    AssetChildEdgeSnap,
    AssetNodeSnap,
    AssetParentEdgeSnap,
    MultiPartitionsSnap,
    SensorSnap,
    TargetSnap,
    TimeWindowPartitionsSnap,
    asset_node_snaps_from_repo,
)
from dagster._serdes import deserialize_value, serialize_value, unpack_value
from dagster._time import create_datetime, get_timezone
from dagster._utils.partitions import DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE


def _get_asset_node_snaps_from_definitions(defs: Definitions) -> Sequence[AssetNodeSnap]:
    repo = defs.get_repository_def()
    return sorted(asset_node_snaps_from_repo(repo), key=lambda n: n.asset_key)


def test_single_asset_job():
    @asset(description="hullo")
    def asset1():
        return 1

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(
            assets=[asset1],
            jobs=[define_asset_job("assets_job", [asset1])],
        )
    )

    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey("asset1"),
            parent_edges=[],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="asset1",
            graph_name=None,
            op_names=["asset1"],
            description="hullo",
            node_definition_name="asset1",
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
        )
    ]


def test_asset_with_default_backfill_policy():
    @asset(description="hullo")
    def asset1():
        return 1

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(
            assets=[asset1],
            jobs=[define_asset_job("assets_job", [asset1])],
        )
    )

    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey("asset1"),
            parent_edges=[],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="asset1",
            graph_name=None,
            op_names=["asset1"],
            description="hullo",
            node_definition_name="asset1",
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
            backfill_policy=None,
        ),
    ]


def test_asset_with_single_run_backfill_policy():
    @asset(description="hullo_single_run", backfill_policy=BackfillPolicy.single_run())
    def asset1():
        return 1

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(
            assets=[asset1],
            jobs=[define_asset_job("assets_job", [asset1])],
        )
    )

    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey("asset1"),
            parent_edges=[],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="asset1",
            graph_name=None,
            op_names=["asset1"],
            description="hullo_single_run",
            node_definition_name="asset1",
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
            backfill_policy=BackfillPolicy.single_run(),
        )
    ]

    assert (
        deserialize_value(serialize_value(asset_node_snaps[0]), AssetNodeSnap)
        == asset_node_snaps[0]
    )


def test_asset_with_multi_run_backfill_policy():
    partitions_snap = TimeWindowPartitionsSnap(
        cron_schedule="5 13 * * 0",
        start=create_datetime(year=2022, month=5, day=5, tz="US/Central").timestamp(),
        timezone="US/Central",
        fmt=DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE,
        end_offset=1,
    )
    partitions_def = partitions_snap.get_partitions_definition()

    @asset(
        description="hullo_ten_partitions_per_run",
        partitions_def=partitions_def,
        backfill_policy=BackfillPolicy.multi_run(10),
    )
    def asset1():
        return 1

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(
            assets=[asset1],
            jobs=[define_asset_job("assets_job", [asset1])],
        )
    )

    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey("asset1"),
            parent_edges=[],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="asset1",
            graph_name=None,
            op_names=["asset1"],
            description="hullo_ten_partitions_per_run",
            node_definition_name="asset1",
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
            partitions=partitions_snap,
            backfill_policy=BackfillPolicy.multi_run(10),
        )
    ]


def test_non_partitioned_asset_with_multi_run_backfill_policy():
    with pytest.raises(
        ParameterCheckError, match="Non partitioned asset can only have single run backfill policy"
    ):

        @asset(description="hullo", backfill_policy=BackfillPolicy.multi_run(10))
        def asset1():
            return 1


def test_asset_with_group_name():
    @asset(group_name="group1")
    def asset1():
        return 1

    asset_node_snaps = _get_asset_node_snaps_from_definitions(Definitions(assets=[asset1]))

    assert asset_node_snaps[0].group_name == "group1"


def test_asset_missing_group_name():
    @asset
    def asset1():
        return 1

    asset_node_snaps = _get_asset_node_snaps_from_definitions(Definitions(assets=[asset1]))

    assert asset_node_snaps[0].group_name == DEFAULT_GROUP_NAME


def test_asset_invalid_group_name():
    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(group_name="group/with/slashes")
        def asset2():
            return 1

    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(group_name="group.with.dots")
        def asset3():
            return 1


def test_two_asset_job():
    @asset
    def asset1():
        return 1

    @asset
    def asset2(asset1):
        assert asset1 == 1

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(
            assets=[asset1, asset2],
            jobs=[define_asset_job("assets_job", [asset1, asset2])],
        ),
    )

    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey("asset1"),
            parent_edges=[],
            child_edges=[AssetChildEdgeSnap(child_asset_key=AssetKey("asset2"))],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="asset1",
            node_definition_name="asset1",
            graph_name=None,
            op_names=["asset1"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey("asset2"),
            parent_edges=[AssetParentEdgeSnap(parent_asset_key=AssetKey("asset1"))],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="asset2",
            node_definition_name="asset2",
            graph_name=None,
            op_names=["asset2"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_input_name_matches_output_name():
    not_result = SourceAsset(key=AssetKey("not_result"), description=None)

    @asset(ins={"result": AssetIn(key=AssetKey("not_result"))})
    def something(result):
        pass

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(
            assets=[not_result, something],
            jobs=[define_asset_job("assets_job", [something])],
        )
    )

    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey("not_result"),
            parent_edges=[],
            child_edges=[AssetChildEdgeSnap(child_asset_key=AssetKey("something"))],
            execution_type=AssetExecutionType.UNEXECUTABLE,
            job_names=[],
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey("something"),
            parent_edges=[AssetParentEdgeSnap(parent_asset_key=AssetKey("not_result"))],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="something",
            node_definition_name="something",
            graph_name=None,
            op_names=["something"],
            output_name="result",
            job_names=["__ASSET_JOB", "assets_job"],
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_assets_excluded_from_subset_not_in_job():
    out_metadata = {"a": 1, "b": "c", "d": None}

    @multi_asset(
        outs={"a": AssetOut(metadata=out_metadata), "b": AssetOut(), "c": AssetOut()},
        can_subset=True,
    )
    def abc():
        pass

    @asset
    def a2(a):
        return a

    @asset
    def c2(c):
        return c

    all_assets = [abc, a2, c2]
    as_job = define_asset_job("as_job", selection="a*").resolve(
        asset_graph=AssetGraph.from_assets(all_assets)
    )
    cs_job = define_asset_job("cs_job", selection="*c2").resolve(
        asset_graph=AssetGraph.from_assets(all_assets)
    )

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(assets=[abc, a2, c2], jobs=[as_job, cs_job])
    )

    assert (
        AssetNodeSnap(
            asset_key=AssetKey("a"),
            parent_edges=[],
            child_edges=[AssetChildEdgeSnap(child_asset_key=AssetKey("a2"))],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="abc",
            node_definition_name="abc",
            graph_name=None,
            op_names=["abc"],
            job_names=["__ASSET_JOB", "as_job"],  # the important line
            output_name="a",
            group_name=DEFAULT_GROUP_NAME,
            metadata=normalize_metadata(out_metadata, allow_invalid=True),
        )
        in asset_node_snaps
    )

    assert (
        AssetNodeSnap(
            asset_key=AssetKey("c"),
            parent_edges=[],
            child_edges=[AssetChildEdgeSnap(child_asset_key=AssetKey("c2"))],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="abc",
            node_definition_name="abc",
            graph_name=None,
            op_names=["abc"],
            job_names=["__ASSET_JOB", "cs_job"],  # the important line
            output_name="c",
            group_name=DEFAULT_GROUP_NAME,
        )
        in asset_node_snaps
    )


def test_two_downstream_assets_job():
    @asset
    def asset1():
        return 1

    @asset
    def asset2_a(asset1):
        assert asset1 == 1

    @asset
    def asset2_b(asset1):
        assert asset1 == 1

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(
            assets=[asset1, asset2_a, asset2_b],
            jobs=[define_asset_job("assets_job", [asset1, asset2_a, asset2_b])],
        )
    )

    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey("asset1"),
            parent_edges=[],
            child_edges=[
                AssetChildEdgeSnap(child_asset_key=AssetKey("asset2_a")),
                AssetChildEdgeSnap(child_asset_key=AssetKey("asset2_b")),
            ],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="asset1",
            node_definition_name="asset1",
            graph_name=None,
            op_names=["asset1"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey("asset2_a"),
            parent_edges=[AssetParentEdgeSnap(parent_asset_key=AssetKey("asset1"))],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="asset2_a",
            node_definition_name="asset2_a",
            graph_name=None,
            op_names=["asset2_a"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey("asset2_b"),
            parent_edges=[AssetParentEdgeSnap(parent_asset_key=AssetKey("asset1"))],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="asset2_b",
            node_definition_name="asset2_b",
            graph_name=None,
            op_names=["asset2_b"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_cross_job_asset_dependency():
    @asset
    def asset1():
        return 1

    @asset
    def asset2(asset1):
        assert asset1 == 1

    assets_job1 = define_asset_job("assets_job1", [asset1])
    assets_job2 = define_asset_job("assets_job2", [asset2])
    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(assets=[asset1, asset2], jobs=[assets_job1, assets_job2])
    )

    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey("asset1"),
            parent_edges=[],
            child_edges=[AssetChildEdgeSnap(child_asset_key=AssetKey("asset2"))],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="asset1",
            node_definition_name="asset1",
            graph_name=None,
            op_names=["asset1"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job1"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey("asset2"),
            parent_edges=[AssetParentEdgeSnap(parent_asset_key=AssetKey("asset1"))],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="asset2",
            node_definition_name="asset2",
            graph_name=None,
            op_names=["asset2"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job2"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_same_asset_in_multiple_jobs():
    @asset
    def asset1():
        return 1

    job1 = define_asset_job("job1", [asset1])
    job2 = define_asset_job("job2", [asset1])

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(
            assets=[asset1],
            jobs=[job1, job2],
        )
    )

    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey("asset1"),
            parent_edges=[],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="asset1",
            node_definition_name="asset1",
            graph_name=None,
            op_names=["asset1"],
            description=None,
            job_names=["__ASSET_JOB", "job1", "job2"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_basic_multi_asset():
    @multi_asset(
        outs={
            f"out{i}": AssetOut(description=f"foo: {i}", key=AssetKey(f"asset{i}"))
            for i in range(10)
        }
    )
    def assets():
        """Some docstring for this operation."""
        pass

    assets_job = define_asset_job("assets_job", [assets])

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(assets=[assets], jobs=[assets_job])
    )

    execution_set_identifier = assets.unique_id

    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey(f"asset{i}"),
            parent_edges=[],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="assets",
            node_definition_name="assets",
            graph_name=None,
            op_names=["assets"],
            description=f"foo: {i}",
            job_names=["__ASSET_JOB", "assets_job"],
            output_name=f"out{i}",
            group_name=DEFAULT_GROUP_NAME,
            execution_set_identifier=execution_set_identifier,
        )
        for i in range(10)
    ]


def test_inter_op_dependency():
    @asset
    def in1():
        pass

    @asset
    def in2():
        pass

    @asset
    def downstream(only_in, mixed, only_out):
        pass

    @multi_asset(
        outs={"only_in": AssetOut(), "mixed": AssetOut(), "only_out": AssetOut()},
        internal_asset_deps={
            "only_in": {AssetKey("in1"), AssetKey("in2")},
            "mixed": {AssetKey("in1"), AssetKey("only_in")},
            "only_out": {AssetKey("only_in"), AssetKey("mixed")},
        },
        can_subset=True,
    )
    def assets(in1, in2):
        pass

    subset_job = define_asset_job("subset_job", selection="mixed").resolve(
        asset_graph=AssetGraph.from_assets([in1, in2, assets, downstream]),
    )
    all_assets_job = define_asset_job("assets_job", [in1, in2, assets, downstream])

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(
            assets=[in1, in2, assets, downstream],
            jobs=[subset_job, all_assets_job],
            # jobs=[all_assets_job, subset_job],
        )
    )
    # sort so that test is deterministic

    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey(["downstream"]),
            parent_edges=[
                AssetParentEdgeSnap(parent_asset_key=AssetKey(["mixed"])),
                AssetParentEdgeSnap(parent_asset_key=AssetKey(["only_in"])),
                AssetParentEdgeSnap(parent_asset_key=AssetKey(["only_out"])),
            ],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="downstream",
            node_definition_name="downstream",
            graph_name=None,
            op_names=["downstream"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            metadata={},
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey(["in1"]),
            parent_edges=[],
            child_edges=[
                AssetChildEdgeSnap(child_asset_key=AssetKey(["mixed"])),
                AssetChildEdgeSnap(child_asset_key=AssetKey(["only_in"])),
            ],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="in1",
            node_definition_name="in1",
            graph_name=None,
            op_names=["in1"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            metadata={},
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey(["in2"]),
            parent_edges=[],
            child_edges=[AssetChildEdgeSnap(child_asset_key=AssetKey(["only_in"]))],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="in2",
            node_definition_name="in2",
            graph_name=None,
            op_names=["in2"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            metadata={},
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey(["mixed"]),
            parent_edges=[
                AssetParentEdgeSnap(parent_asset_key=AssetKey(["in1"])),
                AssetParentEdgeSnap(parent_asset_key=AssetKey(["only_in"])),
            ],
            child_edges=[
                AssetChildEdgeSnap(child_asset_key=AssetKey(["downstream"])),
                AssetChildEdgeSnap(child_asset_key=AssetKey(["only_out"])),
            ],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="assets",
            node_definition_name="assets",
            graph_name=None,
            op_names=["assets"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job", "subset_job"],
            output_name="mixed",
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey(["only_in"]),
            parent_edges=[
                AssetParentEdgeSnap(parent_asset_key=AssetKey(["in1"])),
                AssetParentEdgeSnap(parent_asset_key=AssetKey(["in2"])),
            ],
            child_edges=[
                AssetChildEdgeSnap(child_asset_key=AssetKey(["downstream"])),
                AssetChildEdgeSnap(child_asset_key=AssetKey(["mixed"])),
                AssetChildEdgeSnap(child_asset_key=AssetKey(["only_out"])),
            ],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="assets",
            node_definition_name="assets",
            graph_name=None,
            op_names=["assets"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="only_in",
            metadata={},
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey(["only_out"]),
            parent_edges=[
                AssetParentEdgeSnap(parent_asset_key=AssetKey(["mixed"])),
                AssetParentEdgeSnap(parent_asset_key=AssetKey(["only_in"])),
            ],
            child_edges=[
                AssetChildEdgeSnap(child_asset_key=AssetKey(["downstream"])),
            ],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="assets",
            node_definition_name="assets",
            graph_name=None,
            op_names=["assets"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="only_out",
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_source_asset_with_op() -> None:
    foo = SourceAsset(key=AssetKey("foo"), description=None)

    @asset
    def bar(foo):
        pass

    assets_job = define_asset_job("assets_job", [bar])

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(assets=[foo, bar], jobs=[assets_job])
    )
    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey("bar"),
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="bar",
            node_definition_name="bar",
            graph_name=None,
            op_names=["bar"],
            description=None,
            parent_edges=[AssetParentEdgeSnap(parent_asset_key=AssetKey("foo"))],
            child_edges=[],
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey("foo"),
            execution_type=AssetExecutionType.UNEXECUTABLE,
            description=None,
            parent_edges=[],
            child_edges=[AssetChildEdgeSnap(child_asset_key=AssetKey("bar"))],
            job_names=[],
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_unused_source_asset():
    foo = SourceAsset(key=AssetKey("foo"), description="abc")
    bar = SourceAsset(key=AssetKey("bar"), description="def")

    asset_node_snaps = _get_asset_node_snaps_from_definitions(Definitions(assets=[foo, bar]))
    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey("bar"),
            description="def",
            parent_edges=[],
            child_edges=[],
            execution_type=AssetExecutionType.UNEXECUTABLE,
            job_names=[],
            group_name=DEFAULT_GROUP_NAME,
            is_source=True,
        ),
        AssetNodeSnap(
            asset_key=AssetKey("foo"),
            description="abc",
            parent_edges=[],
            child_edges=[],
            execution_type=AssetExecutionType.UNEXECUTABLE,
            job_names=[],
            group_name=DEFAULT_GROUP_NAME,
            is_source=True,
        ),
    ]


def test_used_source_asset():
    bar = SourceAsset(key=AssetKey("bar"), description="def", tags={"biz": "baz"})

    @asset
    def foo(bar):
        assert bar

    job1 = define_asset_job("job1", [foo])

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(
            assets=[bar, foo],
            jobs=[job1],
        )
    )
    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey("bar"),
            description="def",
            parent_edges=[],
            child_edges=[AssetChildEdgeSnap(child_asset_key=AssetKey(["foo"]))],
            execution_type=AssetExecutionType.UNEXECUTABLE,
            job_names=[],
            group_name=DEFAULT_GROUP_NAME,
            is_source=True,
            tags={"biz": "baz"},
        ),
        AssetNodeSnap(
            asset_key=AssetKey("foo"),
            op_name="foo",
            node_definition_name="foo",
            graph_name=None,
            op_names=["foo"],
            description=None,
            parent_edges=[AssetParentEdgeSnap(parent_asset_key=AssetKey(["bar"]))],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            job_names=["__ASSET_JOB", "job1"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_graph_output_metadata_and_description() -> None:
    asset_metadata = {
        "int": 1,
        "string": "baz",
        "some_list": [1, 2, 3],
        "none": None,
        "md": MetadataValue.md("#123"),
        "float": MetadataValue.float(1.23),
        "_asd_123_sdas": MetadataValue.python_artifact(MetadataValue),
    }

    out_metadata = {
        "out_none": None,
        "out_list": [1, 2, 3],
    }

    @op(out=Out(metadata=out_metadata))
    def add_one(i):
        return i + 1

    @graph
    def three(zero):
        return add_one(add_one(add_one(zero)))

    @asset
    def zero():
        return 0

    three_asset = AssetsDefinition.from_graph(
        three, metadata_by_output_name={"result": asset_metadata}
    )

    assets_job = define_asset_job("assets_job", [zero, three_asset])

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(assets=[zero, three_asset], jobs=[assets_job])
    )

    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey(["three"]),
            parent_edges=[AssetParentEdgeSnap(parent_asset_key=AssetKey(["zero"]))],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="three",
            node_definition_name="add_one",
            graph_name="three",
            op_names=["three.add_one", "three.add_one_2", "three.add_one_3"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            metadata=(normalize_metadata({**asset_metadata, **out_metadata}, allow_invalid=True)),
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey(["zero"]),
            parent_edges=[],
            child_edges=[AssetChildEdgeSnap(child_asset_key=AssetKey(["three"]))],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="zero",
            node_definition_name="zero",
            graph_name=None,
            op_names=["zero"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            metadata={},
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_nasty_nested_graph_asset() -> None:
    @op
    def add_one(i):
        return i + 1

    @graph
    def add_three(i):
        return add_one(add_one(add_one(i)))

    @graph
    def add_five(i):
        return add_one(add_three(add_one(i)))

    @op
    def get_sum(a, b):
        return a + b

    @graph
    def sum_plus_one(a, b):
        return add_one(get_sum(a, b))

    @asset
    def zero():
        return 0

    @graph(out={"eight": GraphOut(), "five": GraphOut()})
    def create_eight_and_five(zero):
        return add_five(add_three(zero)), add_five(zero)

    @graph(out={"thirteen": GraphOut(), "six": GraphOut()})
    def create_thirteen_and_six(eight, five, zero):
        return add_five(eight), sum_plus_one(five, zero)

    @graph
    def create_twenty(thirteen, six):
        return sum_plus_one(thirteen, six)

    eight_and_five = AssetsDefinition(
        keys_by_input_name={"zero": AssetKey("zero")},
        keys_by_output_name={"eight": AssetKey("eight"), "five": AssetKey("five")},
        node_def=create_eight_and_five,
        can_subset=True,
    )

    thirteen_and_six = AssetsDefinition(
        keys_by_input_name={
            "eight": AssetKey("eight"),
            "five": AssetKey("five"),
            "zero": AssetKey("zero"),
        },
        keys_by_output_name={"thirteen": AssetKey("thirteen"), "six": AssetKey("six")},
        node_def=create_thirteen_and_six,
        can_subset=True,
    )

    twenty = AssetsDefinition(
        keys_by_input_name={"thirteen": AssetKey("thirteen"), "six": AssetKey("six")},
        keys_by_output_name={"result": AssetKey("twenty")},
        node_def=create_twenty,
        can_subset=True,
    )

    assets_job = define_asset_job("assets_job", [zero, eight_and_five, thirteen_and_six, twenty])

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(assets=[zero, eight_and_five, thirteen_and_six, twenty], jobs=[assets_job])
    )

    assert asset_node_snaps[-3:] == [
        AssetNodeSnap(
            asset_key=AssetKey(["thirteen"]),
            parent_edges=[
                AssetParentEdgeSnap(parent_asset_key=AssetKey(["eight"])),
                AssetParentEdgeSnap(parent_asset_key=AssetKey(["five"])),
                AssetParentEdgeSnap(parent_asset_key=AssetKey(["zero"])),
            ],
            child_edges=[AssetChildEdgeSnap(child_asset_key=AssetKey(["twenty"]))],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="create_thirteen_and_six",
            node_definition_name="add_one",
            graph_name="create_thirteen_and_six",
            op_names=[
                "create_thirteen_and_six.add_five.add_one",
                "create_thirteen_and_six.add_five.add_one_2",
                "create_thirteen_and_six.add_five.add_three.add_one",
                "create_thirteen_and_six.add_five.add_three.add_one_2",
                "create_thirteen_and_six.add_five.add_three.add_one_3",
            ],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            metadata={},
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey(["twenty"]),
            parent_edges=[
                AssetParentEdgeSnap(parent_asset_key=AssetKey(["six"])),
                AssetParentEdgeSnap(parent_asset_key=AssetKey(["thirteen"])),
            ],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="create_twenty",
            node_definition_name="add_one",
            graph_name="create_twenty",
            op_names=["create_twenty.sum_plus_one.add_one", "create_twenty.sum_plus_one.get_sum"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            metadata={},
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey(["zero"]),
            parent_edges=[],
            child_edges=[
                AssetChildEdgeSnap(child_asset_key=AssetKey(["eight"])),
                AssetChildEdgeSnap(child_asset_key=AssetKey(["five"])),
                AssetChildEdgeSnap(child_asset_key=AssetKey(["six"])),
                AssetChildEdgeSnap(child_asset_key=AssetKey(["thirteen"])),
            ],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="zero",
            node_definition_name="zero",
            graph_name=None,
            op_names=["zero"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            metadata={},
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_deps_resolve_group():
    @asset(key_prefix="abc")
    def asset1(): ...

    @asset
    def asset2(asset1):
        del asset1

    assets_job = define_asset_job("assets_job", [asset1, asset2])
    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(assets=[asset1, asset2], jobs=[assets_job])
    )

    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey(["abc", "asset1"]),
            parent_edges=[],
            child_edges=[AssetChildEdgeSnap(child_asset_key=AssetKey("asset2"))],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="abc__asset1",
            node_definition_name="abc__asset1",
            graph_name=None,
            op_names=["abc__asset1"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey("asset2"),
            parent_edges=[AssetParentEdgeSnap(parent_asset_key=AssetKey(["abc", "asset1"]))],
            child_edges=[],
            execution_type=AssetExecutionType.MATERIALIZATION,
            op_name="asset2",
            node_definition_name="asset2",
            graph_name=None,
            op_names=["asset2"],
            description=None,
            job_names=["__ASSET_JOB", "assets_job"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_back_compat_external_sensor():
    SERIALIZED_0_12_10_SENSOR = (
        '{"__class__": "ExternalSensorData", "description": null, "min_interval": null, "mode":'
        ' "default", "name": "my_sensor", "pipeline_name": "my_pipeline", "solid_selection": null}'
    )
    external_sensor_data = deserialize_value(SERIALIZED_0_12_10_SENSOR, SensorSnap)
    assert isinstance(external_sensor_data, SensorSnap)
    assert len(external_sensor_data.target_dict) == 1
    assert "my_pipeline" in external_sensor_data.target_dict
    target = external_sensor_data.target_dict["my_pipeline"]
    assert isinstance(target, TargetSnap)
    assert target.job_name == "my_pipeline"


def _check_partitions_def_equal(
    p1: TimeWindowPartitionsDefinition, p2: TimeWindowPartitionsDefinition
):
    assert p1.start.timestamp() == p2.start.timestamp()
    assert p1.timezone == p2.timezone
    assert p1.fmt == p2.fmt
    assert p1.end_offset == p2.end_offset
    assert p1.cron_schedule == p2.cron_schedule


def test_back_compat_external_time_window_partitions_def():
    start = datetime(year=2022, month=5, day=5)

    external = TimeWindowPartitionsSnap(
        schedule_type=ScheduleType.WEEKLY,
        start=datetime(year=2022, month=5, day=5, tzinfo=get_timezone("Europe/Berlin")).timestamp(),
        timezone="Europe/Berlin",
        fmt=DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE,
        end_offset=1,
        minute_offset=5,
        hour_offset=13,
    )

    _check_partitions_def_equal(
        external.get_partitions_definition(),
        TimeWindowPartitionsDefinition(
            schedule_type=ScheduleType.WEEKLY,
            start=start,
            timezone="Europe/Berlin",
            fmt=DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE,
            end_offset=1,
            minute_offset=5,
            hour_offset=13,
        ),
    )


def test_external_time_window_partitions_def_cron_schedule():
    start = datetime(year=2022, month=5, day=5)

    partitions_def = TimeWindowPartitionsDefinition(
        start=start,
        timezone="US/Central",
        fmt=DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE,
        end_offset=1,
        cron_schedule="0 10,13 * * *",
    )

    external = TimeWindowPartitionsSnap.from_def(partitions_def).get_partitions_definition()

    _check_partitions_def_equal(external, partitions_def)


def test_external_multi_partitions_def():
    partitions_def = MultiPartitionsDefinition(
        {
            "date": DailyPartitionsDefinition("2022-01-01"),
            "static": StaticPartitionsDefinition(["a", "b", "c"]),
        }
    )

    external = MultiPartitionsSnap.from_def(partitions_def).get_partitions_definition()

    assert external == partitions_def


def test_graph_asset_description():
    @op
    def op1(): ...

    @graph_asset(description="bar")
    def foo():
        return op1()

    assets_job = define_asset_job("assets_job", [foo])

    asset_node_snaps = _get_asset_node_snaps_from_definitions(
        Definitions(assets=[foo], jobs=[assets_job])
    )
    assert asset_node_snaps[0].description == "bar"


def test_graph_multi_asset_description():
    @op
    def op1(): ...

    @op
    def op2(): ...

    @graph_multi_asset(
        outs={
            "asset1": AssetOut(description="bar"),
            "asset2": AssetOut(description="baz"),
        }
    )
    def foo():
        return {"asset1": op1(), "asset2": op2()}

    assets_job = define_asset_job("assets_job", [foo])

    asset_node_snaps = {
        asset_node.asset_key: asset_node
        for asset_node in _get_asset_node_snaps_from_definitions(
            Definitions(assets=[foo], jobs=[assets_job])
        )
    }
    assert asset_node_snaps[AssetKey("asset1")].description == "bar"
    assert asset_node_snaps[AssetKey("asset2")].description == "baz"


def test_external_time_window_valid_partition_key():
    hourly_partition = HourlyPartitionsDefinition(start_date="2023-03-11-15:00")

    external_partitions_def = TimeWindowPartitionsSnap.from_def(hourly_partition)
    assert (
        external_partitions_def.get_partitions_definition().has_partition_key("2023-03-11-15:00")
        is True
    )
    assert (
        external_partitions_def.get_partitions_definition().start.timestamp()
        == create_datetime(2023, 3, 11, 15).timestamp()
    )


def test_external_assets_def_to_external_asset_graph():
    asset1, asset2 = external_assets_from_specs(
        [AssetSpec("asset1"), AssetSpec("asset2", deps=["asset1"])]
    )

    asset_node_snaps = _get_asset_node_snaps_from_definitions(Definitions(assets=[asset1, asset2]))

    assert len(asset_node_snaps) == 2

    assert asset_node_snaps == [
        AssetNodeSnap(
            asset_key=AssetKey(["asset1"]),
            parent_edges=[],
            child_edges=[AssetChildEdgeSnap(child_asset_key=AssetKey("asset2"))],
            execution_type=AssetExecutionType.UNEXECUTABLE,
            group_name=DEFAULT_GROUP_NAME,
        ),
        AssetNodeSnap(
            asset_key=AssetKey("asset2"),
            parent_edges=[AssetParentEdgeSnap(parent_asset_key=AssetKey(["asset1"]))],
            child_edges=[],
            execution_type=AssetExecutionType.UNEXECUTABLE,
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_historical_external_asset_node_that_models_underlying_external_assets_def() -> None:
    assert not AssetNodeSnap(
        asset_key=AssetKey("asset_one"),
        parent_edges=[],
        child_edges=[],
        # purposefully not using constants here so we know when we are breaking ourselves
        metadata={"dagster/asset_execution_type": TextMetadataValue("UNEXECUTABLE")},
    ).is_executable

    assert AssetNodeSnap(
        asset_key=AssetKey("asset_one"),
        parent_edges=[],
        child_edges=[],
    ).is_executable


def test_back_compat_team_owners():
    """Up through Dagster 1.7.7, asset owners provided as "team:foo" would be serialized as "foo"
    going forward, they're serialized as "team:foo".

    This test verifies we can still load the old format.
    """
    packed_1_7_7_external_asset = {
        "__class__": "ExternalAssetNode",
        "asset_key": {"__class__": "AssetKey", "path": ["asset_one"]},
        "dependencies": [],
        "depended_by": [],
        "execution_type": {"__enum__": "AssetExecutionType.MATERIALIZATION"},
        "compute_kind": None,
        "op_name": None,
        "op_names": [],
        "code_version": None,
        "node_definition_name": None,
        "graph_name": None,
        "op_description": None,
        "job_names": [],
        "partitions_def_data": None,
        "output_name": None,
        "output_description": None,
        "metadata_entries": [],
        "tags": {},
        "group_name": "default",
        "freshness_policy": None,
        "is_source": True,
        "is_observable": False,
        "atomic_execution_unit_id": None,
        "required_top_level_resources": [],
        "auto_materialize_policy": None,
        "backfill_policy": None,
        "auto_observe_interval_minutes": None,
        "owners": ["foo", "hi@me.com"],
    }

    external_asset_node = unpack_value(packed_1_7_7_external_asset)
    assert external_asset_node.owners == ["team:foo", "hi@me.com"]
