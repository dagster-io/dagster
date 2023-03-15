import os
import warnings

import pytest
from dagster import (
    AssetKey,
    AssetOut,
    AssetsDefinition,
    DagsterEventType,
    DagsterInvalidDefinitionError,
    DailyPartitionsDefinition,
    DependencyDefinition,
    Field,
    GraphIn,
    GraphOut,
    HourlyPartitionsDefinition,
    In,
    IOManager,
    Nothing,
    Out,
    Output,
    ResourceDefinition,
    StaticPartitionsDefinition,
    build_reconstructable_job,
    define_asset_job,
    graph,
    io_manager,
    materialize_to_memory,
    multi_asset,
    op,
    resource,
    with_resources,
)
from dagster._config import StringSource
from dagster._core.definitions import AssetGroup, AssetIn, SourceAsset, asset, build_assets_job
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets_job import get_base_asset_jobs
from dagster._core.definitions.dependency import NodeHandle
from dagster._core.definitions.executor_definition import in_process_executor
from dagster._core.errors import DagsterInvalidSubsetError
from dagster._core.execution.api import execute_pipeline, execute_run_iterator
from dagster._core.snap import DependencyStructureIndex
from dagster._core.snap.dep_snapshot import (
    OutputHandleSnap,
    build_dep_structure_snapshot_from_icontains_solids,
)
from dagster._core.storage.event_log.base import EventRecordsFilter
from dagster._core.test_utils import instance_for_test
from dagster._utils import safe_tempfile_path
from dagster._utils.backcompat import ExperimentalWarning


@pytest.fixture(autouse=True)
def check_experimental_warnings():
    with warnings.catch_warnings(record=True) as record:
        # turn off any outer warnings filters
        warnings.resetwarnings()

        yield

        for w in record:
            # Expect experimental warnings to be thrown for direct
            # resource_defs and io_manager_def arguments.
            if (
                "resource_defs" in w.message.args[0]
                or "io_manager_def" in w.message.args[0]
                or "build_assets_job" in w.message.args[0]
            ):
                continue
            assert False, f"Unexpected warning: {w.message.args[0]}"


def _asset_keys_for_node(result, node_name):
    mats = result.asset_materializations_for_node(node_name)
    ret = {mat.asset_key for mat in mats}
    assert len(mats) == len(ret)
    return ret


def test_single_asset_pipeline():
    @asset
    def asset1(context):
        assert context.asset_key_for_output() == AssetKey(["asset1"])
        return 1

    job = build_assets_job("a", [asset1])
    assert job.graph.node_defs == [asset1.op]
    assert job.execute_in_process().success


def test_two_asset_pipeline():
    @asset
    def asset1():
        return 1

    @asset
    def asset2(asset1):
        assert asset1 == 1

    job = build_assets_job("a", [asset1, asset2])
    assert job.graph.node_defs == [asset1.op, asset2.op]
    assert job.dependencies == {
        "asset1": {},
        "asset2": {"asset1": DependencyDefinition("asset1", "result")},
    }
    assert job.execute_in_process().success


def test_single_asset_pipeline_with_config():
    @asset(config_schema={"foo": Field(StringSource)})
    def asset1(context):
        return context.op_config["foo"]

    job = build_assets_job("a", [asset1])
    assert job.graph.node_defs == [asset1.op]
    assert job.execute_in_process(
        run_config={"ops": {"asset1": {"config": {"foo": "bar"}}}}
    ).success


def test_fork():
    @asset
    def asset1():
        return 1

    @asset
    def asset2(asset1):
        assert asset1 == 1

    @asset
    def asset3(asset1):
        assert asset1 == 1

    job = build_assets_job("a", [asset1, asset2, asset3])
    assert job.graph.node_defs == [asset1.op, asset2.op, asset3.op]
    assert job.dependencies == {
        "asset1": {},
        "asset2": {"asset1": DependencyDefinition("asset1", "result")},
        "asset3": {"asset1": DependencyDefinition("asset1", "result")},
    }
    assert job.execute_in_process().success


def test_join():
    @asset
    def asset1():
        return 1

    @asset
    def asset2():
        return 2

    @asset
    def asset3(asset1, asset2):
        assert asset1 == 1
        assert asset2 == 2

    job = build_assets_job("a", [asset1, asset2, asset3])
    assert job.graph.node_defs == [asset1.op, asset2.op, asset3.op]
    assert job.dependencies == {
        "asset1": {},
        "asset2": {},
        "asset3": {
            "asset1": DependencyDefinition("asset1", "result"),
            "asset2": DependencyDefinition("asset2", "result"),
        },
    }
    result = job.execute_in_process()
    assert _asset_keys_for_node(result, "asset3") == {AssetKey("asset3")}


def test_asset_key_output():
    @asset
    def asset1():
        return 1

    @asset(ins={"hello": AssetIn(key=AssetKey("asset1"))})
    def asset2(hello):
        return hello

    job = build_assets_job("boo", [asset1, asset2])
    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("asset2") == 1
    assert _asset_keys_for_node(result, "asset2") == {AssetKey("asset2")}


def test_asset_key_matches_input_name():
    @asset
    def asset_foo():
        return "foo"

    @asset
    def asset_bar():
        return "bar"

    @asset(
        ins={"asset_bar": AssetIn(key=AssetKey("asset_foo"))}
    )  # should still use output from asset_foo
    def last_asset(asset_bar):
        return asset_bar

    job = build_assets_job("lol", [asset_foo, asset_bar, last_asset])
    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("last_asset") == "foo"
    assert _asset_keys_for_node(result, "last_asset") == {AssetKey("last_asset")}


def test_asset_key_and_inferred():
    @asset
    def asset_foo():
        return 2

    @asset
    def asset_bar():
        return 5

    @asset(ins={"foo": AssetIn(key=AssetKey("asset_foo"))})
    def asset_baz(foo, asset_bar):
        return foo + asset_bar

    job = build_assets_job("hello", [asset_foo, asset_bar, asset_baz])
    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("asset_baz") == 7
    assert _asset_keys_for_node(result, "asset_baz") == {AssetKey("asset_baz")}


def test_asset_key_for_asset_with_key_prefix_str():
    @asset(key_prefix="hello")
    def asset_foo():
        return "foo"

    @asset(ins={"foo": AssetIn(key=AssetKey(["hello", "asset_foo"]))})
    def success_asset(foo):
        return foo

    job = build_assets_job("lol", [asset_foo, success_asset])

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("success_asset") == "foo"
    assert _asset_keys_for_node(result, "hello__asset_foo") == {AssetKey(["hello", "asset_foo"])}


