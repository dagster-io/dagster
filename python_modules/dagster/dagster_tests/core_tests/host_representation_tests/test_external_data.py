import pytest

from dagster import AssetGroup, AssetKey, DagsterInvariantViolationError, Out
from dagster.check import CheckError
from dagster.core.asset_defs import AssetIn, SourceAsset, asset, build_assets_job, multi_asset
from dagster.core.definitions.metadata import MetadataEntry, MetadataValue
from dagster.core.host_representation.external_data import (
    ExternalAssetDependedBy,
    ExternalAssetDependency,
    ExternalAssetNode,
    ExternalSensorData,
    ExternalTargetData,
    external_asset_graph_from_defs,
)
from dagster.serdes import deserialize_json_to_dagster_namedtuple


def test_single_asset_job():
    @asset
    def asset1():
        return 1

    assets_job = build_assets_job("assets_job", [asset1])
    external_asset_nodes = external_asset_graph_from_defs([assets_job], source_assets_by_key={})

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[],
            op_name="asset1",
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
        )
    ]


def test_two_asset_job():
    @asset
    def asset1():
        return 1

    @asset
    def asset2(asset1):
        assert asset1 == 1

    assets_job = build_assets_job("assets_job", [asset1, asset2])
    external_asset_nodes = external_asset_graph_from_defs([assets_job], source_assets_by_key={})

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey("asset2"), input_name="asset1"
                )
            ],
            op_name="asset1",
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("asset2"),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey("asset1"), input_name="asset1")
            ],
            depended_by=[],
            op_name="asset2",
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
        ),
    ]


def test_two_asset_job_with_group():
    @asset
    def asset1():
        return 1

    @asset
    def asset2(asset1):
        assert asset1 == 1

    asset_group = AssetGroup(assets=[asset1, asset2])
    asset_group_job = build_assets_job(
        asset_group.all_assets_job_name(),
        assets=asset_group.assets,
        source_assets=asset_group.source_assets,
        resource_defs=asset_group.resource_defs,
        executor_def=asset_group.executor_def,
    )
    assets_job = asset_group.build_job(name="assets_job")

    external_asset_nodes = external_asset_graph_from_defs(
        [asset_group_job, assets_job], source_assets_by_key={}
    )

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey("asset2"), input_name="asset1"
                )
            ],
            op_name="asset1",
            op_description=None,
            job_names=[AssetGroup.all_assets_job_name(), "assets_job"],
            output_name="result",
            output_description=None,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("asset2"),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey("asset1"), input_name="asset1")
            ],
            depended_by=[],
            op_name="asset2",
            op_description=None,
            job_names=[AssetGroup.all_assets_job_name(), "assets_job"],
            output_name="result",
            output_description=None,
        ),
    ]


def test_input_name_matches_output_name():
    not_result = SourceAsset(key=AssetKey("not_result"), description=None)

    @asset(ins={"result": AssetIn(asset_key=AssetKey("not_result"))})
    def something(result):  # pylint: disable=unused-argument
        pass

    assets_job = build_assets_job("assets_job", [something], source_assets=[not_result])
    external_asset_nodes = external_asset_graph_from_defs([assets_job], source_assets_by_key={})

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("not_result"),
            dependencies=[],
            depended_by=[
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey("something"), input_name="result"
                )
            ],
            job_names=[],
        ),
        ExternalAssetNode(
            asset_key=AssetKey("something"),
            dependencies=[
                ExternalAssetDependency(
                    upstream_asset_key=AssetKey("not_result"), input_name="result"
                )
            ],
            depended_by=[],
            op_name="something",
            output_name="result",
            job_names=["assets_job"],
        ),
    ]


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

    assets_job = build_assets_job("assets_job", [asset1, asset2_a, asset2_b])
    external_asset_nodes = external_asset_graph_from_defs([assets_job], source_assets_by_key={})

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey("asset2_a"), input_name="asset1"
                ),
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey("asset2_b"), input_name="asset1"
                ),
            ],
            op_name="asset1",
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("asset2_a"),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey("asset1"), input_name="asset1")
            ],
            depended_by=[],
            op_name="asset2_a",
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("asset2_b"),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey("asset1"), input_name="asset1")
            ],
            depended_by=[],
            op_name="asset2_b",
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
        ),
    ]


def test_cross_job_asset_dependency():
    @asset
    def asset1():
        return 1

    @asset
    def asset2(asset1):
        assert asset1 == 1

    assets_job1 = build_assets_job("assets_job1", [asset1])
    assets_job2 = build_assets_job("assets_job2", [asset2], source_assets=[asset1])
    external_asset_nodes = external_asset_graph_from_defs(
        [assets_job1, assets_job2], source_assets_by_key={}
    )

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey("asset2"), input_name="asset1"
                )
            ],
            op_name="asset1",
            op_description=None,
            job_names=["assets_job1"],
            output_name="result",
            output_description=None,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("asset2"),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey("asset1"), input_name="asset1")
            ],
            depended_by=[],
            op_name="asset2",
            op_description=None,
            job_names=["assets_job2"],
            output_name="result",
            output_description=None,
        ),
    ]


