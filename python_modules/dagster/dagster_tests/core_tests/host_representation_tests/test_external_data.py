import pytest

from dagster import AssetKey, AssetsDefinition, GraphOut, In, Out, define_asset_job, graph, job, op
from dagster.core.asset_defs import AssetIn, SourceAsset, asset, build_assets_job, multi_asset
from dagster.core.definitions.utils import DEFAULT_GROUP_NAME
from dagster.core.errors import DagsterInvalidDefinitionError
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
            graph_name=None,
            op_names=["asset1"],
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
            group_name=DEFAULT_GROUP_NAME,
        )
    ]


def test_asset_with_group_name():
    @asset(group_name="group1")
    def asset1():
        return 1

    assets_job = build_assets_job("assets_job", [asset1])
    external_asset_nodes = external_asset_graph_from_defs([assets_job], source_assets_by_key={})

    assert external_asset_nodes[0].group_name == "group1"


def test_asset_missing_group_name():
    @asset
    def asset1():
        return 1

    assets_job = build_assets_job("assets_job", [asset1])
    external_asset_nodes = external_asset_graph_from_defs([assets_job], source_assets_by_key={})

    assert external_asset_nodes[0].group_name == DEFAULT_GROUP_NAME


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

    assets_job = build_assets_job("assets_job", [asset1, asset2])
    external_asset_nodes = external_asset_graph_from_defs([assets_job], source_assets_by_key={})

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[ExternalAssetDependedBy(downstream_asset_key=AssetKey("asset2"))],
            op_name="asset1",
            graph_name=None,
            op_names=["asset1"],
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("asset2"),
            dependencies=[ExternalAssetDependency(upstream_asset_key=AssetKey("asset1"))],
            depended_by=[],
            op_name="asset2",
            graph_name=None,
            op_names=["asset2"],
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
            group_name=DEFAULT_GROUP_NAME,
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
            depended_by=[ExternalAssetDependedBy(downstream_asset_key=AssetKey("something"))],
            job_names=[],
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("something"),
            dependencies=[ExternalAssetDependency(upstream_asset_key=AssetKey("not_result"))],
            depended_by=[],
            op_name="something",
            graph_name=None,
            op_names=["something"],
            output_name="result",
            job_names=["assets_job"],
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_assets_excluded_from_subset_not_in_job():
    @multi_asset(outs={"a": Out(), "b": Out(), "c": Out()}, can_subset=True)
    def abc():
        pass

    @asset
    def a2(a):
        return a

    @asset
    def c2(c):
        return c

    all_assets = [abc, a2, c2]
    as_job = define_asset_job("as_job", selection="a*").resolve(all_assets, [])
    cs_job = define_asset_job("cs_job", selection="*c2").resolve(all_assets, [])

    external_asset_nodes = external_asset_graph_from_defs([as_job, cs_job], source_assets_by_key={})

    assert (
        ExternalAssetNode(
            asset_key=AssetKey("a"),
            dependencies=[],
            depended_by=[ExternalAssetDependedBy(downstream_asset_key=AssetKey("a2"))],
            op_name="abc",
            graph_name=None,
            op_names=["abc"],
            job_names=["as_job"],  # the important line
            output_name="a",
            group_name=DEFAULT_GROUP_NAME,
        )
        in external_asset_nodes
    )

    assert (
        ExternalAssetNode(
            asset_key=AssetKey("c"),
            dependencies=[],
            depended_by=[ExternalAssetDependedBy(downstream_asset_key=AssetKey("c2"))],
            op_name="abc",
            graph_name=None,
            op_names=["abc"],
            job_names=["cs_job"],  # the important line
            output_name="c",
            group_name=DEFAULT_GROUP_NAME,
        )
        in external_asset_nodes
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

    assets_job = build_assets_job("assets_job", [asset1, asset2_a, asset2_b])
    external_asset_nodes = external_asset_graph_from_defs([assets_job], source_assets_by_key={})

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[
                ExternalAssetDependedBy(downstream_asset_key=AssetKey("asset2_a")),
                ExternalAssetDependedBy(downstream_asset_key=AssetKey("asset2_b")),
            ],
            op_name="asset1",
            graph_name=None,
            op_names=["asset1"],
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("asset2_a"),
            dependencies=[ExternalAssetDependency(upstream_asset_key=AssetKey("asset1"))],
            depended_by=[],
            op_name="asset2_a",
            graph_name=None,
            op_names=["asset2_a"],
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("asset2_b"),
            dependencies=[ExternalAssetDependency(upstream_asset_key=AssetKey("asset1"))],
            depended_by=[],
            op_name="asset2_b",
            graph_name=None,
            op_names=["asset2_b"],
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
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

    assets_job1 = build_assets_job("assets_job1", [asset1])
    assets_job2 = build_assets_job("assets_job2", [asset2], source_assets=[asset1])
    external_asset_nodes = external_asset_graph_from_defs(
        [assets_job1, assets_job2], source_assets_by_key={}
    )

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[ExternalAssetDependedBy(downstream_asset_key=AssetKey("asset2"))],
            op_name="asset1",
            graph_name=None,
            op_names=["asset1"],
            op_description=None,
            job_names=["assets_job1"],
            output_name="result",
            output_description=None,
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("asset2"),
            dependencies=[ExternalAssetDependency(upstream_asset_key=AssetKey("asset1"))],
            depended_by=[],
            op_name="asset2",
            graph_name=None,
            op_names=["asset2"],
            op_description=None,
            job_names=["assets_job2"],
            output_name="result",
            output_description=None,
            group_name=DEFAULT_GROUP_NAME,
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
            graph_name=None,
            op_names=["asset1"],
            op_description=None,
            job_names=["job1", "job2"],
            output_name="result",
            output_description=None,
            group_name=DEFAULT_GROUP_NAME,
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
            graph_name=None,
            op_names=["assets"],
            op_description=None,
            job_names=["assets_job"],
            output_name=f"out{i}",
            output_description=f"foo: {i}",
            group_name=DEFAULT_GROUP_NAME,
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
            "only_in": {AssetKey("in1"), AssetKey("in2")},
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
                ExternalAssetDependency(upstream_asset_key=AssetKey(["mixed"])),
                ExternalAssetDependency(upstream_asset_key=AssetKey(["only_in"])),
                ExternalAssetDependency(upstream_asset_key=AssetKey(["only_out"])),
            ],
            depended_by=[],
            op_name="downstream",
            graph_name=None,
            op_names=["downstream"],
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            metadata_entries=[],
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey(["in1"]),
            dependencies=[],
            depended_by=[
                ExternalAssetDependedBy(downstream_asset_key=AssetKey(["mixed"])),
                ExternalAssetDependedBy(downstream_asset_key=AssetKey(["only_in"])),
            ],
            op_name="in1",
            graph_name=None,
            op_names=["in1"],
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            metadata_entries=[],
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey(["in2"]),
            dependencies=[],
            depended_by=[ExternalAssetDependedBy(downstream_asset_key=AssetKey(["only_in"]))],
            op_name="in2",
            graph_name=None,
            op_names=["in2"],
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            metadata_entries=[],
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey(["mixed"]),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey(["in1"])),
                ExternalAssetDependency(upstream_asset_key=AssetKey(["only_in"])),
            ],
            depended_by=[
                ExternalAssetDependedBy(downstream_asset_key=AssetKey(["downstream"])),
                ExternalAssetDependedBy(downstream_asset_key=AssetKey(["only_out"])),
            ],
            op_name="assets",
            graph_name=None,
            op_names=["assets"],
            op_description=None,
            job_names=["assets_job"],
            output_name="mixed",
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey(["only_in"]),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey(["in1"])),
                ExternalAssetDependency(upstream_asset_key=AssetKey(["in2"])),
            ],
            depended_by=[
                ExternalAssetDependedBy(downstream_asset_key=AssetKey(["downstream"])),
                ExternalAssetDependedBy(downstream_asset_key=AssetKey(["mixed"])),
                ExternalAssetDependedBy(downstream_asset_key=AssetKey(["only_out"])),
            ],
            op_name="assets",
            graph_name=None,
            op_names=["assets"],
            op_description=None,
            job_names=["assets_job"],
            output_name="only_in",
            metadata_entries=[],
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey(["only_out"]),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey(["mixed"])),
                ExternalAssetDependency(upstream_asset_key=AssetKey(["only_in"])),
            ],
            depended_by=[
                ExternalAssetDependedBy(downstream_asset_key=AssetKey(["downstream"])),
            ],
            op_name="assets",
            graph_name=None,
            op_names=["assets"],
            op_description=None,
            job_names=["assets_job"],
            output_name="only_out",
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_explicit_asset_keys():
    @op(out={"a": Out(asset_key=AssetKey("a"))})
    def a_op():
        return 1

    @op(
        ins={"a": In(asset_key=AssetKey("a"))},
        out={"b": Out(asset_key=AssetKey("b"))},
    )
    def b_op(a):
        return a + 1

    @job
    def assets_job():
        b_op(a_op())

    external_asset_nodes = external_asset_graph_from_defs([assets_job], source_assets_by_key={})
    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("a"),
            op_name="a_op",
            graph_name=None,
            op_names=["a_op"],
            op_description=None,
            dependencies=[],
            depended_by=[ExternalAssetDependedBy(AssetKey("b"))],
            job_names=["assets_job"],
            output_name="a",
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("b"),
            op_name="b_op",
            graph_name=None,
            op_names=["b_op"],
            op_description=None,
            dependencies=[ExternalAssetDependency(AssetKey("a"))],
            depended_by=[],
            job_names=["assets_job"],
            output_name="b",
            group_name=DEFAULT_GROUP_NAME,
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
            depended_by=[ExternalAssetDependedBy(AssetKey("bar"))],
            job_names=[],
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("bar"),
            op_name="bar",
            graph_name=None,
            op_names=["bar"],
            op_description=None,
            dependencies=[ExternalAssetDependency(AssetKey("foo"))],
            depended_by=[],
            job_names=["assets_job"],
            output_name="result",
            group_name=DEFAULT_GROUP_NAME,
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
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("bar"),
            op_description="def",
            dependencies=[],
            depended_by=[],
            job_names=[],
            group_name=DEFAULT_GROUP_NAME,
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
            depended_by=[ExternalAssetDependedBy(downstream_asset_key=AssetKey(["foo"]))],
            job_names=[],
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("foo"),
            op_name="foo",
            graph_name=None,
            op_names=["foo"],
            op_description=None,
            dependencies=[ExternalAssetDependency(upstream_asset_key=AssetKey(["bar"]))],
            depended_by=[],
            job_names=["job1"],
            output_name="result",
            output_description=None,
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_nasty_nested_graph_asset():
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
        asset_keys_by_input_name={"zero": AssetKey("zero")},
        asset_keys_by_output_name={"eight": AssetKey("eight"), "five": AssetKey("five")},
        node_def=create_eight_and_five,
    )

    thirteen_and_six = AssetsDefinition(
        asset_keys_by_input_name={
            "eight": AssetKey("eight"),
            "five": AssetKey("five"),
            "zero": AssetKey("zero"),
        },
        asset_keys_by_output_name={"thirteen": AssetKey("thirteen"), "six": AssetKey("six")},
        node_def=create_thirteen_and_six,
    )

    twenty = AssetsDefinition(
        asset_keys_by_input_name={"thirteen": AssetKey("thirteen"), "six": AssetKey("six")},
        asset_keys_by_output_name={"result": AssetKey("twenty")},
        node_def=create_twenty,
    )

    assets_job = build_assets_job("assets_job", [zero, eight_and_five, thirteen_and_six, twenty])

    external_asset_nodes = external_asset_graph_from_defs([assets_job], source_assets_by_key={})
    # sort so that test is deterministic
    sorted_nodes = sorted(
        [
            node._replace(
                dependencies=sorted(node.dependencies, key=lambda d: d.upstream_asset_key),
                depended_by=sorted(node.depended_by, key=lambda d: d.downstream_asset_key),
                op_names=sorted(node.op_names),
            )
            for node in external_asset_nodes
        ],
        key=lambda n: n.asset_key,
    )

    assert sorted_nodes[-3:] == [
        ExternalAssetNode(
            asset_key=AssetKey(["thirteen"]),
            dependencies=[
                ExternalAssetDependency(AssetKey(["eight"])),
                ExternalAssetDependency(AssetKey(["five"])),
                ExternalAssetDependency(AssetKey(["zero"])),
            ],
            depended_by=[ExternalAssetDependedBy(AssetKey(["twenty"]))],
            op_name="create_thirteen_and_six",
            graph_name="create_thirteen_and_six",
            op_names=[
                "create_thirteen_and_six.add_five.add_one",
                "create_thirteen_and_six.add_five.add_one_2",
                "create_thirteen_and_six.add_five.add_three.add_one",
                "create_thirteen_and_six.add_five.add_three.add_one_2",
                "create_thirteen_and_six.add_five.add_three.add_one_3",
            ],
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            metadata_entries=[],
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey(["twenty"]),
            dependencies=[
                ExternalAssetDependency(AssetKey(["six"])),
                ExternalAssetDependency(AssetKey(["thirteen"])),
            ],
            depended_by=[],
            op_name="create_twenty",
            graph_name="create_twenty",
            op_names=["create_twenty.sum_plus_one.add_one", "create_twenty.sum_plus_one.get_sum"],
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            metadata_entries=[],
            group_name=DEFAULT_GROUP_NAME,
        ),
        ExternalAssetNode(
            asset_key=AssetKey(["zero"]),
            dependencies=[],
            depended_by=[
                ExternalAssetDependedBy(AssetKey(["eight"])),
                ExternalAssetDependedBy(AssetKey(["five"])),
                ExternalAssetDependedBy(AssetKey(["six"])),
                ExternalAssetDependedBy(AssetKey(["thirteen"])),
            ],
            op_name="zero",
            graph_name=None,
            op_names=["zero"],
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            metadata_entries=[],
            group_name=DEFAULT_GROUP_NAME,
        ),
    ]


def test_back_compat_external_sensor():
    SERIALIZED_0_12_10_SENSOR = '{"__class__": "ExternalSensorData", "description": null, "min_interval": null, "mode": "default", "name": "my_sensor", "pipeline_name": "my_pipeline", "solid_selection": null}'
    external_sensor_data = deserialize_json_to_dagster_namedtuple(SERIALIZED_0_12_10_SENSOR)
    assert isinstance(external_sensor_data, ExternalSensorData)
    assert len(external_sensor_data.target_dict) == 1
    assert "my_pipeline" in external_sensor_data.target_dict
    target = external_sensor_data.target_dict["my_pipeline"]
    assert isinstance(target, ExternalTargetData)
    assert target.pipeline_name == "my_pipeline"