def test_source_asset():
    @asset
    def asset1(source1):
        assert source1 == 5
        return 1

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert context.resource_config["a"] == 7
            assert context.resources.subresource == 9
            assert context.upstream_output.resources.subresource == 9
            assert context.upstream_output.asset_key == AssetKey("source1")
            assert context.upstream_output.metadata == {"a": "b"}
            assert context.upstream_output.resource_config["a"] == 7
            assert context.upstream_output.log is not None
            context.upstream_output.log.info("hullo")
            assert context.asset_key == AssetKey("source1")
            return 5

    @io_manager(config_schema={"a": int}, required_resource_keys={"subresource"})
    def my_io_manager(_):
        return MyIOManager()

    job = build_assets_job(
        "a",
        [asset1],
        source_assets=[
            SourceAsset(
                AssetKey("source1"), io_manager_key="special_io_manager", metadata={"a": "b"}
            )
        ],
        resource_defs={
            "special_io_manager": my_io_manager.configured({"a": 7}),
            "subresource": ResourceDefinition.hardcoded_resource(9),
        },
    )
    assert job.graph.node_defs == [asset1.op]
    result = job.execute_in_process()
    assert result.success
    assert _asset_keys_for_node(result, "asset1") == {AssetKey("asset1")}


def test_missing_io_manager():
    @asset
    def asset1(source1):
        return source1

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            r"io manager with key 'special_io_manager' required by SourceAsset with key"
            r" \[\"source1\"\] was not provided."
        ),
    ):
        build_assets_job(
            "a",
            [asset1],
            source_assets=[SourceAsset(AssetKey("source1"), io_manager_key="special_io_manager")],
        )


def test_source_op_asset():
    @asset(io_manager_key="special_io_manager")
    def source1():
        pass

    @asset
    def asset1(source1):
        assert source1 == 5
        return 1

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @io_manager
    def my_io_manager(_):
        return MyIOManager()

    job = build_assets_job(
        "a",
        [asset1],
        source_assets=[source1],
        resource_defs={"special_io_manager": my_io_manager},
    )
    assert job.graph.node_defs == [asset1.op]
    result = job.execute_in_process()
    assert result.success
    assert _asset_keys_for_node(result, "asset1") == {AssetKey("asset1")}


def test_non_argument_deps():
    with safe_tempfile_path() as path:

        @asset
        def foo():
            with open(path, "w", encoding="utf8") as ff:
                ff.write("yup")

        @asset(non_argument_deps={AssetKey("foo")})
        def bar():
            # assert that the foo asset already executed
            assert os.path.exists(path)

        job = build_assets_job("a", [foo, bar])
        result = job.execute_in_process()
        assert result.success
        assert _asset_keys_for_node(result, "foo") == {AssetKey("foo")}
        assert _asset_keys_for_node(result, "bar") == {AssetKey("bar")}


def test_non_argument_deps_as_str():
    @asset
    def foo():
        pass

    @asset(non_argument_deps={"foo"})
    def bar():
        pass

    assert AssetKey("foo") in bar.asset_deps[AssetKey("bar")]


def test_multiple_non_argument_deps():
    @asset
    def foo():
        pass

    @asset(key_prefix="key_prefix")
    def bar():
        pass

    @asset
    def baz():
        return 1

    @asset(non_argument_deps={AssetKey("foo"), AssetKey(["key_prefix", "bar"])})
    def qux(baz):
        return baz

    job = build_assets_job("a", [foo, bar, baz, qux])

    dep_structure_snapshot = build_dep_structure_snapshot_from_icontains_solids(job.graph)
    index = DependencyStructureIndex(dep_structure_snapshot)

    assert index.get_invocation("foo")
    assert index.get_invocation("key_prefix__bar")
    assert index.get_invocation("baz")

    assert index.get_upstream_outputs("qux", "foo") == [
        OutputHandleSnap("foo", "result"),
    ]
    assert index.get_upstream_outputs("qux", "key_prefix_bar") == [
        OutputHandleSnap("key_prefix__bar", "result")
    ]
    assert index.get_upstream_outputs("qux", "baz") == [OutputHandleSnap("baz", "result")]

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("qux") == 1
    assert _asset_keys_for_node(result, "key_prefix__bar") == {AssetKey(["key_prefix", "bar"])}
    assert _asset_keys_for_node(result, "qux") == {AssetKey("qux")}


def test_basic_graph_asset():
    @op
    def return_one():
        return 1

    @op
    def add_one(in1):
        return in1 + 1

    @graph
    def create_cool_thing():
        return add_one(add_one(return_one()))

    cool_thing_asset = AssetsDefinition(
        keys_by_input_name={},
        keys_by_output_name={"result": AssetKey("cool_thing")},
        node_def=create_cool_thing,
    )
    job = build_assets_job("graph_asset_job", [cool_thing_asset])

    result = job.execute_in_process()
    assert _asset_keys_for_node(result, "create_cool_thing.add_one_2") == {AssetKey("cool_thing")}


def test_input_mapped_graph_asset():
    @asset
    def a():
        return "a"

    @asset
    def b():
        return "b"

    @op
    def double_string(s):
        return s * 2

    @op
    def combine_strings(s1, s2):
        return s1 + s2

    @graph
    def create_cool_thing(a, b):
        da = double_string(double_string(a))
        db = double_string(b)
        return combine_strings(da, db)

    cool_thing_asset = AssetsDefinition(
        keys_by_input_name={"a": AssetKey("a"), "b": AssetKey("b")},
        keys_by_output_name={"result": AssetKey("cool_thing")},
        node_def=create_cool_thing,
    )

    job = build_assets_job("graph_asset_job", [a, b, cool_thing_asset])

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("create_cool_thing.combine_strings") == "aaaabb"
    assert _asset_keys_for_node(result, "create_cool_thing") == {AssetKey("cool_thing")}
    assert _asset_keys_for_node(result, "create_cool_thing.combine_strings") == {
        AssetKey("cool_thing")
    }


def test_output_mapped_same_op_graph_asset():
    @asset
    def a():
        return "a"

    @asset
    def b():
        return "b"

    @op
    def double_string(s):
        return s * 2

    @op(out={"ns1": Out(), "ns2": Out()})
    def combine_strings_and_split(s1, s2):
        return (s1 + s2, s2 + s1)

    @graph(out={"o1": GraphOut(), "o2": GraphOut()})
    def create_cool_things(a, b):
        da = double_string(double_string(a))
        db = double_string(b)
        o1, o2 = combine_strings_and_split(da, db)
        return o1, o2

    @asset
    def out_asset1_plus_one(out_asset1):
        return out_asset1 + "one"

    @asset
    def out_asset2_plus_one(out_asset2):
        return out_asset2 + "one"

    complex_asset = AssetsDefinition(
        keys_by_input_name={"a": AssetKey("a"), "b": AssetKey("b")},
        keys_by_output_name={"o1": AssetKey("out_asset1"), "o2": AssetKey("out_asset2")},
        node_def=create_cool_things,
    )

    job = build_assets_job(
        "graph_asset_job", [a, b, complex_asset, out_asset1_plus_one, out_asset2_plus_one]
    )

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("out_asset1_plus_one") == "aaaabbone"
    assert result.output_for_node("out_asset2_plus_one") == "bbaaaaone"

    assert _asset_keys_for_node(result, "create_cool_things") == {
        AssetKey("out_asset1"),
        AssetKey("out_asset2"),
    }
    assert _asset_keys_for_node(result, "create_cool_things.combine_strings_and_split") == {
        AssetKey("out_asset1"),
        AssetKey("out_asset2"),
    }