def test_same_asset_in_multiple_pipelines():
    @asset
    def asset1():
        return 1

    job1 = build_assets_job("job1", [asset1])
    job2 = build_assets_job("job2", [asset1])

    external_asset_nodes = external_asset_graph_from_defs([job1, job2], source_assets_by_key={})

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[],
            op_name="asset1",
            op_description=None,
            job_names=["job1", "job2"],
            output_name="result",
            output_description=None,
        ),
    ]


def test_basic_multi_asset():
    @multi_asset(
        outs={
            f"out{i}": Out(description=f"foo: {i}", asset_key=AssetKey(f"asset{i}"))
            for i in range(10)
        }
    )
    def assets():
        pass

    assets_job = build_assets_job("assets_job", [assets])

    external_asset_nodes = external_asset_graph_from_defs([assets_job], source_assets_by_key={})

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey(f"asset{i}"),
            dependencies=[],
            depended_by=[],
            op_name="assets",
            op_description=None,
            job_names=["assets_job"],
            output_name=f"out{i}",
            output_description=f"foo: {i}",
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
    def downstream(only_in, mixed, only_out):  # pylint: disable=unused-argument
        pass

    @multi_asset(
        outs={"only_in": Out(), "mixed": Out(), "only_out": Out()},
        internal_asset_deps={
            "mixed": {AssetKey("in1"), AssetKey("only_in")},
            "only_out": {AssetKey("only_in"), AssetKey("mixed")},
        },
    )
    def assets(in1, in2):  # pylint: disable=unused-argument
        pass

    assets_job = build_assets_job("assets_job", [in1, in2, assets, downstream])

    external_asset_nodes = external_asset_graph_from_defs([assets_job], source_assets_by_key={})
    # sort so that test is deterministic
    sorted_nodes = sorted(
        [
            node._replace(
                dependencies=sorted(node.dependencies, key=lambda d: d.upstream_asset_key),
                depended_by=sorted(node.depended_by, key=lambda d: d.downstream_asset_key),
            )
            for node in external_asset_nodes
        ],
        key=lambda n: n.asset_key,
    )

    assert sorted_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey(["downstream"]),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey(["mixed"]), input_name="mixed"),
                ExternalAssetDependency(
                    upstream_asset_key=AssetKey(["only_in"]), input_name="only_in"
                ),
                ExternalAssetDependency(
                    upstream_asset_key=AssetKey(["only_out"]), input_name="only_out"
                ),
            ],
            depended_by=[],
            op_name="downstream",
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            metadata_entries=[],
        ),
        ExternalAssetNode(
            asset_key=AssetKey(["in1"]),
            dependencies=[],
            depended_by=[
                ExternalAssetDependedBy(downstream_asset_key=AssetKey(["mixed"]), input_name="in1"),
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey(["only_in"]), input_name="in1"
                ),
            ],
            op_name="in1",
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            metadata_entries=[],
        ),
        ExternalAssetNode(
            asset_key=AssetKey(["in2"]),
            dependencies=[],
            depended_by=[
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey(["only_in"]), input_name="in2"
                )
            ],
            op_name="in2",
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            metadata_entries=[],
        ),
        ExternalAssetNode(
            asset_key=AssetKey(["mixed"]),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey(["in1"]), input_name="in1"),
                ExternalAssetDependency(
                    upstream_asset_key=AssetKey(["only_in"]), output_name="only_in"
                ),
            ],
            depended_by=[
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey(["downstream"]), input_name="mixed"
                ),
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey(["only_out"]), output_name="mixed"
                ),
            ],
            op_name="assets",
            op_description=None,
            job_names=["assets_job"],
            output_name="mixed",
            metadata_entries=[
                MetadataEntry(
                    label=".dagster/asset_deps",
                    description=None,
                    entry_data=MetadataValue.text("[set] (unserializable)"),
                )
            ],
        ),
        ExternalAssetNode(
            asset_key=AssetKey(["only_in"]),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey(["in1"]), input_name="in1"),
                ExternalAssetDependency(upstream_asset_key=AssetKey(["in2"]), input_name="in2"),
            ],
            depended_by=[
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey(["downstream"]), input_name="only_in"
                ),
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey(["mixed"]), output_name="only_in"
                ),
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey(["only_out"]), output_name="only_in"
                ),
            ],
            op_name="assets",
            op_description=None,
            job_names=["assets_job"],
            output_name="only_in",
            metadata_entries=[],
        ),
        ExternalAssetNode(
            asset_key=AssetKey(["only_out"]),
            dependencies=[
                ExternalAssetDependency(
                    upstream_asset_key=AssetKey(["mixed"]), output_name="mixed"
                ),
                ExternalAssetDependency(
                    upstream_asset_key=AssetKey(["only_in"]), output_name="only_in"
                ),
            ],
            depended_by=[
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey(["downstream"]), input_name="only_out"
                ),
            ],
            op_name="assets",
            op_description=None,
            job_names=["assets_job"],
            output_name="only_out",
            metadata_entries=[
                MetadataEntry(
                    label=".dagster/asset_deps",
                    description=None,
                    entry_data=MetadataValue.text("[set] (unserializable)"),
                )
            ],
        ),
    ]