def test_output_mapped_different_op_graph_asset():
    @asset
    def a():
        return "a"

    @asset
    def b():
        return "b"

    @op
    def double_string(s):
        return s * 2

    @op(out={"ns1": Out(), "ns2": Out()})
    def combine_strings_and_split(s1, s2):
        return (s1 + s2, s2 + s1)

    @graph(out={"o1": GraphOut(), "o2": GraphOut()})
    def create_cool_things(a, b):
        ab, ba = combine_strings_and_split(a, b)
        dab = double_string(ab)
        dba = double_string(ba)
        return dab, dba

    @asset
    def out_asset1_plus_one(out_asset1):
        return out_asset1 + "one"

    @asset
    def out_asset2_plus_one(out_asset2):
        return out_asset2 + "one"

    complex_asset = AssetsDefinition(
        keys_by_input_name={"a": AssetKey("a"), "b": AssetKey("b")},
        keys_by_output_name={"o1": AssetKey("out_asset1"), "o2": AssetKey("out_asset2")},
        node_def=create_cool_things,
    )

    job = build_assets_job(
        "graph_asset_job", [a, b, complex_asset, out_asset1_plus_one, out_asset2_plus_one]
    )

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("out_asset1_plus_one") == "ababone"
    assert result.output_for_node("out_asset2_plus_one") == "babaone"

    assert _asset_keys_for_node(result, "create_cool_things") == {
        AssetKey("out_asset1"),
        AssetKey("out_asset2"),
    }
    assert _asset_keys_for_node(result, "create_cool_things.double_string") == {
        AssetKey("out_asset1")
    }
    assert _asset_keys_for_node(result, "create_cool_things.double_string_2") == {
        AssetKey("out_asset2")
    }


def test_nasty_nested_graph_assets():
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
    )

    thirteen_and_six = AssetsDefinition(
        keys_by_input_name={
            "eight": AssetKey("eight"),
            "five": AssetKey("five"),
            "zero": AssetKey("zero"),
        },
        keys_by_output_name={"thirteen": AssetKey("thirteen"), "six": AssetKey("six")},
        node_def=create_thirteen_and_six,
    )

    twenty = AssetsDefinition(
        keys_by_input_name={"thirteen": AssetKey("thirteen"), "six": AssetKey("six")},
        keys_by_output_name={"result": AssetKey("twenty")},
        node_def=create_twenty,
    )

    job = build_assets_job("graph_asset_job", [zero, eight_and_five, thirteen_and_six, twenty])

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("create_thirteen_and_six", "six") == 6
    assert result.output_for_node("create_twenty") == 20
    assert _asset_keys_for_node(result, "create_eight_and_five") == {
        AssetKey("eight"),
        AssetKey("five"),
    }
    assert _asset_keys_for_node(result, "create_thirteen_and_six") == {
        AssetKey("thirteen"),
        AssetKey("six"),
    }
    assert _asset_keys_for_node(result, "create_twenty") == {AssetKey("twenty")}


def test_internal_asset_deps():
    @op
    def my_op(x, y):  # pylint: disable=unused-argument
        return x

    with pytest.raises(Exception, match="output_name non_exist_output_name"):

        @graph(ins={"x": GraphIn()})
        def my_graph(x, y):
            my_op(x, y)

        AssetsDefinition.from_graph(
            graph_def=my_graph, internal_asset_deps={"non_exist_output_name": {AssetKey("b")}}
        )

    with pytest.raises(Exception, match="output_name non_exist_output_name"):
        AssetsDefinition.from_op(
            op_def=my_op, internal_asset_deps={"non_exist_output_name": {AssetKey("b")}}
        )


def test_asset_def_from_op_inputs():
    @op(ins={"my_input": In(), "other_input": In()}, out={"out1": Out(), "out2": Out()})
    def my_op(my_input, other_input):  # pylint: disable=unused-argument
        pass

    assets_def = AssetsDefinition.from_op(
        op_def=my_op,
        keys_by_input_name={"my_input": AssetKey("x_asset"), "other_input": AssetKey("y_asset")},
    )

    assert assets_def.keys_by_input_name["my_input"] == AssetKey("x_asset")
    assert assets_def.keys_by_input_name["other_input"] == AssetKey("y_asset")
    assert assets_def.keys_by_output_name["out1"] == AssetKey("out1")
    assert assets_def.keys_by_output_name["out2"] == AssetKey("out2")


def test_asset_def_from_op_outputs():
    @op(ins={"my_input": In(), "other_input": In()}, out={"out1": Out(), "out2": Out()})
    def x_op(my_input, other_input):  # pylint: disable=unused-argument
        pass

    assets_def = AssetsDefinition.from_op(
        op_def=x_op,
        keys_by_output_name={"out2": AssetKey("y_asset"), "out1": AssetKey("x_asset")},
    )

    assert assets_def.keys_by_output_name["out2"] == AssetKey("y_asset")
    assert assets_def.keys_by_output_name["out1"] == AssetKey("x_asset")
    assert assets_def.keys_by_input_name["my_input"] == AssetKey("my_input")
    assert assets_def.keys_by_input_name["other_input"] == AssetKey("other_input")


def test_asset_from_op_no_args():
    @op
    def my_op(x, y):  # pylint: disable=unused-argument
        return x

    assets_def = AssetsDefinition.from_op(
        op_def=my_op,
    )

    assert assets_def.keys_by_input_name["x"] == AssetKey("x")
    assert assets_def.keys_by_input_name["y"] == AssetKey("y")
    assert assets_def.keys_by_output_name["result"] == AssetKey("my_op")


def test_asset_def_from_graph_inputs():
    @op
    def my_op(x, y):  # pylint: disable=unused-argument
        return x

    @graph(ins={"x": GraphIn(), "y": GraphIn()})
    def my_graph(x, y):
        return my_op(x, y)

    assets_def = AssetsDefinition.from_graph(
        graph_def=my_graph,
        keys_by_input_name={"x": AssetKey("x_asset"), "y": AssetKey("y_asset")},
    )

    assert assets_def.keys_by_input_name["x"] == AssetKey("x_asset")
    assert assets_def.keys_by_input_name["y"] == AssetKey("y_asset")