def test_source_asset_with_op():

    foo = SourceAsset(key=AssetKey("foo"), description=None)

    @asset
    def bar(foo):  # pylint: disable=unused-argument
        pass

    assets_job = build_assets_job("assets_job", [bar], source_assets=[foo])

    external_asset_nodes = external_asset_graph_from_defs([assets_job], source_assets_by_key={})
    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("foo"),
            op_description=None,
            dependencies=[],
            depended_by=[ExternalAssetDependedBy(AssetKey("bar"), input_name="foo")],
            job_names=[],
        ),
        ExternalAssetNode(
            asset_key=AssetKey("bar"),
            op_name="bar",
            op_description=None,
            dependencies=[ExternalAssetDependency(AssetKey("foo"), input_name="foo")],
            depended_by=[],
            job_names=["assets_job"],
            output_name="result",
        ),
    ]


def test_unused_source_asset():
    foo = SourceAsset(key=AssetKey("foo"), description="abc")
    bar = SourceAsset(key=AssetKey("bar"), description="def")

    external_asset_nodes = external_asset_graph_from_defs(
        [], source_assets_by_key={AssetKey("foo"): foo, AssetKey("bar"): bar}
    )
    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("foo"),
            op_description="abc",
            dependencies=[],
            depended_by=[],
            job_names=[],
        ),
        ExternalAssetNode(
            asset_key=AssetKey("bar"),
            op_description="def",
            dependencies=[],
            depended_by=[],
            job_names=[],
        ),
    ]


def test_used_source_asset():
    bar = SourceAsset(key=AssetKey("bar"), description="def")

    @asset
    def foo(bar):
        assert bar

    job1 = build_assets_job("job1", [foo], source_assets=[bar])

    external_asset_nodes = external_asset_graph_from_defs(
        [job1], source_assets_by_key={AssetKey("bar"): bar}
    )
    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("bar"),
            op_description="def",
            dependencies=[],
            depended_by=[
                ExternalAssetDependedBy(downstream_asset_key=AssetKey(["foo"]), input_name="bar")
            ],
            job_names=[],
        ),
        ExternalAssetNode(
            asset_key=AssetKey("foo"),
            op_name="foo",
            op_description=None,
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey(["bar"]), input_name="bar")
            ],
            depended_by=[],
            job_names=["job1"],
            output_name="result",
            output_description=None,
        ),
    ]


def test_source_asset_conflicts_with_asset():
    bar_source_asset = SourceAsset(key=AssetKey("bar"), description="def")

    @asset
    def bar():
        pass

    job1 = build_assets_job("job1", [bar])

    with pytest.raises(DagsterInvariantViolationError):
        external_asset_graph_from_defs(
            [job1], source_assets_by_key={AssetKey("bar"): bar_source_asset}
        )


def test_input_name_or_output_name_dep_by():
    with pytest.raises(CheckError, match="input `foo` and output `bar`"):
        ExternalAssetDependedBy(
            downstream_asset_key=AssetKey("bar"), input_name="foo", output_name="bar"
        )
    with pytest.raises(CheckError, match="input `None` and output `None`"):
        ExternalAssetDependedBy(
            downstream_asset_key=AssetKey("bar"), input_name=None, output_name=None
        )


def test_input_name_or_output_name_dependency():
    with pytest.raises(CheckError, match="input `foo` and output `bar`"):
        ExternalAssetDependency(
            upstream_asset_key=AssetKey("bar"), input_name="foo", output_name="bar"
        )
    with pytest.raises(CheckError, match="input `None` and output `None`"):
        ExternalAssetDependency(
            upstream_asset_key=AssetKey("bar"), input_name=None, output_name=None
        )


def test_back_compat_external_sensor():
    SERIALIZED_0_12_10_SENSOR = '{"__class__": "ExternalSensorData", "description": null, "min_interval": null, "mode": "default", "name": "my_sensor", "pipeline_name": "my_pipeline", "solid_selection": null}'
    external_sensor_data = deserialize_json_to_dagster_namedtuple(SERIALIZED_0_12_10_SENSOR)
    assert isinstance(external_sensor_data, ExternalSensorData)
    assert len(external_sensor_data.target_dict) == 1
    assert "my_pipeline" in external_sensor_data.target_dict
    target = external_sensor_data.target_dict["my_pipeline"]
    assert isinstance(target, ExternalTargetData)
    assert target.pipeline_name == "my_pipeline"