def test_asset_def_from_graph_outputs():
    @op
    def x_op(x):
        return x

    @op
    def y_op(y):
        return y

    @graph(out={"x": GraphOut(), "y": GraphOut()})
    def my_graph(x, y):
        return {"x": x_op(x), "y": y_op(y)}

    assets_def = AssetsDefinition.from_graph(
        graph_def=my_graph,
        keys_by_output_name={"y": AssetKey("y_asset"), "x": AssetKey("x_asset")},
    )

    assert assets_def.keys_by_output_name["y"] == AssetKey("y_asset")
    assert assets_def.keys_by_output_name["x"] == AssetKey("x_asset")


def test_graph_asset_decorator_no_args():
    @op
    def my_op(x, y):  # pylint: disable=unused-argument
        return x

    @graph
    def my_graph(x, y):
        return my_op(x, y)

    assets_def = AssetsDefinition.from_graph(
        graph_def=my_graph,
    )

    assert assets_def.keys_by_input_name["x"] == AssetKey("x")
    assert assets_def.keys_by_input_name["y"] == AssetKey("y")
    assert assets_def.keys_by_output_name["result"] == AssetKey("my_graph")


def test_graph_asset_group_name():
    @op
    def my_op1(x):  # pylint: disable=unused-argument
        return x

    @op
    def my_op2(y):
        return y

    @graph
    def my_graph(x):
        return my_op2(my_op1(x))

    assets_def = AssetsDefinition.from_graph(
        graph_def=my_graph,
        group_name="group1",
    )

    # The asset key is the function name when there is only one output
    assert assets_def.group_names_by_key[AssetKey("my_graph")] == "group1"


def test_graph_asset_group_name_for_multiple_assets():
    @op(out={"first_output": Out(), "second_output": Out()})
    def two_outputs():
        return 1, 2

    @graph(out={"first_asset": GraphOut(), "second_asset": GraphOut()})
    def two_assets_graph():
        one, two = two_outputs()
        return {"first_asset": one, "second_asset": two}

    two_assets = AssetsDefinition.from_graph(two_assets_graph, group_name="group2")
    # same as above but using keys_by_output_name to assign AssetKey to each output
    two_assets_with_keys = AssetsDefinition.from_graph(
        two_assets_graph,
        keys_by_output_name={
            "first_asset": AssetKey("first_asset_key"),
            "second_asset": AssetKey("second_asset_key"),
        },
        group_name="group3",
    )

    assert two_assets.group_names_by_key[AssetKey("first_asset")] == "group2"
    assert two_assets.group_names_by_key[AssetKey("second_asset")] == "group2"

    assert two_assets_with_keys.group_names_by_key[AssetKey("first_asset_key")] == "group3"
    assert two_assets_with_keys.group_names_by_key[AssetKey("second_asset_key")] == "group3"


def test_execute_graph_asset():
    @op(out={"x": Out(), "y": Out()})
    def x_op(context):
        assert context.asset_key_for_output("x") == AssetKey("x_asset")
        return 1, 2

    @graph(out={"x": GraphOut(), "y": GraphOut()})
    def my_graph():
        x, y = x_op()
        return {"x": x, "y": y}

    assets_def = AssetsDefinition.from_graph(
        graph_def=my_graph,
        keys_by_output_name={"y": AssetKey("y_asset"), "x": AssetKey("x_asset")},
    )

    assert AssetGroup([assets_def]).build_job("abc").execute_in_process().success


def test_graph_asset_partitioned():
    @op
    def my_op(context):
        assert context.partition_key == "a"

    @graph
    def my_graph():
        return my_op()

    assets_def = AssetsDefinition.from_graph(
        graph_def=my_graph, partitions_def=StaticPartitionsDefinition(["a", "b", "c"])
    )

    AssetGroup([assets_def]).build_job("abc").execute_in_process(partition_key="a")


def test_all_assets_job():
    @asset
    def a1():
        return 1

    @asset
    def a2(a1):  # pylint: disable=unused-argument
        return 2

    job = build_assets_job("graph_asset_job", [a1, a2])
    node_handle_deps_by_asset = job.asset_layer.dependency_node_handles_by_asset_key

    assert node_handle_deps_by_asset[AssetKey("a1")] == {
        NodeHandle("a1", parent=None),
    }
    assert node_handle_deps_by_asset[AssetKey("a2")] == {NodeHandle("a2", parent=None)}


def test_basic_graph():
    @op
    def get_string():
        return "foo"

    @op(out={"ns1": Out(), "ns2": Out()})
    def combine_strings_and_split(s1, s2):
        return (s1 + s2, s2 + s1)

    @graph(out={"o1": GraphOut()})
    def thing():
        da = get_string()
        db = get_string()
        o1, o2 = combine_strings_and_split(da, db)  # pylint: disable=unused-variable
        return o1

    @asset
    def out_asset1_plus_one(out_asset1):
        return out_asset1 + "one"

    @asset
    def out_asset2_plus_one(out_asset2):
        return out_asset2 + "one"

    complex_asset = AssetsDefinition(
        keys_by_input_name={},
        keys_by_output_name={"o1": AssetKey("out_asset1")},
        node_def=thing,
    )

    job = build_assets_job("graph_asset_job", [complex_asset])
    node_handle_deps_by_asset = job.asset_layer.dependency_node_handles_by_asset_key

    thing_handle = NodeHandle(name="thing", parent=None)
    assert node_handle_deps_by_asset[AssetKey("out_asset1")] == {
        NodeHandle("get_string", parent=thing_handle),
        NodeHandle("get_string_2", parent=thing_handle),
        NodeHandle("combine_strings_and_split", parent=thing_handle),
    }


def test_hanging_op_graph():
    @op
    def get_string():
        return "foo"

    @op
    def combine_strings(s1, s2):
        return s1 + s2

    @op
    def hanging_op():
        return "bar"

    @graph(out={"o1": GraphOut(), "o2": GraphOut()})
    def thing():
        da = get_string()
        db = get_string()
        o1 = combine_strings(da, db)
        o2 = hanging_op()
        return {"o1": o1, "o2": o2}

    complex_asset = AssetsDefinition(
        keys_by_input_name={},
        keys_by_output_name={"o1": AssetKey("out_asset1"), "o2": AssetKey("out_asset2")},
        node_def=thing,
    )
    job = build_assets_job("graph_asset_job", [complex_asset])
    node_handle_deps_by_asset = job.asset_layer.dependency_node_handles_by_asset_key

    thing_handle = NodeHandle(name="thing", parent=None)
    assert node_handle_deps_by_asset[AssetKey("out_asset1")] == {
        NodeHandle("get_string", parent=thing_handle),
        NodeHandle("get_string_2", parent=thing_handle),
        NodeHandle("combine_strings", parent=thing_handle),
    }
    assert node_handle_deps_by_asset[AssetKey("out_asset2")] == {
        NodeHandle("hanging_op", parent=thing_handle),
    }


def test_nested_graph():
    @op
    def get_inside_string():
        return "bar"

    @graph(out={"o2": GraphOut()})
    def inside_thing():
        return get_inside_string()

    @op
    def get_string():
        return "foo"

    @op(out={"ns1": Out(), "ns2": Out()})
    def combine_strings_and_split(s1, s2):
        return (s1 + s2, s2 + s1)

    @graph(out={"o1": GraphOut()})
    def thing():
        da = inside_thing()
        db = get_string()
        o1, o2 = combine_strings_and_split(da, db)  # pylint: disable=unused-variable
        return o1

    thing_asset = AssetsDefinition(
        keys_by_input_name={},
        keys_by_output_name={"o1": AssetKey("thing")},
        node_def=thing,
    )

    job = build_assets_job("graph_asset_job", [thing_asset])
    node_handle_deps_by_asset = job.asset_layer.dependency_node_handles_by_asset_key

    thing_handle = NodeHandle(name="thing", parent=None)
    assert node_handle_deps_by_asset[AssetKey("thing")] == {
        NodeHandle("get_inside_string", parent=NodeHandle("inside_thing", parent=thing_handle)),
        NodeHandle("get_string", parent=thing_handle),
        NodeHandle("combine_strings_and_split", parent=thing_handle),
    }


def test_asset_in_nested_graph():
    @op
    def get_inside_string():
        return "bar"

    @op
    def get_string():
        return "foo"

    @graph(out={"n1": GraphOut(), "n2": GraphOut()})
    def inside_thing():
        n1 = get_inside_string()
        n2 = get_string()
        return n1, n2

    @op
    def get_transformed_string(string):
        return string + "qux"

    @graph(out={"o1": GraphOut(), "o3": GraphOut()})
    def thing():
        o1, o2 = inside_thing()
        o3 = get_transformed_string(o2)
        return (o1, o3)

    thing_asset = AssetsDefinition(
        keys_by_input_name={},
        keys_by_output_name={"o1": AssetKey("thing"), "o3": AssetKey("thing_2")},
        node_def=thing,
    )

    job = build_assets_job("graph_asset_job", [thing_asset])
    node_handle_deps_by_asset = job.asset_layer.dependency_node_handles_by_asset_key

    thing_handle = NodeHandle(name="thing", parent=None)
    assert node_handle_deps_by_asset[AssetKey("thing")] == {
        NodeHandle("get_inside_string", parent=NodeHandle("inside_thing", parent=thing_handle)),
    }
    assert node_handle_deps_by_asset[AssetKey("thing_2")] == {
        NodeHandle("get_string", parent=NodeHandle("inside_thing", parent=thing_handle)),
        NodeHandle("get_transformed_string", parent=thing_handle),
    }


def test_twice_nested_graph():
    @op
    def get_inside_string():
        return "bar"

    @op
    def get_string():
        return "foo"

    @graph(out={"n1": GraphOut(), "n2": GraphOut()})
    def innermost_thing():
        n1 = get_inside_string()
        n2 = get_string()
        return {"n1": n1, "n2": n2}

    @op
    def transformer(string):
        return string + "qux"

    @op
    def combiner(s1, s2):
        return s1 + s2

    @graph(out={"n1": GraphOut(), "n2": GraphOut(), "unused": GraphOut()})
    def middle_thing():
        n1, unused_output = innermost_thing()
        n2 = get_string()
        return {"n1": n1, "n2": n2, "unused": unused_output}

    @graph(out={"n1": GraphOut(), "n2": GraphOut(), "unused": GraphOut()})
    def outer_thing(foo_asset):
        n1, output, unused_output = middle_thing()
        n2 = transformer(output)
        unused_output = combiner(unused_output, transformer(foo_asset))
        return {"n1": n1, "n2": n2, "unused": unused_output}

    @asset
    def foo_asset():
        return "foo"

    thing_asset = AssetsDefinition.from_graph(
        graph_def=outer_thing,
        keys_by_input_name={},
        keys_by_output_name={
            "n1": AssetKey("thing"),
            "n2": AssetKey("thing_2"),
            "unused": AssetKey("asjdlaksjhbdluuawubn"),
        },
    )

    job = build_assets_job("graph_asset_job", [foo_asset, thing_asset])
    node_handle_deps_by_asset = job.asset_layer.dependency_node_handles_by_asset_key

    outer_thing_handle = NodeHandle("outer_thing", parent=None)
    middle_thing_handle = NodeHandle("middle_thing", parent=outer_thing_handle)
    assert node_handle_deps_by_asset[AssetKey("thing")] == {
        NodeHandle(
            "get_inside_string",
            parent=NodeHandle(
                "innermost_thing",
                parent=middle_thing_handle,
            ),
        )
    }
    assert node_handle_deps_by_asset[AssetKey("thing_2")] == {
        NodeHandle("get_string", parent=middle_thing_handle),
        NodeHandle("transformer", parent=outer_thing_handle),
    }
    assert node_handle_deps_by_asset[AssetKey("foo_asset")] == {
        NodeHandle("foo_asset", parent=None)
    }


def test_internal_asset_deps_assets():
    @op
    def upstream_op():
        return "foo"

    @op(out={"o1": Out(), "o2": Out()})
    def two_outputs(upstream_op):
        o1 = upstream_op
        o2 = o1 + "bar"
        return o1, o2

    @graph(out={"o1": GraphOut(), "o2": GraphOut()})
    def thing():
        o1, o2 = two_outputs(upstream_op())
        return (o1, o2)

    thing_asset = AssetsDefinition(
        keys_by_input_name={},
        keys_by_output_name={"o1": AssetKey("thing"), "o2": AssetKey("thing_2")},
        node_def=thing,
        asset_deps={AssetKey("thing"): set(), AssetKey("thing_2"): {AssetKey("thing")}},
    )

    @multi_asset(
        outs={
            "my_out_name": AssetOut(metadata={"foo": "bar"}),
            "my_other_out_name": AssetOut(metadata={"bar": "foo"}),
        },
        internal_asset_deps={
            "my_out_name": {AssetKey("my_other_out_name")},
            "my_other_out_name": {AssetKey("thing")},
        },
    )
    def multi_asset_with_internal_deps(thing):  # pylint: disable=unused-argument
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    job = build_assets_job("graph_asset_job", [thing_asset, multi_asset_with_internal_deps])
    node_handle_deps_by_asset = job.asset_layer.dependency_node_handles_by_asset_key
    assert node_handle_deps_by_asset[AssetKey("thing")] == {
        NodeHandle("two_outputs", parent=NodeHandle("thing", parent=None)),
        NodeHandle(name="upstream_op", parent=NodeHandle(name="thing", parent=None)),
    }
    assert node_handle_deps_by_asset[AssetKey("thing_2")] == {
        NodeHandle("two_outputs", parent=NodeHandle("thing", parent=None))
    }

    assert node_handle_deps_by_asset[AssetKey("my_out_name")] == {
        NodeHandle(name="multi_asset_with_internal_deps", parent=None)
    }
    assert node_handle_deps_by_asset[AssetKey("my_other_out_name")] == {
        NodeHandle(name="multi_asset_with_internal_deps", parent=None)
    }


@multi_asset(
    outs={"a": AssetOut(is_required=False), "b": AssetOut(is_required=False)}, can_subset=True
)
def ab(context, foo):
    if "a" in context.selected_output_names:
        yield Output(foo + 1, "a")
    if "b" in context.selected_output_names:
        yield Output(foo + 2, "b")


@asset
def foo():
    return 5


@asset
def bar():
    return 10


@asset
def foo_bar(foo, bar):
    return foo + bar


@asset
def baz(foo_bar):
    return foo_bar


@asset
def unconnected():
    pass


asset_group = AssetGroup([foo, ab, bar, foo_bar, baz, unconnected])


def test_disconnected_subset():
    with instance_for_test() as instance:
        job = asset_group.build_job("foo")
        result = job.execute_in_process(
            instance=instance, asset_selection=[AssetKey("unconnected"), AssetKey("bar")]
        )
        materialization_events = [
            event for event in result.all_events if event.is_step_materialization
        ]

        assert len(materialization_events) == 2
        assert materialization_events[0].asset_key == AssetKey("bar")
        assert materialization_events[1].asset_key == AssetKey("unconnected")


def test_connected_subset():
    with instance_for_test() as instance:
        job = asset_group.build_job("foo")
        result = job.execute_in_process(
            instance=instance,
            asset_selection=[AssetKey("foo"), AssetKey("bar"), AssetKey("foo_bar")],
        )
        materialization_events = sorted(
            [event for event in result.all_events if event.is_step_materialization],
            key=lambda event: event.asset_key,
        )

        assert len(materialization_events) == 3
        assert materialization_events[0].asset_key == AssetKey("bar")
        assert materialization_events[1].asset_key == AssetKey("foo")
        assert materialization_events[2].asset_key == AssetKey("foo_bar")


def test_subset_of_asset_job():
    with instance_for_test() as instance:
        foo_job = asset_group.build_job("foo_job", selection=["*baz"])
        result = foo_job.execute_in_process(
            instance=instance,
            asset_selection=[AssetKey("foo"), AssetKey("bar"), AssetKey("foo_bar")],
        )
        materialization_events = sorted(
            [event for event in result.all_events if event.is_step_materialization],
            key=lambda event: event.asset_key,
        )
        assert len(materialization_events) == 3
        assert materialization_events[0].asset_key == AssetKey("bar")
        assert materialization_events[1].asset_key == AssetKey("foo")
        assert materialization_events[2].asset_key == AssetKey("foo_bar")

        # with pytest.raises(DagsterInvalidSubsetError):
        #     result = foo_job.execute_in_process(
        #         instance=instance,
        #         asset_selection=[AssetKey("unconnected")],
        #     )


def test_subset_of_build_assets_job():
    foo_job = build_assets_job("foo_job", assets=[foo, bar, foo_bar, baz])
    with instance_for_test() as instance:
        result = foo_job.execute_in_process(
            instance=instance,
            asset_selection=[AssetKey("foo"), AssetKey("bar"), AssetKey("foo_bar")],
        )
        materialization_events = sorted(
            [event for event in result.all_events if event.is_step_materialization],
            key=lambda event: event.asset_key,
        )
        assert len(materialization_events) == 3
        assert materialization_events[0].asset_key == AssetKey("bar")
        assert materialization_events[1].asset_key == AssetKey("foo")
        assert materialization_events[2].asset_key == AssetKey("foo_bar")

        with pytest.raises(DagsterInvalidSubsetError):
            result = foo_job.execute_in_process(
                instance=instance,
                asset_selection=[AssetKey("unconnected")],
            )


@resource
def my_resource():
    return 1


@resource
def my_resource_2():
    return 1


@multi_asset(
    name="fivetran_sync",
    outs={key: AssetOut(key=AssetKey(key)) for key in ["a", "b", "c"]},
)
def fivetran_asset():
    return 1, 2, 3


@op(
    name="dbt",
    ins={
        "a": In(Nothing),
        "b": In(Nothing),
        "c": In(Nothing),
    },
    out={
        "d": Out(is_required=False),
        "e": Out(is_required=False),
        "f": Out(is_required=False),
    },
    required_resource_keys={"my_resource_2"},
)
def dbt_op():
    yield Output(4, "f")


dbt_asset_def = AssetsDefinition(
    keys_by_output_name={k: AssetKey(k) for k in ["d", "e", "f"]},
    keys_by_input_name={k: AssetKey(k) for k in ["a", "b", "c"]},
    node_def=dbt_op,
    can_subset=True,
    asset_deps={
        AssetKey("d"): {AssetKey("a")},
        AssetKey("e"): {AssetKey("d"), AssetKey("b")},
        AssetKey("f"): {AssetKey("d"), AssetKey("e")},
    },
)

my_job = define_asset_job("foo", selection=["a", "b", "c", "d", "e", "f"]).resolve(
    with_resources(
        [dbt_asset_def, fivetran_asset],
        resource_defs={"my_resource": my_resource, "my_resource_2": my_resource_2},
    ),
    [],
)


def reconstruct_asset_job():
    return my_job


def test_asset_selection_reconstructable():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=ExperimentalWarning)
        warnings.simplefilter("ignore", category=DeprecationWarning)
        with instance_for_test() as instance:
            run = instance.create_run_for_pipeline(
                pipeline_def=my_job, asset_selection=frozenset([AssetKey("f")])
            )
            reconstructable_foo_job = build_reconstructable_job(
                "dagster_tests.asset_defs_tests.test_assets_job",
                "reconstruct_asset_job",
                reconstructable_args=tuple(),
                reconstructable_kwargs={},
            ).subset_for_execution(asset_selection=frozenset([AssetKey("f")]))

            events = list(execute_run_iterator(reconstructable_foo_job, run, instance=instance))
            assert len([event for event in events if event.is_pipeline_success]) == 1

            materialization_planned = list(
                instance.get_event_records(
                    EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
                )
            )
            assert len(materialization_planned) == 1


def test_job_preserved_with_asset_subset():
    # Assert that default config is used for asset subset

    @op(config_schema={"foo": int})
    def one(context):
        assert context.op_config["foo"] == 1

    asset_one = AssetsDefinition.from_op(one)

    @asset(config_schema={"bar": int})
    def two(context, one):  # pylint: disable=unused-argument
        assert context.op_config["bar"] == 2

    @asset(config_schema={"baz": int})
    def three(context, two):  # pylint: disable=unused-argument
        assert context.op_config["baz"] == 3

    foo_job = define_asset_job(
        "foo_job",
        config={
            "ops": {
                "one": {"config": {"foo": 1}},
                "two": {"config": {"bar": 2}},
                "three": {"config": {"baz": 3}},
            }
        },
        description="my cool job",
        tags={"yay": 1},
    ).resolve([asset_one, two, three], [])

    result = foo_job.execute_in_process(asset_selection=[AssetKey("one")])
    assert result.success
    assert result.dagster_run.tags == {"yay": "1"}


def test_job_default_config_preserved_with_asset_subset():
    # Assert that default config is used for asset subset

    @op(config_schema={"foo": Field(int, default_value=1)})
    def one(context):
        assert context.op_config["foo"] == 1

    asset_one = AssetsDefinition.from_op(one)

    @asset(config_schema={"bar": Field(int, default_value=2)})
    def two(context, one):  # pylint: disable=unused-argument
        assert context.op_config["bar"] == 2

    @asset(config_schema={"baz": Field(int, default_value=3)})
    def three(context, two):  # pylint: disable=unused-argument
        assert context.op_config["baz"] == 3

    foo_job = define_asset_job("foo_job").resolve([asset_one, two, three], [])

    result = foo_job.execute_in_process(asset_selection=[AssetKey("one")])
    assert result.success


def test_empty_asset_job():
    @asset
    def a():
        pass

    @asset
    def b(a):
        pass

    empty_selection = AssetSelection.keys("a", "b") - AssetSelection.keys("a", "b")
    assert empty_selection.resolve([a, b]) == set()

    empty_job = define_asset_job("empty_job", selection=empty_selection).resolve([a, b], [])
    assert empty_job.all_node_defs == []

    result = empty_job.execute_in_process()
    assert result.success


def test_raise_error_on_incomplete_graph_asset_subset():
    @op
    def do_something(x):
        return x * 2

    @op
    def foo():
        return 1, 2

    @graph(
        out={
            "comments_table": GraphOut(),
            "stories_table": GraphOut(),
        },
    )
    def complicated_graph():
        result = foo()
        return do_something(result), do_something(result)

    job = AssetGroup(
        [
            AssetsDefinition.from_graph(complicated_graph),
        ],
    ).build_job("job")

    with instance_for_test() as instance:
        with pytest.raises(DagsterInvalidSubsetError, match="complicated_graph"):
            job.execute_in_process(instance=instance, asset_selection=[AssetKey("comments_table")])


def test_multi_subset():
    with instance_for_test() as instance:
        job = asset_group.build_job("foo")
        result = job.execute_in_process(
            instance=instance,
            asset_selection=[AssetKey("foo"), AssetKey("a")],
        )
        materialization_events = sorted(
            [event for event in result.all_events if event.is_step_materialization],
            key=lambda event: event.asset_key,
        )

        assert len(materialization_events) == 2
        assert materialization_events[0].asset_key == AssetKey("a")
        assert materialization_events[1].asset_key == AssetKey("foo")


def test_multi_all():
    with instance_for_test() as instance:
        job = asset_group.build_job("foo")
        result = job.execute_in_process(
            instance=instance,
            asset_selection=[AssetKey("foo"), AssetKey("a"), AssetKey("b")],
        )
        materialization_events = sorted(
            [event for event in result.all_events if event.is_step_materialization],
            key=lambda event: event.asset_key,
        )

        assert len(materialization_events) == 3
        assert materialization_events[0].asset_key == AssetKey("a")
        assert materialization_events[1].asset_key == AssetKey("b")
        assert materialization_events[2].asset_key == AssetKey("foo")


def test_subset_with_source_asset():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @io_manager
    def the_manager():
        return MyIOManager()

    my_source_asset = SourceAsset(key=AssetKey("my_source_asset"), io_manager_key="the_manager")

    @asset
    def my_derived_asset(my_source_asset):
        return my_source_asset + 4

    source_asset_job = AssetGroup(
        assets=[my_derived_asset],
        source_assets=[my_source_asset],
        resource_defs={"the_manager": the_manager},
    ).build_job("source_asset_job")

    result = source_asset_job.execute_in_process(asset_selection=[AssetKey("my_derived_asset")])
    assert result.success


def test_op_outputs_with_default_asset_io_mgr():
    @op
    def return_stuff():
        return 12

    @op
    def transform(data):
        assert data == 12
        return data * 2

    @op
    def one_more_transformation(transformed_data):
        assert transformed_data == 24
        return transformed_data + 1

    @graph(
        out={
            "asset_1": GraphOut(),
            "asset_2": GraphOut(),
        },
    )
    def complicated_graph():
        result = return_stuff()
        return one_more_transformation(transform(result)), transform(result)

    @asset
    def my_asset(asset_1):
        assert asset_1 == 25
        return asset_1

    my_job = AssetGroup(
        [AssetsDefinition.from_graph(complicated_graph), my_asset],
    ).build_job("my_job", executor_def=in_process_executor)

    result = execute_pipeline(my_job)
    assert result.success


def test_graph_output_is_input_within_graph():
    @op
    def return_stuff():
        return 1

    @op
    def transform(data):
        return data * 2

    @op
    def one_more_transformation(transformed_data):
        return transformed_data + 1

    @graph(
        out={
            "one": GraphOut(),
            "two": GraphOut(),
        },
    )
    def nested():
        result = transform(return_stuff())
        return one_more_transformation(result), result

    @graph(
        out={
            "asset_1": GraphOut(),
            "asset_2": GraphOut(),
            "asset_3": GraphOut(),
        },
    )
    def complicated_graph():
        one, two = nested()
        return one, two, transform(two)

    my_job = AssetGroup(
        [AssetsDefinition.from_graph(complicated_graph)],
    ).build_job("my_job")

    result = my_job.execute_in_process()
    assert result.success

    assert result.output_for_node("complicated_graph.nested", "one") == 3
    assert result.output_for_node("complicated_graph.nested", "two") == 2

    assert result.output_for_node("complicated_graph", "asset_1") == 3
    assert result.output_for_node("complicated_graph", "asset_2") == 2
    assert result.output_for_node("complicated_graph", "asset_3") == 4


def test_source_asset_io_manager_def():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @io_manager
    def the_manager():
        return MyIOManager()

    my_source_asset = SourceAsset(key=AssetKey("my_source_asset"), io_manager_def=the_manager)

    @asset
    def my_derived_asset(my_source_asset):
        return my_source_asset + 4

    source_asset_job = build_assets_job(
        name="test", assets=[my_derived_asset], source_assets=[my_source_asset]
    )

    result = source_asset_job.execute_in_process(asset_selection=[AssetKey("my_derived_asset")])
    assert result.success
    assert result.output_for_node("my_derived_asset") == 9


def test_source_asset_io_manager_not_provided():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @io_manager
    def the_manager():
        return MyIOManager()

    my_source_asset = SourceAsset(key=AssetKey("my_source_asset"))

    @asset
    def my_derived_asset(my_source_asset):
        return my_source_asset + 4

    source_asset_job = build_assets_job(
        "the_job",
        assets=[my_derived_asset],
        source_assets=[my_source_asset],
        resource_defs={"io_manager": the_manager},
    )

    result = source_asset_job.execute_in_process(asset_selection=[AssetKey("my_derived_asset")])
    assert result.success
    assert result.output_for_node("my_derived_asset") == 9


def test_source_asset_io_manager_key_provided():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @io_manager
    def the_manager():
        return MyIOManager()

    my_source_asset = SourceAsset(key=AssetKey("my_source_asset"), io_manager_key="some_key")

    @asset
    def my_derived_asset(my_source_asset):
        return my_source_asset + 4

    source_asset_job = build_assets_job(
        "the_job",
        assets=[my_derived_asset],
        source_assets=[my_source_asset],
        resource_defs={"some_key": the_manager},
    )

    result = source_asset_job.execute_in_process(asset_selection=[AssetKey("my_derived_asset")])
    assert result.success
    assert result.output_for_node("my_derived_asset") == 9


def test_source_asset_requires_resource_defs():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @resource(required_resource_keys={"bar"})
    def foo_resource(context):
        assert context.resources.bar == "blah"

    @io_manager(required_resource_keys={"foo"})
    def the_manager():
        return MyIOManager()

    my_source_asset = SourceAsset(
        key=AssetKey("my_source_asset"),
        io_manager_def=the_manager,
        resource_defs={"foo": foo_resource, "bar": ResourceDefinition.hardcoded_resource("blah")},
    )

    @asset
    def my_derived_asset(my_source_asset):
        return my_source_asset + 4

    source_asset_job = build_assets_job(
        "the_job",
        assets=[my_derived_asset],
        source_assets=[my_source_asset],
    )

    result = source_asset_job.execute_in_process(asset_selection=[AssetKey("my_derived_asset")])
    assert result.success
    assert result.output_for_node("my_derived_asset") == 9


def test_other_asset_provides_req():
    # Demonstrate that assets cannot resolve each other's dependencies with
    # resources on each definition.
    @asset(required_resource_keys={"foo"})
    def asset_reqs_foo():
        pass

    @asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("blah")})
    def asset_provides_foo():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'foo' required by op 'asset_reqs_foo' was not provided.",
    ):
        build_assets_job(name="test", assets=[asset_reqs_foo, asset_provides_foo])


def test_transitive_deps_not_provided():
    @resource(required_resource_keys={"foo"})
    def unused_resource():
        pass

    @asset(resource_defs={"unused": unused_resource})
    def the_asset():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'foo' required by resource with key 'unused' was not provided.",
    ):
        build_assets_job(name="test", assets=[the_asset])


def test_transitive_resource_deps_provided():
    @resource(required_resource_keys={"foo"})
    def used_resource(context):
        assert context.resources.foo == "blah"

    @asset(
        resource_defs={"used": used_resource, "foo": ResourceDefinition.hardcoded_resource("blah")}
    )
    def the_asset():
        pass

    the_job = build_assets_job(name="test", assets=[the_asset])
    assert the_job.execute_in_process().success


def test_transitive_io_manager_dep_not_provided():
    @io_manager(required_resource_keys={"foo"})
    def the_manager():
        pass

    my_source_asset = SourceAsset(
        key=AssetKey("my_source_asset"),
        io_manager_def=the_manager,
    )

    @asset
    def my_derived_asset(my_source_asset):  # pylint: disable=unused-argument
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "resource with key 'foo' required by resource with key 'my_source_asset__io_manager'"
            " was not provided."
        ),
    ):
        build_assets_job(name="test", assets=[my_derived_asset], source_assets=[my_source_asset])


def test_resolve_dependency_in_group():
    @asset(key_prefix="abc")
    def asset1():
        ...

    @asset
    def asset2(context, asset1):
        del asset1
        assert context.asset_key_for_input("asset1") == AssetKey(["abc", "asset1"])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=ExperimentalWarning)

        assert materialize_to_memory([asset1, asset2]).success


def test_resolve_dependency_fail_across_groups():
    @asset(key_prefix="abc", group_name="other")
    def asset1():
        ...

    @asset
    def asset2(asset1):
        del asset1

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "is not produced by any of the provided asset ops and is not one of the provided"
            " sources"
        ),
    ):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)

            materialize_to_memory([asset1, asset2])


def test_resolve_dependency_multi_asset_different_groups():
    @asset(key_prefix="abc", group_name="a")
    def upstream():
        ...

    @op(out={"ns1": Out(), "ns2": Out()})
    def op1(upstream):
        del upstream

    assets = AssetsDefinition(
        keys_by_input_name={"upstream": AssetKey("upstream")},
        keys_by_output_name={"ns1": AssetKey("ns1"), "ns2": AssetKey("ns2")},
        node_def=op1,
        group_names_by_key={AssetKey("ns1"): "a", AssetKey("ns2"): "b"},
    )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "is not produced by any of the provided asset ops and is not one of the provided"
            " sources"
        ),
    ):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)

            materialize_to_memory([upstream, assets])


def test_get_base_asset_jobs_multiple_partitions_defs():
    @asset(partitions_def=DailyPartitionsDefinition(start_date="2021-05-05"))
    def daily_asset():
        ...

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2021-05-05"))
    def daily_asset2():
        ...

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-05-05"))
    def daily_asset_different_start_date():
        ...

    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2021-05-05-00:00"))
    def hourly_asset():
        ...

    @asset
    def unpartitioned_asset():
        ...

    jobs = get_base_asset_jobs(
        assets=[
            daily_asset,
            daily_asset2,
            daily_asset_different_start_date,
            hourly_asset,
            unpartitioned_asset,
        ],
        source_assets=[],
        executor_def=None,
        resource_defs={},
    )
    assert len(jobs) == 3
    assert {job_def.name for job_def in jobs} == {
        "__ASSET_JOB_0",
        "__ASSET_JOB_1",
        "__ASSET_JOB_2",
    }
    assert {
        frozenset([node_def.name for node_def in job_def.all_node_defs]) for job_def in jobs
    } == {
        frozenset(["daily_asset", "daily_asset2", "unpartitioned_asset"]),
        frozenset(["hourly_asset", "unpartitioned_asset"]),
        frozenset(["daily_asset_different_start_date", "unpartitioned_asset"]),
    }
