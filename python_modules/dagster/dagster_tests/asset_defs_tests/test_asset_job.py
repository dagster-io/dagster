import hashlib
import os
import re
import traceback

import dagster as dg
import dagster._check as check
import pytest
from dagster import (
    AssetsDefinition,
    DagsterEventType,
    Definitions,
    InputContext,
    Nothing,
    OutputContext,
    ResourceDefinition,
)
from dagster._core.definitions.asset_selection import AssetSelection, CoercibleToAssetSelection
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.definitions.dependency import NodeHandle
from dagster._core.definitions.executor_definition import in_process_executor
from dagster._core.execution.api import execute_run_iterator
from dagster._core.snap import DependencyStructureIndex
from dagster._core.snap.dep_snapshot import (
    OutputHandleSnap,
    build_dep_structure_snapshot_from_graph_def,
)
from dagster._core.test_utils import (
    create_test_asset_job,
    ignore_warning,
    raise_exception_on_warnings,
)
from dagster._utils import safe_tempfile_path
from dagster._utils.warnings import disable_dagster_warnings
from dagster_shared.error import SerializableErrorInfo


@pytest.fixture(autouse=True)
def error_on_warning():
    raise_exception_on_warnings()


def _all_asset_keys(result):
    mats = [
        event.event_specific_data.materialization
        for event in result.all_events
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    ret = {mat.asset_key for mat in mats}
    assert len(mats) == len(ret)
    return ret


def _asset_keys_for_node(result, node_name):
    mats = result.asset_materializations_for_node(node_name)
    ret = {mat.asset_key for mat in mats}
    assert len(mats) == len(ret)
    return ret


def test_single_asset_job():
    @dg.asset
    def asset1(context):
        assert context.asset_key == dg.AssetKey(["asset1"])
        return 1

    job = create_test_asset_job([asset1])
    assert job.graph.node_defs == [asset1.op]
    assert job.execute_in_process().success


def test_two_asset_job():
    @dg.asset
    def asset1():
        return 1

    @dg.asset
    def asset2(asset1):
        assert asset1 == 1

    job = create_test_asset_job([asset1, asset2])
    sorted_node_defs = sorted(job.graph.node_defs, key=lambda node_def: node_def.name)
    assert sorted_node_defs == [asset1.op, asset2.op]
    assert job.dependencies == {
        dg.NodeInvocation("asset1"): {},
        dg.NodeInvocation("asset2"): {"asset1": dg.DependencyDefinition("asset1", "result")},
    }
    assert job.execute_in_process().success


def test_single_asset_job_with_config():
    @dg.asset(config_schema={"foo": dg.Field(dg.StringSource)})
    def asset1(context):
        return context.op_execution_context.op_config["foo"]

    job = create_test_asset_job([asset1])
    assert job.graph.node_defs == [asset1.op]
    assert job.execute_in_process(
        run_config={"ops": {"asset1": {"config": {"foo": "bar"}}}}
    ).success


def test_fork():
    @dg.asset
    def asset1():
        return 1

    @dg.asset
    def asset2(asset1):
        assert asset1 == 1

    @dg.asset
    def asset3(asset1):
        assert asset1 == 1

    job = create_test_asset_job([asset1, asset2, asset3])
    sorted_node_defs = sorted(job.graph.node_defs, key=lambda node_def: node_def.name)
    assert sorted_node_defs == [asset1.op, asset2.op, asset3.op]
    assert job.dependencies == {
        dg.NodeInvocation("asset1"): {},
        dg.NodeInvocation("asset2"): {"asset1": dg.DependencyDefinition("asset1", "result")},
        dg.NodeInvocation("asset3"): {"asset1": dg.DependencyDefinition("asset1", "result")},
    }
    assert job.execute_in_process().success


def test_join():
    @dg.asset
    def asset1():
        return 1

    @dg.asset
    def asset2():
        return 2

    @dg.asset
    def asset3(asset1, asset2):
        assert asset1 == 1
        assert asset2 == 2

    job = create_test_asset_job([asset1, asset2, asset3])
    sorted_node_defs = sorted(job.graph.node_defs, key=lambda node_def: node_def.name)
    assert sorted_node_defs == [asset1.op, asset2.op, asset3.op]
    assert job.dependencies == {
        dg.NodeInvocation("asset1"): {},
        dg.NodeInvocation("asset2"): {},
        dg.NodeInvocation("asset3"): {
            "asset1": dg.DependencyDefinition("asset1", "result"),
            "asset2": dg.DependencyDefinition("asset2", "result"),
        },
    }
    result = job.execute_in_process()
    assert _asset_keys_for_node(result, "asset3") == {dg.AssetKey("asset3")}


def test_asset_key_output():
    @dg.asset
    def asset1():
        return 1

    @dg.asset(ins={"hello": dg.AssetIn(key=dg.AssetKey("asset1"))})
    def asset2(hello):
        return hello

    job = create_test_asset_job([asset1, asset2])
    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("asset2") == 1
    assert _asset_keys_for_node(result, "asset2") == {dg.AssetKey("asset2")}


def test_asset_key_matches_input_name():
    @dg.asset
    def asset_foo():
        return "foo"

    @dg.asset
    def asset_bar():
        return "bar"

    @dg.asset(
        ins={"asset_bar": dg.AssetIn(key=dg.AssetKey("asset_foo"))}
    )  # should still use output from asset_foo
    def last_asset(asset_bar):
        return asset_bar

    job = create_test_asset_job([asset_foo, asset_bar, last_asset])
    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("last_asset") == "foo"
    assert _asset_keys_for_node(result, "last_asset") == {dg.AssetKey("last_asset")}


def test_asset_key_and_inferred():
    @dg.asset
    def asset_foo():
        return 2

    @dg.asset
    def asset_bar():
        return 5

    @dg.asset(ins={"foo": dg.AssetIn(key=dg.AssetKey("asset_foo"))})
    def asset_baz(foo, asset_bar):
        return foo + asset_bar

    job = create_test_asset_job([asset_foo, asset_bar, asset_baz])
    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("asset_baz") == 7
    assert _asset_keys_for_node(result, "asset_baz") == {dg.AssetKey("asset_baz")}


def test_asset_key_for_asset_with_key_prefix_str():
    @dg.asset(key_prefix="hello")
    def asset_foo():
        return "foo"

    @dg.asset(ins={"foo": dg.AssetIn(key=dg.AssetKey(["hello", "asset_foo"]))})
    def success_asset(foo):
        return foo

    job = create_test_asset_job([asset_foo, success_asset])

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("success_asset") == "foo"
    assert _asset_keys_for_node(result, "hello__asset_foo") == {dg.AssetKey(["hello", "asset_foo"])}


@ignore_warning("Class `SourceAsset` is deprecated and will be removed in 2.0.0.")
def test_source_asset():
    @dg.asset
    def asset1(source1):
        assert source1 == 5
        return 1

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert context.resource_config["a"] == 7  # pyright: ignore[reportOptionalSubscript]
            assert context.resources.subresource == 9
            assert context.upstream_output.resources.subresource == 9  # pyright: ignore[reportOptionalMemberAccess]
            assert context.upstream_output.asset_key == dg.AssetKey("source1")  # pyright: ignore[reportOptionalMemberAccess]
            assert context.upstream_output.definition_metadata["a"] == "b"  # pyright: ignore[reportOptionalMemberAccess]
            assert context.upstream_output.resource_config["a"] == 7  # pyright: ignore[reportOptionalSubscript,reportOptionalMemberAccess]
            assert context.upstream_output.log is not None  # pyright: ignore[reportOptionalMemberAccess]
            context.upstream_output.log.info("hullo")  # pyright: ignore[reportOptionalMemberAccess]
            assert context.asset_key == dg.AssetKey("source1")
            return 5

    @dg.io_manager(config_schema={"a": int}, required_resource_keys={"subresource"})
    def my_io_manager(_):
        return MyIOManager()

    job = create_test_asset_job(
        [
            asset1,
            dg.SourceAsset(
                dg.AssetKey("source1"), io_manager_key="special_io_manager", metadata={"a": "b"}
            ),
        ],
        resources={
            "special_io_manager": my_io_manager.configured({"a": 7}),
            "subresource": ResourceDefinition.hardcoded_resource(9),
        },
    )
    assert job.graph.node_defs == [asset1.op]
    result = job.execute_in_process()
    assert result.success
    assert _asset_keys_for_node(result, "asset1") == {dg.AssetKey("asset1")}


@ignore_warning("Class `SourceAsset` is deprecated and will be removed in 2.0.0.")
def test_missing_io_manager():
    @dg.asset
    def asset1(source1):
        return source1

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"io manager with key 'special_io_manager' required by SourceAsset with key"
            r" \[\"source1\"\] was not provided."
        ),
    ):
        create_test_asset_job(
            [asset1, dg.SourceAsset(dg.AssetKey("source1"), io_manager_key="special_io_manager")],
        )


def test_source_op_asset():
    @dg.asset(io_manager_key="special_io_manager")
    def source1():
        pass

    @dg.asset
    def asset1(source1):
        assert source1 == 5
        return 1

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @dg.io_manager
    def my_io_manager(_):
        return MyIOManager()

    job = create_test_asset_job(
        [asset1, source1],
        selection=[asset1],
        resources={"special_io_manager": my_io_manager},
    )
    assert job.graph.node_defs == [asset1.op]
    result = job.execute_in_process()
    assert result.success
    assert _asset_keys_for_node(result, "asset1") == {dg.AssetKey("asset1")}


def test_deps():
    with safe_tempfile_path() as path:

        @dg.asset
        def foo():
            with open(path, "w", encoding="utf8") as ff:
                ff.write("yup")

        @dg.asset(deps=[dg.AssetKey("foo")])
        def bar():
            # assert that the foo asset already executed
            assert os.path.exists(path)

        job = create_test_asset_job([foo, bar])
        result = job.execute_in_process()
        assert result.success
        assert _asset_keys_for_node(result, "foo") == {dg.AssetKey("foo")}
        assert _asset_keys_for_node(result, "bar") == {dg.AssetKey("bar")}


def test_deps_as_str():
    @dg.asset
    def foo():
        pass

    @dg.asset(deps=["foo"])
    def bar():
        pass

    assert dg.AssetKey("foo") in bar.asset_deps[dg.AssetKey("bar")]


def test_multiple_deps():
    @dg.asset
    def foo():
        pass

    @dg.asset(key_prefix="key_prefix")
    def bar():
        pass

    @dg.asset
    def baz():
        return 1

    @dg.asset(deps=[dg.AssetKey("foo"), dg.AssetKey(["key_prefix", "bar"])])
    def qux(baz):
        return baz

    job = create_test_asset_job([foo, bar, baz, qux])

    dep_structure_snapshot = build_dep_structure_snapshot_from_graph_def(job.graph)
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
    assert _asset_keys_for_node(result, "key_prefix__bar") == {dg.AssetKey(["key_prefix", "bar"])}
    assert _asset_keys_for_node(result, "qux") == {dg.AssetKey("qux")}


def test_basic_graph_asset():
    @dg.op
    def return_one():
        return 1

    @dg.op
    def add_one(in1):
        return in1 + 1

    @dg.graph
    def create_cool_thing():
        return add_one(add_one(return_one()))

    cool_thing_asset = dg.AssetsDefinition(
        keys_by_input_name={},
        keys_by_output_name={"result": dg.AssetKey("cool_thing")},
        node_def=create_cool_thing,
    )
    job = create_test_asset_job([cool_thing_asset])

    result = job.execute_in_process()
    assert _asset_keys_for_node(result, "create_cool_thing.add_one_2") == {
        dg.AssetKey("cool_thing")
    }


def test_input_mapped_graph_asset():
    @dg.asset
    def a():
        return "a"

    @dg.asset
    def b():
        return "b"

    @dg.op
    def double_string(s):
        return s * 2

    @dg.op
    def combine_strings(s1, s2):
        return s1 + s2

    @dg.graph
    def create_cool_thing(a, b):
        da = double_string(double_string(a))
        db = double_string(b)
        return combine_strings(da, db)

    cool_thing_asset = dg.AssetsDefinition(
        keys_by_input_name={"a": dg.AssetKey("a"), "b": dg.AssetKey("b")},
        keys_by_output_name={"result": dg.AssetKey("cool_thing")},
        node_def=create_cool_thing,
    )

    job = create_test_asset_job([a, b, cool_thing_asset])

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("create_cool_thing.combine_strings") == "aaaabb"
    assert _asset_keys_for_node(result, "create_cool_thing") == {dg.AssetKey("cool_thing")}
    assert _asset_keys_for_node(result, "create_cool_thing.combine_strings") == {
        dg.AssetKey("cool_thing")
    }


def test_output_mapped_same_op_graph_asset():
    @dg.asset
    def a():
        return "a"

    @dg.asset
    def b():
        return "b"

    @dg.op
    def double_string(s):
        return s * 2

    @dg.op(out={"ns1": dg.Out(), "ns2": dg.Out()})
    def combine_strings_and_split(s1, s2):
        return (s1 + s2, s2 + s1)

    @dg.graph(out={"o1": dg.GraphOut(), "o2": dg.GraphOut()})
    def create_cool_things(a, b):
        da = double_string(double_string(a))
        db = double_string(b)
        o1, o2 = combine_strings_and_split(da, db)
        return o1, o2

    @dg.asset
    def out_asset1_plus_one(out_asset1):
        return out_asset1 + "one"

    @dg.asset
    def out_asset2_plus_one(out_asset2):
        return out_asset2 + "one"

    complex_asset = dg.AssetsDefinition(
        keys_by_input_name={"a": dg.AssetKey("a"), "b": dg.AssetKey("b")},
        keys_by_output_name={"o1": dg.AssetKey("out_asset1"), "o2": dg.AssetKey("out_asset2")},
        node_def=create_cool_things,
    )

    job = create_test_asset_job([a, b, complex_asset, out_asset1_plus_one, out_asset2_plus_one])

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("out_asset1_plus_one") == "aaaabbone"
    assert result.output_for_node("out_asset2_plus_one") == "bbaaaaone"

    assert _asset_keys_for_node(result, "create_cool_things") == {
        dg.AssetKey("out_asset1"),
        dg.AssetKey("out_asset2"),
    }
    assert _asset_keys_for_node(result, "create_cool_things.combine_strings_and_split") == {
        dg.AssetKey("out_asset1"),
        dg.AssetKey("out_asset2"),
    }


def test_output_mapped_different_op_graph_asset():
    @dg.asset
    def a():
        return "a"

    @dg.asset
    def b():
        return "b"

    @dg.op
    def double_string(s):
        return s * 2

    @dg.op(out={"ns1": dg.Out(), "ns2": dg.Out()})
    def combine_strings_and_split(s1, s2):
        return (s1 + s2, s2 + s1)

    @dg.graph(out={"o1": dg.GraphOut(), "o2": dg.GraphOut()})
    def create_cool_things(a, b):
        ab, ba = combine_strings_and_split(a, b)
        dab = double_string(ab)
        dba = double_string(ba)
        return dab, dba

    @dg.asset
    def out_asset1_plus_one(out_asset1):
        return out_asset1 + "one"

    @dg.asset
    def out_asset2_plus_one(out_asset2):
        return out_asset2 + "one"

    complex_asset = dg.AssetsDefinition(
        keys_by_input_name={"a": dg.AssetKey("a"), "b": dg.AssetKey("b")},
        keys_by_output_name={"o1": dg.AssetKey("out_asset1"), "o2": dg.AssetKey("out_asset2")},
        node_def=create_cool_things,
    )

    job = create_test_asset_job([a, b, complex_asset, out_asset1_plus_one, out_asset2_plus_one])

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("out_asset1_plus_one") == "ababone"
    assert result.output_for_node("out_asset2_plus_one") == "babaone"

    assert _asset_keys_for_node(result, "create_cool_things") == {
        dg.AssetKey("out_asset1"),
        dg.AssetKey("out_asset2"),
    }
    assert _asset_keys_for_node(result, "create_cool_things.double_string") == {
        dg.AssetKey("out_asset1")
    }
    assert _asset_keys_for_node(result, "create_cool_things.double_string_2") == {
        dg.AssetKey("out_asset2")
    }


def test_nasty_nested_graph_assets():
    @dg.op
    def add_one(i):
        return i + 1

    @dg.graph
    def add_three(i):
        return add_one(add_one(add_one(i)))

    @dg.graph
    def add_five(i):
        return add_one(add_three(add_one(i)))

    @dg.op
    def get_sum(a, b):
        return a + b

    @dg.graph
    def sum_plus_one(a, b):
        return add_one(get_sum(a, b))

    @dg.asset
    def zero():
        return 0

    @dg.graph(out={"eight": dg.GraphOut(), "five": dg.GraphOut()})
    def create_eight_and_five(zero):
        return add_five(add_three(zero)), add_five(zero)

    @dg.graph(out={"thirteen": dg.GraphOut(), "six": dg.GraphOut()})
    def create_thirteen_and_six(eight, five, zero):
        return add_five(eight), sum_plus_one(five, zero)

    @dg.graph
    def create_twenty(thirteen, six):
        return sum_plus_one(thirteen, six)

    eight_and_five = dg.AssetsDefinition(
        keys_by_input_name={"zero": dg.AssetKey("zero")},
        keys_by_output_name={"eight": dg.AssetKey("eight"), "five": dg.AssetKey("five")},
        node_def=create_eight_and_five,
    )

    thirteen_and_six = dg.AssetsDefinition(
        keys_by_input_name={
            "eight": dg.AssetKey("eight"),
            "five": dg.AssetKey("five"),
            "zero": dg.AssetKey("zero"),
        },
        keys_by_output_name={"thirteen": dg.AssetKey("thirteen"), "six": dg.AssetKey("six")},
        node_def=create_thirteen_and_six,
    )

    twenty = dg.AssetsDefinition(
        keys_by_input_name={"thirteen": dg.AssetKey("thirteen"), "six": dg.AssetKey("six")},
        keys_by_output_name={"result": dg.AssetKey("twenty")},
        node_def=create_twenty,
    )

    job = create_test_asset_job([zero, eight_and_five, thirteen_and_six, twenty])

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("create_thirteen_and_six", "six") == 6
    assert result.output_for_node("create_twenty") == 20
    assert _asset_keys_for_node(result, "create_eight_and_five") == {
        dg.AssetKey("eight"),
        dg.AssetKey("five"),
    }
    assert _asset_keys_for_node(result, "create_thirteen_and_six") == {
        dg.AssetKey("thirteen"),
        dg.AssetKey("six"),
    }
    assert _asset_keys_for_node(result, "create_twenty") == {dg.AssetKey("twenty")}


def test_internal_asset_deps():
    @dg.op
    def my_op(x, y):
        return x

    with pytest.raises(Exception, match="output_name non_exist_output_name"):

        @dg.graph(ins={"x": dg.GraphIn()})
        def my_graph(x, y):
            my_op(x, y)

        AssetsDefinition.from_graph(
            graph_def=my_graph, internal_asset_deps={"non_exist_output_name": {dg.AssetKey("b")}}
        )

    with pytest.raises(Exception, match="output_name non_exist_output_name"):
        AssetsDefinition.from_op(
            op_def=my_op, internal_asset_deps={"non_exist_output_name": {dg.AssetKey("b")}}
        )


def test_asset_def_from_op_inputs():
    @dg.op(
        ins={"my_input": dg.In(), "other_input": dg.In()}, out={"out1": dg.Out(), "out2": dg.Out()}
    )
    def my_op(my_input, other_input):
        pass

    assets_def = AssetsDefinition.from_op(
        op_def=my_op,
        keys_by_input_name={
            "my_input": dg.AssetKey("x_asset"),
            "other_input": dg.AssetKey("y_asset"),
        },
    )

    assert assets_def.keys_by_input_name["my_input"] == dg.AssetKey("x_asset")
    assert assets_def.keys_by_input_name["other_input"] == dg.AssetKey("y_asset")
    assert assets_def.keys_by_output_name["out1"] == dg.AssetKey("out1")
    assert assets_def.keys_by_output_name["out2"] == dg.AssetKey("out2")


def test_asset_def_from_op_outputs():
    @dg.op(
        ins={"my_input": dg.In(), "other_input": dg.In()}, out={"out1": dg.Out(), "out2": dg.Out()}
    )
    def x_op(my_input, other_input):
        pass

    assets_def = AssetsDefinition.from_op(
        op_def=x_op,
        keys_by_output_name={"out2": dg.AssetKey("y_asset"), "out1": dg.AssetKey("x_asset")},
    )

    assert assets_def.keys_by_output_name["out2"] == dg.AssetKey("y_asset")
    assert assets_def.keys_by_output_name["out1"] == dg.AssetKey("x_asset")
    assert assets_def.keys_by_input_name["my_input"] == dg.AssetKey("my_input")
    assert assets_def.keys_by_input_name["other_input"] == dg.AssetKey("other_input")


def test_asset_from_op_no_args():
    @dg.op
    def my_op(x, y):
        return x

    assets_def = AssetsDefinition.from_op(
        op_def=my_op,
    )

    assert assets_def.keys_by_input_name["x"] == dg.AssetKey("x")
    assert assets_def.keys_by_input_name["y"] == dg.AssetKey("y")
    assert assets_def.keys_by_output_name["result"] == dg.AssetKey("my_op")


def test_asset_def_from_graph_inputs():
    @dg.op
    def my_op(x, y):
        return x

    @dg.graph(ins={"x": dg.GraphIn(), "y": dg.GraphIn()})
    def my_graph(x, y):
        return my_op(x, y)

    assets_def = AssetsDefinition.from_graph(
        graph_def=my_graph,
        keys_by_input_name={"x": dg.AssetKey("x_asset"), "y": dg.AssetKey("y_asset")},
    )

    assert assets_def.keys_by_input_name["x"] == dg.AssetKey("x_asset")
    assert assets_def.keys_by_input_name["y"] == dg.AssetKey("y_asset")


def test_asset_def_from_graph_outputs():
    @dg.op
    def x_op(x):
        return x

    @dg.op
    def y_op(y):
        return y

    @dg.graph(out={"x": dg.GraphOut(), "y": dg.GraphOut()})
    def my_graph(x, y):
        return {"x": x_op(x), "y": y_op(y)}

    assets_def = AssetsDefinition.from_graph(
        graph_def=my_graph,
        keys_by_output_name={"y": dg.AssetKey("y_asset"), "x": dg.AssetKey("x_asset")},
    )

    assert assets_def.keys_by_output_name["y"] == dg.AssetKey("y_asset")
    assert assets_def.keys_by_output_name["x"] == dg.AssetKey("x_asset")


def test_graph_asset_decorator_no_args():
    @dg.op
    def my_op(x, y):
        return x

    @dg.graph
    def my_graph(x, y):
        return my_op(x, y)

    assets_def = AssetsDefinition.from_graph(
        graph_def=my_graph,
    )

    assert assets_def.keys_by_input_name["x"] == dg.AssetKey("x")
    assert assets_def.keys_by_input_name["y"] == dg.AssetKey("y")
    assert assets_def.keys_by_output_name["result"] == dg.AssetKey("my_graph")


def test_graph_asset_group_name():
    @dg.op
    def my_op1(x):
        return x

    @dg.op
    def my_op2(y):
        return y

    @dg.graph
    def my_graph(x):
        return my_op2(my_op1(x))

    assets_def = AssetsDefinition.from_graph(
        graph_def=my_graph,
        group_name="group1",
    )

    # The asset key is the function name when there is only one output
    assert assets_def.group_names_by_key[dg.AssetKey("my_graph")] == "group1"


def test_graph_asset_group_name_for_multiple_assets():
    @dg.op(out={"first_output": dg.Out(), "second_output": dg.Out()})
    def two_outputs():
        return 1, 2

    @dg.graph(out={"first_asset": dg.GraphOut(), "second_asset": dg.GraphOut()})
    def two_assets_graph():
        one, two = two_outputs()
        return {"first_asset": one, "second_asset": two}

    two_assets = AssetsDefinition.from_graph(two_assets_graph, group_name="group2")
    # same as above but using keys_by_output_name to assign AssetKey to each output
    two_assets_with_keys = AssetsDefinition.from_graph(
        two_assets_graph,
        keys_by_output_name={
            "first_asset": dg.AssetKey("first_asset_key"),
            "second_asset": dg.AssetKey("second_asset_key"),
        },
        group_name="group3",
    )

    assert two_assets.group_names_by_key[dg.AssetKey("first_asset")] == "group2"
    assert two_assets.group_names_by_key[dg.AssetKey("second_asset")] == "group2"

    assert two_assets_with_keys.group_names_by_key[dg.AssetKey("first_asset_key")] == "group3"
    assert two_assets_with_keys.group_names_by_key[dg.AssetKey("second_asset_key")] == "group3"


def test_execute_graph_asset():
    @dg.op(out={"x": dg.Out(), "y": dg.Out()})
    def x_op(context):
        assert context.asset_key_for_output("x") == dg.AssetKey("x_asset")
        return 1, 2

    @dg.graph(out={"x": dg.GraphOut(), "y": dg.GraphOut()})
    def my_graph():
        x, y = x_op()
        return {"x": x, "y": y}

    assets_def = AssetsDefinition.from_graph(
        graph_def=my_graph,
        keys_by_output_name={"y": dg.AssetKey("y_asset"), "x": dg.AssetKey("x_asset")},
    )

    assert dg.materialize_to_memory([assets_def]).success


def test_graph_asset_partitioned():
    @dg.op
    def my_op(context):
        assert context.partition_key == "a"

    @dg.graph
    def my_graph():
        return my_op()

    assets_def = AssetsDefinition.from_graph(
        graph_def=my_graph, partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c"])
    )

    assert dg.materialize_to_memory([assets_def], partition_key="a").success


def test_multi_asset_with_different_partitions_defs():
    unpartitioned_asset_spec = dg.AssetSpec("asset1")
    specs = [
        dg.AssetSpec("asset2", partitions_def=dg.StaticPartitionsDefinition(["a", "b"])),
        dg.AssetSpec("asset3", partitions_def=dg.StaticPartitionsDefinition(["x", "y"])),
        unpartitioned_asset_spec,
    ]

    @dg.multi_asset(specs=specs, can_subset=True)
    def my_multi_asset(context: dg.AssetExecutionContext):
        for asset_key in context.selected_asset_keys:
            yield dg.MaterializeResult(asset_key)

    assert dg.materialize_to_memory(
        [my_multi_asset], selection=[unpartitioned_asset_spec.key]
    ).success


def test_all_assets_job():
    @dg.asset
    def a1():
        return 1

    @dg.asset
    def a2(a1):
        return 2

    job = create_test_asset_job([a1, a2])

    assert job.asset_layer.upstream_dep_op_handles(dg.AssetKey("a1")) == {
        NodeHandle("a1", parent=None),
    }
    assert job.asset_layer.upstream_dep_op_handles(dg.AssetKey("a2")) == {
        NodeHandle("a2", parent=None)
    }


def test_basic_graph():
    @dg.op
    def get_string():
        return "foo"

    @dg.op(out={"ns1": dg.Out(), "ns2": dg.Out()})
    def combine_strings_and_split(s1, s2):
        return (s1 + s2, s2 + s1)

    @dg.graph(out={"o1": dg.GraphOut()})
    def thing():
        da = get_string()
        db = get_string()
        o1, o2 = combine_strings_and_split(da, db)
        return o1

    @dg.asset
    def out_asset1_plus_one(out_asset1):
        return out_asset1 + "one"

    @dg.asset
    def out_asset2_plus_one(out_asset2):
        return out_asset2 + "one"

    complex_asset = dg.AssetsDefinition(
        keys_by_input_name={},
        keys_by_output_name={"o1": dg.AssetKey("out_asset1")},
        node_def=thing,
    )

    job = create_test_asset_job([complex_asset])

    thing_handle = NodeHandle(name="thing", parent=None)
    assert job.asset_layer.upstream_dep_op_handles(dg.AssetKey("out_asset1")) == {
        NodeHandle("get_string", parent=thing_handle),
        NodeHandle("get_string_2", parent=thing_handle),
        NodeHandle("combine_strings_and_split", parent=thing_handle),
    }


def test_hanging_op_graph():
    @dg.op
    def get_string():
        return "foo"

    @dg.op
    def combine_strings(s1, s2):
        return s1 + s2

    @dg.op
    def hanging_op():
        return "bar"

    @dg.graph(out={"o1": dg.GraphOut(), "o2": dg.GraphOut()})
    def thing():
        da = get_string()
        db = get_string()
        o1 = combine_strings(da, db)
        o2 = hanging_op()
        return {"o1": o1, "o2": o2}

    complex_asset = dg.AssetsDefinition(
        keys_by_input_name={},
        keys_by_output_name={"o1": dg.AssetKey("out_asset1"), "o2": dg.AssetKey("out_asset2")},
        node_def=thing,
    )
    job = create_test_asset_job([complex_asset])
    thing_handle = NodeHandle(name="thing", parent=None)

    assert job.asset_layer.upstream_dep_op_handles(dg.AssetKey("out_asset1")) == {
        NodeHandle("get_string", parent=thing_handle),
        NodeHandle("get_string_2", parent=thing_handle),
        NodeHandle("combine_strings", parent=thing_handle),
    }
    assert job.asset_layer.upstream_dep_op_handles(dg.AssetKey("out_asset2")) == {
        NodeHandle("hanging_op", parent=thing_handle),
    }


def test_nested_graph():
    @dg.op
    def get_inside_string():
        return "bar"

    @dg.graph(out={"o2": dg.GraphOut()})
    def inside_thing():
        return get_inside_string()

    @dg.op
    def get_string():
        return "foo"

    @dg.op(out={"ns1": dg.Out(), "ns2": dg.Out()})
    def combine_strings_and_split(s1, s2):
        return (s1 + s2, s2 + s1)

    @dg.graph(out={"o1": dg.GraphOut()})
    def thing():
        da = inside_thing()
        db = get_string()
        o1, o2 = combine_strings_and_split(da, db)
        return o1

    thing_asset = dg.AssetsDefinition(
        keys_by_input_name={},
        keys_by_output_name={"o1": dg.AssetKey("thing")},
        node_def=thing,
    )

    job = create_test_asset_job([thing_asset])
    thing_handle = NodeHandle(name="thing", parent=None)
    assert job.asset_layer.upstream_dep_op_handles(dg.AssetKey("thing")) == {
        NodeHandle("get_inside_string", parent=NodeHandle("inside_thing", parent=thing_handle)),
        NodeHandle("get_string", parent=thing_handle),
        NodeHandle("combine_strings_and_split", parent=thing_handle),
    }


def test_asset_in_nested_graph():
    @dg.op
    def get_inside_string():
        return "bar"

    @dg.op
    def get_string():
        return "foo"

    @dg.graph(out={"n1": dg.GraphOut(), "n2": dg.GraphOut()})
    def inside_thing():
        n1 = get_inside_string()
        n2 = get_string()
        return n1, n2

    @dg.op
    def get_transformed_string(string):
        return string + "qux"

    @dg.graph(out={"o1": dg.GraphOut(), "o3": dg.GraphOut()})
    def thing():
        o1, o2 = inside_thing()  # pyright: ignore[reportGeneralTypeIssues]
        o3 = get_transformed_string(o2)
        return (o1, o3)

    thing_asset = dg.AssetsDefinition(
        keys_by_input_name={},
        keys_by_output_name={"o1": dg.AssetKey("thing"), "o3": dg.AssetKey("thing_2")},
        node_def=thing,
    )

    job = create_test_asset_job([thing_asset])

    thing_handle = NodeHandle(name="thing", parent=None)
    assert job.asset_layer.upstream_dep_op_handles(dg.AssetKey("thing")) == {
        NodeHandle("get_inside_string", parent=NodeHandle("inside_thing", parent=thing_handle)),
    }
    assert job.asset_layer.upstream_dep_op_handles(dg.AssetKey("thing_2")) == {
        NodeHandle("get_string", parent=NodeHandle("inside_thing", parent=thing_handle)),
        NodeHandle("get_transformed_string", parent=thing_handle),
    }


def test_twice_nested_graph():
    @dg.op
    def get_inside_string():
        return "bar"

    @dg.op
    def get_string():
        return "foo"

    @dg.graph(out={"n1": dg.GraphOut(), "n2": dg.GraphOut()})
    def innermost_thing():
        n1 = get_inside_string()
        n2 = get_string()
        return {"n1": n1, "n2": n2}

    @dg.op
    def transformer(string):
        return string + "qux"

    @dg.op
    def combiner(s1, s2):
        return s1 + s2

    @dg.graph(out={"n1": dg.GraphOut(), "n2": dg.GraphOut(), "unused": dg.GraphOut()})
    def middle_thing():
        n1, unused_output = innermost_thing()  # pyright: ignore[reportGeneralTypeIssues]
        n2 = get_string()
        return {"n1": n1, "n2": n2, "unused": unused_output}

    @dg.graph(out={"n1": dg.GraphOut(), "n2": dg.GraphOut(), "unused": dg.GraphOut()})
    def outer_thing(foo_asset):
        n1, output, unused_output = middle_thing()  # pyright: ignore[reportGeneralTypeIssues]
        n2 = transformer(output)
        unused_output = combiner(unused_output, transformer(foo_asset))
        return {"n1": n1, "n2": n2, "unused": unused_output}

    @dg.asset
    def foo_asset():
        return "foo"

    thing_asset = AssetsDefinition.from_graph(
        graph_def=outer_thing,
        keys_by_input_name={},
        keys_by_output_name={
            "n1": dg.AssetKey("thing"),
            "n2": dg.AssetKey("thing_2"),
            "unused": dg.AssetKey("asjdlaksjhbdluuawubn"),
        },
    )

    job = create_test_asset_job([foo_asset, thing_asset])

    outer_thing_handle = NodeHandle("outer_thing", parent=None)
    middle_thing_handle = NodeHandle("middle_thing", parent=outer_thing_handle)
    assert job.asset_layer.upstream_dep_op_handles(dg.AssetKey("thing")) == {
        NodeHandle(
            "get_inside_string",
            parent=NodeHandle(
                "innermost_thing",
                parent=middle_thing_handle,
            ),
        )
    }
    assert job.asset_layer.upstream_dep_op_handles(dg.AssetKey("thing_2")) == {
        NodeHandle("get_string", parent=middle_thing_handle),
        NodeHandle("transformer", parent=outer_thing_handle),
    }
    assert job.asset_layer.upstream_dep_op_handles(dg.AssetKey("foo_asset")) == {
        NodeHandle("foo_asset", parent=None)
    }


def test_internal_asset_deps_assets():
    @dg.op
    def upstream_op():
        return "foo"

    @dg.op(out={"o1": dg.Out(), "o2": dg.Out()})
    def two_outputs(upstream_op):
        o1 = upstream_op
        o2 = o1 + "bar"
        return o1, o2

    @dg.graph(out={"o1": dg.GraphOut(), "o2": dg.GraphOut()})
    def thing():
        o1, o2 = two_outputs(upstream_op())
        return (o1, o2)

    thing_asset = dg.AssetsDefinition(
        keys_by_input_name={},
        keys_by_output_name={"o1": dg.AssetKey("thing"), "o2": dg.AssetKey("thing_2")},
        node_def=thing,
        asset_deps={dg.AssetKey("thing"): set(), dg.AssetKey("thing_2"): {dg.AssetKey("thing")}},
    )

    @dg.multi_asset(
        outs={
            "my_out_name": dg.AssetOut(metadata={"foo": "bar"}),
            "my_other_out_name": dg.AssetOut(metadata={"bar": "foo"}),
        },
        internal_asset_deps={
            "my_out_name": {dg.AssetKey("my_other_out_name")},
            "my_other_out_name": {dg.AssetKey("thing")},
        },
    )
    def multi_asset_with_internal_deps(thing):
        yield dg.Output(1, "my_out_name")
        yield dg.Output(2, "my_other_out_name")

    job = create_test_asset_job([thing_asset, multi_asset_with_internal_deps])
    assert job.asset_layer.upstream_dep_op_handles(dg.AssetKey("thing")) == {
        NodeHandle("two_outputs", parent=NodeHandle("thing", parent=None)),
        NodeHandle(name="upstream_op", parent=NodeHandle(name="thing", parent=None)),
    }
    assert job.asset_layer.upstream_dep_op_handles(dg.AssetKey("thing_2")) == {
        NodeHandle("two_outputs", parent=NodeHandle("thing", parent=None)),
        NodeHandle(name="upstream_op", parent=NodeHandle(name="thing", parent=None)),
    }

    assert job.asset_layer.upstream_dep_op_handles(dg.AssetKey("my_out_name")) == {
        NodeHandle(name="multi_asset_with_internal_deps", parent=None)
    }
    assert job.asset_layer.upstream_dep_op_handles(dg.AssetKey("my_other_out_name")) == {
        NodeHandle(name="multi_asset_with_internal_deps", parent=None)
    }


@dg.multi_asset(
    outs={"a": dg.AssetOut(is_required=False), "b": dg.AssetOut(is_required=False)}, can_subset=True
)
def ab(context, foo):
    assert (context.op_execution_context.selected_output_names != {"a", "b"}) == context.is_subset

    if "a" in context.op_execution_context.selected_output_names:
        yield dg.Output(foo + 1, "a")
    if "b" in context.op_execution_context.selected_output_names:
        yield dg.Output(foo + 2, "b")


@dg.asset
def foo():
    return 5


@dg.asset
def bar():
    return 10


@dg.asset
def foo_bar(foo, bar):
    return foo + bar


@dg.asset
def baz(foo_bar):
    return foo_bar


@dg.asset
def unconnected():
    pass


asset_defs = [foo, ab, bar, foo_bar, baz, unconnected]


def test_disconnected_subset():
    with dg.instance_for_test() as instance:
        defs = dg.Definitions(assets=asset_defs, jobs=[dg.define_asset_job("foo")])
        foo_job = defs.resolve_job_def("foo")
        result = foo_job.execute_in_process(
            instance=instance, asset_selection=[dg.AssetKey("unconnected"), dg.AssetKey("bar")]
        )
        materialization_events = [
            event for event in result.all_events if event.is_step_materialization
        ]

        assert len(materialization_events) == 2
        assert materialization_events[0].asset_key == dg.AssetKey("bar")
        assert materialization_events[1].asset_key == dg.AssetKey("unconnected")


def test_connected_subset():
    with dg.instance_for_test() as instance:
        defs = dg.Definitions(assets=asset_defs, jobs=[dg.define_asset_job("foo")])
        foo_job = defs.resolve_job_def("foo")
        result = foo_job.execute_in_process(
            instance=instance,
            asset_selection=[dg.AssetKey("foo"), dg.AssetKey("bar"), dg.AssetKey("foo_bar")],
        )
        materialization_events = sorted(
            [event for event in result.all_events if event.is_step_materialization],
            key=lambda event: event.asset_key,  # type: ignore
        )

        assert len(materialization_events) == 3
        assert materialization_events[0].asset_key == dg.AssetKey("bar")
        assert materialization_events[1].asset_key == dg.AssetKey("foo")
        assert materialization_events[2].asset_key == dg.AssetKey("foo_bar")


def test_subset_of_asset_job():
    with dg.instance_for_test() as instance:
        defs = dg.Definitions(assets=asset_defs, jobs=[dg.define_asset_job("foo", "*baz")])
        foo_job = defs.resolve_job_def("foo")
        result = foo_job.execute_in_process(
            instance=instance,
            asset_selection=[dg.AssetKey("foo"), dg.AssetKey("bar"), dg.AssetKey("foo_bar")],
        )
        materialization_events = sorted(
            [event for event in result.all_events if event.is_step_materialization],
            key=lambda event: event.asset_key,  # type: ignore
        )
        assert len(materialization_events) == 3
        assert materialization_events[0].asset_key == dg.AssetKey("bar")
        assert materialization_events[1].asset_key == dg.AssetKey("foo")
        assert materialization_events[2].asset_key == dg.AssetKey("foo_bar")

        # with pytest.raises(DagsterInvalidSubsetError):
        #     result = foo_job.execute_in_process(
        #         instance=instance,
        #         asset_selection=[AssetKey("unconnected")],
        #     )


def test_subset_of_assets_job():
    foo_job = create_test_asset_job(assets=[foo, bar, foo_bar, baz])
    with dg.instance_for_test() as instance:
        result = foo_job.execute_in_process(
            instance=instance,
            asset_selection=[dg.AssetKey("foo"), dg.AssetKey("bar"), dg.AssetKey("foo_bar")],
        )
        materialization_events = sorted(
            [event for event in result.all_events if event.is_step_materialization],
            key=lambda event: event.asset_key,  # type: ignore
        )
        assert len(materialization_events) == 3
        assert materialization_events[0].asset_key == dg.AssetKey("bar")
        assert materialization_events[1].asset_key == dg.AssetKey("foo")
        assert materialization_events[2].asset_key == dg.AssetKey("foo_bar")

        with pytest.raises(dg.DagsterInvalidSubsetError):
            result = foo_job.execute_in_process(
                instance=instance,
                asset_selection=[dg.AssetKey("unconnected")],
            )


@dg.resource
def my_resource():
    return 1


@dg.resource
def my_resource_2():
    return 1


@dg.multi_asset(
    name="fivetran_sync",
    outs={key: dg.AssetOut(key=dg.AssetKey(key)) for key in ["a", "b", "c"]},
)
def fivetran_asset():
    return 1, 2, 3


@dg.op(
    name="dbt",
    ins={
        "a": dg.In(dg.Nothing),
        "b": dg.In(dg.Nothing),
        "c": dg.In(dg.Nothing),
    },
    out={
        "d": dg.Out(is_required=False),
        "e": dg.Out(is_required=False),
        "f": dg.Out(is_required=False),
    },
    required_resource_keys={"my_resource_2"},
)
def dbt_op():
    yield dg.Output(4, "f")


dbt_asset_def = dg.AssetsDefinition(
    keys_by_output_name={k: dg.AssetKey(k) for k in ["d", "e", "f"]},
    keys_by_input_name={k: dg.AssetKey(k) for k in ["a", "b", "c"]},
    node_def=dbt_op,
    can_subset=True,
    asset_deps={
        dg.AssetKey("d"): {dg.AssetKey("a")},
        dg.AssetKey("e"): {dg.AssetKey("d"), dg.AssetKey("b")},
        dg.AssetKey("f"): {dg.AssetKey("d"), dg.AssetKey("e")},
    },
)

my_job = dg.define_asset_job("foo", selection=["a", "b", "c", "d", "e", "f"]).resolve(
    asset_graph=AssetGraph.from_assets(
        dg.with_resources(
            [dbt_asset_def, fivetran_asset],
            resource_defs={"my_resource": my_resource, "my_resource_2": my_resource_2},
        ),
    )
)


def reconstruct_asset_job():
    return my_job


def test_asset_selection_reconstructable():
    with disable_dagster_warnings():
        with dg.instance_for_test() as instance:
            run = instance.create_run_for_job(
                job_def=my_job, asset_selection=frozenset([dg.AssetKey("f")])
            )
            reconstructable_foo_job = dg.build_reconstructable_job(
                "dagster_tests.asset_defs_tests.test_asset_job",
                "reconstruct_asset_job",
                reconstructable_args=tuple(),
                reconstructable_kwargs={},
            ).get_subset(asset_selection=frozenset([dg.AssetKey("f")]))

            events = list(execute_run_iterator(reconstructable_foo_job, run, instance=instance))
            assert len([event for event in events if event.is_job_success]) == 1

            materialization_planned = list(
                instance.get_records_for_run(
                    run_id=run.run_id,
                    of_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                ).records
            )
            assert len(materialization_planned) == 1


def test_job_preserved_with_asset_subset():
    # Assert that default config is used for asset subset

    @dg.op(config_schema={"foo": int})
    def one(context):
        assert context.op_execution_context.op_config["foo"] == 1

    asset_one = AssetsDefinition.from_op(one)

    @dg.asset(config_schema={"bar": int})
    def two(context, one):
        assert context.op_execution_context.op_config["bar"] == 2

    @dg.asset(config_schema={"baz": int})
    def three(context, two):
        assert context.op_execution_context.op_config["baz"] == 3

    foo_job = dg.define_asset_job(
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
    ).resolve(asset_graph=AssetGraph.from_assets([asset_one, two, three]))

    result = foo_job.execute_in_process(asset_selection=[dg.AssetKey("one")])
    assert result.success
    assert result.dagster_run.tags == {"yay": "1"}


def test_job_default_config_preserved_with_asset_subset():
    # Assert that default config is used for asset subset

    @dg.op(config_schema={"foo": dg.Field(int, default_value=1)})
    def one(context):
        assert context.op_execution_context.op_config["foo"] == 1

    asset_one = AssetsDefinition.from_op(one)

    @dg.asset(config_schema={"bar": dg.Field(int, default_value=2)})
    def two(context, one):
        assert context.op_execution_context.op_config["bar"] == 2

    @dg.asset(config_schema={"baz": dg.Field(int, default_value=3)})
    def three(context, two):
        assert context.op_execution_context.op_config["baz"] == 3

    foo_job = dg.define_asset_job("foo_job").resolve(
        asset_graph=AssetGraph.from_assets([asset_one, two, three])
    )

    result = foo_job.execute_in_process(asset_selection=[dg.AssetKey("one")])
    assert result.success


def test_empty_asset_job():
    @dg.asset
    def a():
        pass

    @dg.asset
    def b(a):
        pass

    empty_selection = AssetSelection.assets("a", "b") - AssetSelection.assets("a", "b")
    assert empty_selection.resolve([a, b]) == set()

    empty_job = dg.define_asset_job("empty_job", selection=empty_selection).resolve(
        asset_graph=AssetGraph.from_assets([a, b])
    )
    assert empty_job.all_node_defs == []

    result = empty_job.execute_in_process()
    assert result.success


def test_raise_error_on_incomplete_graph_asset_subset():
    @dg.op
    def do_something(x):
        return x * 2

    @dg.op
    def foo():
        return 1, 2

    @dg.graph(
        out={
            "comments_table": dg.GraphOut(),
            "stories_table": dg.GraphOut(),
        },
    )
    def complicated_graph():
        result = foo()
        return do_something(result), do_something(result)

    defs = dg.Definitions(
        assets=[
            AssetsDefinition.from_graph(complicated_graph),
        ],
        jobs=[dg.define_asset_job("foo_job")],
    )
    foo_job = defs.resolve_job_def("foo_job")

    with dg.instance_for_test() as instance:
        with pytest.raises(dg.DagsterInvalidSubsetError, match="complicated_graph"):
            foo_job.execute_in_process(
                instance=instance, asset_selection=[dg.AssetKey("comments_table")]
            )


def test_multi_subset():
    with dg.instance_for_test() as instance:
        defs = dg.Definitions(assets=asset_defs, jobs=[dg.define_asset_job("foo")])
        foo_job = defs.resolve_job_def("foo")
        result = foo_job.execute_in_process(
            instance=instance,
            asset_selection=[dg.AssetKey("foo"), dg.AssetKey("a")],
        )
        materialization_events = sorted(
            [event for event in result.all_events if event.is_step_materialization],
            key=lambda event: event.asset_key,  # type: ignore
        )

        assert len(materialization_events) == 2
        assert materialization_events[0].asset_key == dg.AssetKey("a")
        assert materialization_events[1].asset_key == dg.AssetKey("foo")


def test_multi_all():
    with dg.instance_for_test() as instance:
        defs = dg.Definitions(assets=asset_defs, jobs=[dg.define_asset_job("foo")])
        foo_job = defs.resolve_job_def("foo")
        result = foo_job.execute_in_process(
            instance=instance,
            asset_selection=[dg.AssetKey("foo"), dg.AssetKey("a"), dg.AssetKey("b")],
        )
        materialization_events = sorted(
            [event for event in result.all_events if event.is_step_materialization],
            key=lambda event: event.asset_key,  # type: ignore
        )

        assert len(materialization_events) == 3
        assert materialization_events[0].asset_key == dg.AssetKey("a")
        assert materialization_events[1].asset_key == dg.AssetKey("b")
        assert materialization_events[2].asset_key == dg.AssetKey("foo")


@ignore_warning("Class `SourceAsset` is deprecated and will be removed in 2.0.0.")
def test_subset_with_source_asset():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @dg.io_manager
    def the_manager():
        return MyIOManager()

    my_source_asset = dg.SourceAsset(
        key=dg.AssetKey("my_source_asset"), io_manager_key="the_manager"
    )

    @dg.asset
    def my_derived_asset(my_source_asset):
        return my_source_asset + 4

    source_asset_job = dg.Definitions(
        assets=[my_derived_asset, my_source_asset],
        resources={"the_manager": the_manager},
        jobs=[dg.define_asset_job("source_asset_job", [my_derived_asset])],
    ).resolve_job_def("source_asset_job")

    result = source_asset_job.execute_in_process(asset_selection=[dg.AssetKey("my_derived_asset")])
    assert result.success


def test_op_outputs_with_default_asset_io_mgr():
    @dg.op
    def return_stuff():
        return 12

    @dg.op
    def transform(data):
        assert data == 12
        return data * 2

    @dg.op
    def one_more_transformation(transformed_data):
        assert transformed_data == 24
        return transformed_data + 1

    @dg.graph(
        out={
            "asset_1": dg.GraphOut(),
            "asset_2": dg.GraphOut(),
        },
    )
    def complicated_graph():
        result = return_stuff()
        return one_more_transformation(transform(result)), transform(result)

    @dg.asset
    def my_asset(asset_1):
        assert asset_1 == 25
        return asset_1

    defs = dg.Definitions(
        assets=[
            AssetsDefinition.from_graph(complicated_graph),
            my_asset,
        ],
        jobs=[dg.define_asset_job("foo_job", executor_def=in_process_executor)],
    )
    foo_job = defs.resolve_job_def("foo_job")

    result = foo_job.execute_in_process()
    assert result.success


def test_graph_output_is_input_within_graph():
    @dg.op
    def return_stuff():
        return 1

    @dg.op
    def transform(data):
        return data * 2

    @dg.op
    def one_more_transformation(transformed_data):
        return transformed_data + 1

    @dg.graph(
        out={
            "one": dg.GraphOut(),
            "two": dg.GraphOut(),
        },
    )
    def nested():
        result = transform(return_stuff())
        return one_more_transformation(result), result

    @dg.graph(
        out={
            "asset_1": dg.GraphOut(),
            "asset_2": dg.GraphOut(),
            "asset_3": dg.GraphOut(),
        },
    )
    def complicated_graph():
        one, two = nested()  # pyright: ignore[reportGeneralTypeIssues]
        return one, two, transform(two)

    defs = dg.Definitions(
        assets=[
            AssetsDefinition.from_graph(complicated_graph),
        ],
        jobs=[dg.define_asset_job("foo_job")],
    )
    foo_job = defs.resolve_job_def("foo_job")

    result = foo_job.execute_in_process()
    assert result.success

    assert result.output_for_node("complicated_graph.nested", "one") == 3
    assert result.output_for_node("complicated_graph.nested", "two") == 2

    assert result.output_for_node("complicated_graph", "asset_1") == 3
    assert result.output_for_node("complicated_graph", "asset_2") == 2
    assert result.output_for_node("complicated_graph", "asset_3") == 4


@ignore_warning("Class `SourceAsset` is deprecated and will be removed in 2.0.0.")
@ignore_warning("Parameter `io_manager_def` .* is currently in beta")
def test_source_asset_io_manager_def():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @dg.io_manager
    def the_manager():
        return MyIOManager()

    my_source_asset = dg.SourceAsset(key=dg.AssetKey("my_source_asset"), io_manager_def=the_manager)

    @dg.asset
    def my_derived_asset(my_source_asset):
        return my_source_asset + 4

    source_asset_job = create_test_asset_job(assets=[my_derived_asset, my_source_asset])

    result = source_asset_job.execute_in_process(asset_selection=[dg.AssetKey("my_derived_asset")])
    assert result.success
    assert result.output_for_node("my_derived_asset") == 9


@ignore_warning("Class `SourceAsset` is deprecated and will be removed in 2.0.0.")
def test_source_asset_io_manager_not_provided():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @dg.io_manager
    def the_manager():
        return MyIOManager()

    my_source_asset = dg.SourceAsset(key=dg.AssetKey("my_source_asset"))

    @dg.asset
    def my_derived_asset(my_source_asset):
        return my_source_asset + 4

    source_asset_job = create_test_asset_job(
        assets=[my_derived_asset, my_source_asset],
        resources={"io_manager": the_manager},
    )

    result = source_asset_job.execute_in_process(asset_selection=[dg.AssetKey("my_derived_asset")])
    assert result.success
    assert result.output_for_node("my_derived_asset") == 9


@ignore_warning("Class `SourceAsset` is deprecated and will be removed in 2.0.0.")
def test_source_asset_io_manager_key_provided():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @dg.io_manager
    def the_manager():
        return MyIOManager()

    my_source_asset = dg.SourceAsset(key=dg.AssetKey("my_source_asset"), io_manager_key="some_key")

    @dg.asset
    def my_derived_asset(my_source_asset):
        return my_source_asset + 4

    source_asset_job = create_test_asset_job(
        assets=[my_derived_asset, my_source_asset],
        resources={"some_key": the_manager},
    )

    result = source_asset_job.execute_in_process(asset_selection=[dg.AssetKey("my_derived_asset")])
    assert result.success
    assert result.output_for_node("my_derived_asset") == 9


@ignore_warning("Class `SourceAsset` is deprecated and will be removed in 2.0.0.")
@ignore_warning("Parameter `resource_defs` .* is currently in beta")
@ignore_warning("Parameter `io_manager_def` .* is currently in beta")
def test_source_asset_requires_resource_defs():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @dg.resource(required_resource_keys={"bar"})
    def foo_resource(context):
        assert context.resources.bar == "blah"

    @dg.io_manager(required_resource_keys={"foo"})
    def the_manager():
        return MyIOManager()

    my_source_asset = dg.SourceAsset(
        key=dg.AssetKey("my_source_asset"),
        io_manager_def=the_manager,
        resource_defs={"foo": foo_resource, "bar": ResourceDefinition.hardcoded_resource("blah")},
    )

    @dg.asset
    def my_derived_asset(my_source_asset):
        return my_source_asset + 4

    source_asset_job = create_test_asset_job(
        assets=[my_derived_asset, my_source_asset],
    )

    result = source_asset_job.execute_in_process(asset_selection=[dg.AssetKey("my_derived_asset")])
    assert result.success
    assert result.output_for_node("my_derived_asset") == 9


@ignore_warning("Parameter `resource_defs` .* is currently in beta")
def test_other_asset_provides_req():
    # Demonstrate that assets cannot resolve each other's dependencies with
    # resources on each definition.
    @dg.asset(required_resource_keys={"foo"})
    def asset_reqs_foo():
        pass

    @dg.asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("blah")})
    def asset_provides_foo():
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="resource with key 'foo' required by op 'asset_reqs_foo' was not provided.",
    ):
        create_test_asset_job(assets=[asset_reqs_foo, asset_provides_foo])


@ignore_warning("Parameter `resource_defs` .* is currently in beta")
def test_transitive_deps_not_provided():
    @dg.resource(required_resource_keys={"foo"})
    def unused_resource():
        pass

    @dg.asset(resource_defs={"unused": unused_resource})
    def the_asset():
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="resource with key 'foo' required by resource with key 'unused' was not provided.",
    ):
        create_test_asset_job(assets=[the_asset])


@ignore_warning("Parameter `resource_defs` .* is currently in beta")
def test_transitive_resource_deps_provided():
    @dg.resource(required_resource_keys={"foo"})
    def used_resource(context):
        assert context.resources.foo == "blah"

    @dg.asset(
        resource_defs={"used": used_resource, "foo": ResourceDefinition.hardcoded_resource("blah")}
    )
    def the_asset():
        pass

    the_job = create_test_asset_job(assets=[the_asset])
    assert the_job.execute_in_process().success


@ignore_warning("Class `SourceAsset` is deprecated and will be removed in 2.0.0.")
@ignore_warning("Parameter `io_manager_def` .* is currently in beta")
def test_transitive_io_manager_dep_not_provided():
    @dg.io_manager(required_resource_keys={"foo"})  # pyright: ignore[reportArgumentType]
    def the_manager():
        pass

    my_source_asset = dg.SourceAsset(
        key=dg.AssetKey("my_source_asset"),
        io_manager_def=the_manager,
    )

    @dg.asset
    def my_derived_asset(my_source_asset):
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "resource with key 'foo' required by resource with key 'my_source_asset__io_manager'"
            " was not provided."
        ),
    ):
        create_test_asset_job(assets=[my_derived_asset, my_source_asset])


def test_resolve_dependency_in_group():
    @dg.asset(key_prefix="abc")
    def asset1(): ...

    @dg.asset
    def asset2(context, asset1):
        del asset1
        assert context.asset_key_for_input("asset1") == dg.AssetKey(["abc", "asset1"])

    with disable_dagster_warnings():
        assert dg.materialize_to_memory([asset1, asset2]).success


def test_resolve_dependency_fail_across_groups():
    @dg.asset(key_prefix="abc", group_name="other")
    def asset1(): ...

    @dg.asset
    def asset2(asset1):
        del asset1

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "is not produced by any of the provided asset ops and is not one of the provided"
            " sources"
        ),
    ):
        with disable_dagster_warnings():
            dg.materialize_to_memory([asset1, asset2])


def test_resolve_dependency_multi_asset_different_groups():
    @dg.asset(key_prefix="abc", group_name="a")
    def upstream(): ...

    @dg.op(out={"ns1": dg.Out(), "ns2": dg.Out()})
    def op1(upstream):
        del upstream

    assets = dg.AssetsDefinition(
        keys_by_input_name={"upstream": dg.AssetKey("upstream")},
        keys_by_output_name={"ns1": dg.AssetKey("ns1"), "ns2": dg.AssetKey("ns2")},
        node_def=op1,
        group_names_by_key={dg.AssetKey("ns1"): "a", dg.AssetKey("ns2"): "b"},
    )

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "is not produced by any of the provided asset ops and is not one of the provided"
            " sources"
        ),
    ):
        with disable_dagster_warnings():
            dg.materialize_to_memory([upstream, assets])


def test_coerce_resource_asset_job() -> None:
    executed = {}

    class BareResourceObject:
        pass

    @dg.asset(required_resource_keys={"bare_resource"})
    def an_asset(context) -> None:
        assert context.resources.bare_resource
        executed["yes"] = True

    a_job = create_test_asset_job(
        assets=[an_asset], resources={"bare_resource": BareResourceObject()}
    )

    assert a_job.execute_in_process().success


def test_assets_def_takes_bare_object():
    class BareResourceObject:
        pass

    executed = {}

    @dg.op(required_resource_keys={"bare_resource"})
    def an_op(context):
        assert context.resources.bare_resource
        executed["yes"] = True

    cool_thing_asset = dg.AssetsDefinition(
        keys_by_input_name={},
        keys_by_output_name={"result": dg.AssetKey("thing")},
        node_def=an_op,
        resource_defs={"bare_resource": BareResourceObject()},
    )
    job = create_test_asset_job([cool_thing_asset])
    result = job.execute_in_process()
    assert result.success
    assert executed["yes"]


def test_async_multi_asset():
    async def make_outputs():
        yield dg.Output(1, output_name="A")
        yield dg.Output(2, output_name="B")

    @dg.multi_asset(
        outs={"A": dg.AssetOut(), "B": dg.AssetOut()},
        can_subset=True,
    )
    async def aio_gen_asset(context):
        async for v in make_outputs():
            context.log.info(v.output_name)
            yield v

    aio_job = create_test_asset_job([aio_gen_asset])
    result = aio_job.execute_in_process()
    assert result.success


@ignore_warning("Class `SourceAsset` is deprecated and will be removed in 2.0.0.")
def test_selection_multi_component():
    source_asset = dg.SourceAsset(["apple", "banana"])

    @dg.asset(key_prefix="abc")
    def asset1(): ...

    assert dg.Definitions(
        assets=[source_asset, asset1],
        jobs=[dg.define_asset_job("something", selection="abc/asset1")],
    ).resolve_job_def("something").asset_layer.executable_asset_keys == {
        dg.AssetKey(["abc", "asset1"])
    }


@pytest.mark.parametrize(
    "job_selection,expected_nodes", [("*", "n1,n2,n3"), ("n2+", "n2,n3"), ("n1", "n1")]
)
def test_asset_subset_io_managers(job_selection, expected_nodes):
    # we're testing that when this job is subset, the correct io managers are used to load each
    # source asset
    @dg.io_manager(config_schema={"n": int})
    def return_n_io_manager(context):
        class ReturnNIOManager(dg.IOManager):
            def handle_output(self, _context, obj):  # pyright: ignore[reportIncompatibleMethodOverride]
                pass

            def load_input(self, _context):  # pyright: ignore[reportIncompatibleMethodOverride]
                return context.resource_config["n"]

        return ReturnNIOManager()

    _ACTUAL_OUTPUT_VAL = 99999

    @dg.asset(io_manager_key="n1_iom")
    def n1():
        return _ACTUAL_OUTPUT_VAL

    @dg.asset(io_manager_key="n2_iom")
    def n2(n1):
        assert n1 == 1
        return _ACTUAL_OUTPUT_VAL

    @dg.asset(io_manager_key="n3_iom")
    def n3(n1, n2):
        assert n1 == 1
        assert n2 == 2
        return _ACTUAL_OUTPUT_VAL

    asset_job = dg.define_asset_job("test", selection=job_selection)
    defs = dg.Definitions(
        assets=[n1, n2, n3],
        resources={
            "n1_iom": return_n_io_manager.configured({"n": 1}),
            "n2_iom": return_n_io_manager.configured({"n": 2}),
            "n3_iom": return_n_io_manager.configured({"n": 3}),
        },
        jobs=[asset_job],
    )

    result = defs.resolve_job_def("test").execute_in_process()

    for node in expected_nodes.split(","):
        assert result.output_for_node(node) == _ACTUAL_OUTPUT_VAL


def asset_aware_io_manager():
    class MyIOManager(dg.IOManager):
        def __init__(self):
            self.db = {}

        def handle_output(self, context, obj):
            self.db[context.asset_key] = obj

        def load_input(self, context):
            return self.db.get(context.asset_key)

    io_manager_obj = MyIOManager()

    @dg.io_manager
    def _asset_aware():
        return io_manager_obj

    return io_manager_obj, _asset_aware


def _get_assets_defs(use_multi: bool = False, allow_subset: bool = False):
    """Get a predefined set of assets definitions for testing.

    Dependencies:
        "upstream": {
            "start": set(),
            "a": {"start"},
            "b": set(),
            "c": {"b"},
            "d": {"a", "b"},
            "e": {"c"},
            "f": {"e", "d"},
            "final": {"a", "d"},
        },
        "downstream": {
            "start": {"a"},
            "b": {"c", "d"},
            "a": {"final", "d"},
            "c": {"e"},
            "d": {"final", "f"},
            "e": {"f"},
        }
    """

    @dg.asset
    def start():
        return 1

    @dg.asset
    def a(start):
        return start + 1

    @dg.asset
    def b():
        return 1

    @dg.asset
    def c(b):
        return b + 1

    @dg.multi_asset(
        outs={
            "a": dg.AssetOut(is_required=False),
            "b": dg.AssetOut(is_required=False),
            "c": dg.AssetOut(is_required=False),
        },
        internal_asset_deps={
            "a": {dg.AssetKey("start")},
            "b": set(),
            "c": {dg.AssetKey("b")},
        },
        can_subset=allow_subset,
    )
    def abc_(context, start):
        assert (
            context.op_execution_context.selected_output_names != {"a", "b", "c"}
        ) == context.is_subset

        a = (start + 1) if start else None
        b = 1
        c = b + 1
        out_values = {"a": a, "b": b, "c": c}
        # Alphabetical order matches topological order here
        outputs_to_return = (
            sorted(context.op_execution_context.selected_output_names) if allow_subset else "abc"
        )
        for output_name in outputs_to_return:
            yield dg.Output(out_values[output_name], output_name)

    @dg.asset
    def d(a, b):
        return a + b

    @dg.asset
    def e(c):
        return c + 1

    @dg.asset
    def f(d, e):
        return d + e

    @dg.multi_asset(
        outs={
            "d": dg.AssetOut(is_required=False),
            "e": dg.AssetOut(is_required=False),
            "f": dg.AssetOut(is_required=False),
        },
        internal_asset_deps={
            "d": {dg.AssetKey("a"), dg.AssetKey("b")},
            "e": {dg.AssetKey("c")},
            "f": {dg.AssetKey("d"), dg.AssetKey("e")},
        },
        can_subset=allow_subset,
    )
    def def_(context, a, b, c):
        assert (
            context.op_execution_context.selected_output_names != {"d", "e", "f"}
        ) == context.is_subset

        d = (a + b) if a and b else None
        e = (c + 1) if c else None
        f = (d + e) if d and e else None
        out_values = {"d": d, "e": e, "f": f}
        # Alphabetical order matches topological order here
        outputs_to_return = (
            sorted(context.op_execution_context.selected_output_names) if allow_subset else "def"
        )
        for output_name in outputs_to_return:
            yield dg.Output(out_values[output_name], output_name)

    @dg.asset
    def final(a, d):
        return a + d

    if use_multi:
        return [start, abc_, def_, final]
    return [start, a, b, c, d, e, f, final]


@pytest.mark.parametrize(
    "job_selection,use_multi,expected_error",
    [
        ("*", False, None),
        ("*", True, None),
        ("e", False, None),
        ("e", True, (dg.DagsterInvalidSubsetError, None)),
        (
            "x",
            False,
            (
                dg.DagsterInvalidSubsetError,
                r"no AssetsDefinition objects supply these keys",
            ),
        ),
        (
            "x",
            True,
            (
                dg.DagsterInvalidSubsetError,
                r"no AssetsDefinition objects supply these keys",
            ),
        ),
        (
            ["start", "x"],
            False,
            (
                dg.DagsterInvalidSubsetError,
                r"no AssetsDefinition objects supply these keys",
            ),
        ),
        (
            ["start", "x"],
            True,
            (
                dg.DagsterInvalidSubsetError,
                r"no AssetsDefinition objects supply these keys",
            ),
        ),
        (["d", "e", "f"], False, None),
        (["d", "e", "f"], True, None),
        (["start+"], False, None),
        (
            ["start+"],
            True,
            (
                dg.DagsterInvalidSubsetError,
                r"When building job, the AssetsDefinition 'abc_' contains asset keys "
                r"\[AssetKey\(\['a'\]\), AssetKey\(\['b'\]\), AssetKey\(\['c'\]\)\] and check keys \[\], but"
                r" attempted to "
                r"select only assets \[AssetKey\(\['a'\]\)\] and checks \[\]",
            ),
        ),
    ],
)
def test_build_subset_job_errors(job_selection, use_multi, expected_error):
    assets = _get_assets_defs(use_multi=use_multi)
    asset_job = dg.define_asset_job("some_name", selection=job_selection)

    if expected_error:
        expected_class, expected_message = expected_error
        with pytest.raises(dg.DagsterInvalidDefinitionError) as exc_info:
            dg.Definitions(assets=assets, jobs=[asset_job]).resolve_all_job_defs()

        tb_exc = traceback.TracebackException.from_exception(exc_info.value)
        error_info = SerializableErrorInfo.from_traceback(tb_exc)

        # assert exception context has the expected message and class
        assert check.not_none(error_info.cause).cls_name == expected_class.__name__
        if expected_message:
            assert (
                re.compile(expected_message).search(check.not_none(error_info.cause).message)
                is not None
            )

    else:
        dg.Definitions(assets=assets, jobs=[asset_job])


@pytest.mark.parametrize(
    "job_selection,expected_assets",
    [
        ("*", "a,b,c"),
        ("a+", "a,b"),
        ("+c", "b,c"),
        (["a", "c"], "a,c"),
    ],
)
def test_simple_graph_backed_asset_subset(
    job_selection: CoercibleToAssetSelection, expected_assets: str
):
    @dg.op
    def one():
        return 1

    @dg.op
    def add_one(x):
        return x + 1

    @dg.op(out=dg.Out(io_manager_key="asset_io_manager"))
    def create_asset(x):
        return x * 2

    @dg.graph
    def a():
        return create_asset(add_one(add_one(one())))

    @dg.graph
    def b(a):
        return create_asset(add_one(add_one(a)))

    @dg.graph
    def c(b):
        return create_asset(add_one(add_one(b)))

    a_asset = AssetsDefinition.from_graph(a)
    b_asset = AssetsDefinition.from_graph(b)
    c_asset = AssetsDefinition.from_graph(c)

    _, io_manager_def = asset_aware_io_manager()
    defs = dg.Definitions(
        assets=[a_asset, b_asset, c_asset],
        jobs=[dg.define_asset_job("assets_job", job_selection)],
        resources={"asset_io_manager": io_manager_def},
    )
    # materialize all assets once so values exist to load from
    defs.resolve_implicit_global_asset_job_def().execute_in_process()

    # now build the subset job
    job = defs.resolve_job_def("assets_job")

    result = job.execute_in_process()

    expected_asset_keys = set(dg.AssetKey(a) for a in expected_assets.split(","))

    # make sure we've generated the correct set of keys
    assert _all_asset_keys(result) == expected_asset_keys

    if dg.AssetKey("a") in expected_asset_keys:
        # (1 + 1 + 1) * 2
        assert result.output_for_node("a.create_asset") == 6
    if dg.AssetKey("b") in expected_asset_keys:
        # (6 + 1 + 1) * 8
        assert result.output_for_node("b.create_asset") == 16
    if dg.AssetKey("c") in expected_asset_keys:
        # (16 + 1 + 1) * 2
        assert result.output_for_node("c.create_asset") == 36


@pytest.mark.parametrize("use_multi", [True, False])
@pytest.mark.parametrize(
    "job_selection,expected_assets,prefixes",
    [
        ("*", "start,a,b,c,d,e,f,final", None),
        ("a", "a", None),
        ("b+", "b,c,d", None),
        ("+f", "f,d,e", None),
        ("++f", "f,d,e,c,a,b", None),
        ("start*", "start,a,d,f,final", None),
        (["+a", "b+"], "start,a,b,c,d", None),
        (["*c", "final"], "b,c,final", None),
        ("*", "start,a,b,c,d,e,f,final", ["core", "models"]),
        ("core/models/a", "a", ["core", "models"]),
        ("core/models/b+", "b,c,d", ["core", "models"]),
        ("+core/models/f", "f,d,e", ["core", "models"]),
        ("++core/models/f", "f,d,e,c,a,b", ["core", "models"]),
        ("core/models/start*", "start,a,d,f,final", ["core", "models"]),
        (["+core/models/a", "core/models/b+"], "start,a,b,c,d", ["core", "models"]),
        (["*core/models/c", "core/models/final"], "b,c,final", ["core", "models"]),
    ],
)
def test_asset_group_build_subset_job(job_selection, expected_assets, use_multi, prefixes):
    _, io_manager_def = asset_aware_io_manager()
    all_assets = _get_assets_defs(use_multi=use_multi, allow_subset=use_multi)
    # apply prefixes
    for prefix in reversed(prefixes or []):
        all_assets = [
            assets_def.with_attributes(
                asset_key_replacements={
                    k: k.with_prefix(prefix)
                    for k in set(assets_def.keys_by_input_name.values()) | set(assets_def.keys)
                },
            )
            for assets_def in all_assets
        ]

    defs = dg.Definitions(
        # for these, if we have multi assets, we'll always allow them to be subset
        assets=all_assets,
        jobs=[dg.define_asset_job("assets_job", job_selection)],
        resources={"io_manager": io_manager_def},
    )

    # materialize all assets once so values exist to load from
    defs.resolve_implicit_global_asset_job_def().execute_in_process()

    # now build the subset job
    job = defs.resolve_job_def("assets_job")

    with dg.instance_for_test() as instance:
        result = job.execute_in_process(instance=instance)
        planned_asset_keys = {
            record.event_log_entry.dagster_event.event_specific_data.asset_key  # pyright: ignore[reportAttributeAccessIssue,reportOptionalMemberAccess]
            for record in instance.get_records_for_run(
                run_id=result.run_id,
                of_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
            ).records
        }

    expected_asset_keys = set(
        dg.AssetKey([*(prefixes or []), a]) for a in expected_assets.split(",")
    )
    # make sure we've planned on the correct set of keys
    assert planned_asset_keys == expected_asset_keys

    # make sure we've generated the correct set of keys
    assert _all_asset_keys(result) == expected_asset_keys

    if use_multi:
        expected_outputs = {
            "start": 1,
            "abc_.a": 2,
            "abc_.b": 1,
            "abc_.c": 2,
            "def_.d": 3,
            "def_.e": 3,
            "def_.f": 6,
            "final": 5,
        }
    else:
        expected_outputs = {"start": 1, "a": 2, "b": 1, "c": 2, "d": 3, "e": 3, "f": 6, "final": 5}

    # check if the output values are as we expect
    for output, value in expected_outputs.items():
        asset_name = output.split(".")[-1]
        if asset_name in expected_assets.split(","):
            # dealing with multi asset
            if output != asset_name:
                node_def_name = output.split(".")[0]
                keys_for_node = {dg.AssetKey([*(prefixes or []), c]) for c in node_def_name[:-1]}
                selected_keys_for_node = keys_for_node.intersection(expected_asset_keys)
                if (
                    selected_keys_for_node != keys_for_node
                    # too much of a pain to explicitly encode the cases where we need to create a
                    # new node definition
                    and not result.job_def.has_node_named(node_def_name)
                ):
                    node_def_name += (
                        "_subset_"
                        + hashlib.md5(
                            (str(list(sorted(selected_keys_for_node)))).encode()
                        ).hexdigest()[-5:]
                    )
                assert result.output_for_node(node_def_name, asset_name)
            # dealing with regular asset
            else:
                assert result.output_for_node(output, "result") == value


def test_subset_cycle_resolution_embed_assets_in_complex_graph():
    """This represents a single large multi-asset with two assets embedded inside of it.

    Ops:
        foo produces: a, b, c, d, e, f, g, h
        x produces: x
        y produces: y

    Upstream Assets:
        a: []
        b: []
        c: [b]
        d: [b]
        e: [x, c]
        f: [d]
        g: [e]
        h: [g, y]
        x: [a]
        y: [e, f].
    """
    io_manager_obj, io_manager_def = asset_aware_io_manager()
    for item in "abcdefghxy":
        io_manager_obj.db[dg.AssetKey(item)] = None

    @dg.multi_asset(
        outs={name: dg.AssetOut(is_required=False) for name in "a,b,c,d,e,f,g,h".split(",")},
        internal_asset_deps={
            "a": set(),
            "b": set(),
            "c": {dg.AssetKey("b")},
            "d": {dg.AssetKey("b")},
            "e": {dg.AssetKey("c"), dg.AssetKey("x")},
            "f": {dg.AssetKey("d")},
            "g": {dg.AssetKey("e")},
            "h": {dg.AssetKey("g"), dg.AssetKey("y")},
        },
        can_subset=True,
    )
    def foo(context, x, y):
        assert (
            context.op_execution_context.selected_output_names
            != {"a", "b", "c", "d", "e", "f", "g", "h"}
        ) == context.is_subset

        a = b = c = d = e = f = g = h = None
        if "a" in context.op_execution_context.selected_output_names:
            a = 1
            yield dg.Output(a, "a")
        if "b" in context.op_execution_context.selected_output_names:
            b = 1
            yield dg.Output(b, "b")
        if "c" in context.op_execution_context.selected_output_names:
            c = (b or 1) + 1
            yield dg.Output(c, "c")
        if "d" in context.op_execution_context.selected_output_names:
            d = (b or 1) + 1
            yield dg.Output(d, "d")
        if "e" in context.op_execution_context.selected_output_names:
            e = x + (c or 2)
            yield dg.Output(e, "e")
        if "f" in context.op_execution_context.selected_output_names:
            f = (d or 1) + 1
            yield dg.Output(f, "f")
        if "g" in context.op_execution_context.selected_output_names:
            g = (e or 4) + 1
            yield dg.Output(g, "g")
        if "h" in context.op_execution_context.selected_output_names:
            h = (g or 5) + y
            yield dg.Output(h, "h")

    @dg.asset
    def x(a):
        return a + 1

    @dg.asset
    def y(e, f):
        return e + f

    job = dg.Definitions(
        assets=[foo, x, y],
        resources={"io_manager": io_manager_def},
    ).resolve_implicit_global_asset_job_def()

    # should produce a job with foo(a,b,c,d,f) -> x -> foo(e,g) -> y -> foo(h)
    assert len(list(job.graph.iterate_op_defs())) == 5
    result = job.execute_in_process()

    assert _all_asset_keys(result) == {dg.AssetKey(x) for x in "a,b,c,d,e,f,g,h,x,y".split(",")}
    assert result.output_for_node("foo_3", "h") == 12


def test_subset_cycle_resolution_complex():
    """Test cycle resolution.

    Ops:
        foo produces: a, b, c, d, e, f
        x produces: x
        y produces: y
        z produces: z

    Upstream Assets:
        a: []
        b: [x]
        c: [x]
        d: [y]
        e: [c]
        f: [d]
        x: [a]
        y: [b, c].
    """
    io_manager_obj, io_manager_def = asset_aware_io_manager()
    for item in "abcdefxy":
        io_manager_obj.db[dg.AssetKey(item)] = None

    @dg.multi_asset(
        outs={name: dg.AssetOut(is_required=False) for name in "a,b,c,d,e,f".split(",")},
        internal_asset_deps={
            "a": set(),
            "b": {dg.AssetKey("x")},
            "c": {dg.AssetKey("x")},
            "d": {dg.AssetKey("y")},
            "e": {dg.AssetKey("c")},
            "f": {dg.AssetKey("d")},
        },
        can_subset=True,
    )
    def foo(context, x, y):
        if "a" in context.op_execution_context.selected_output_names:
            yield dg.Output(1, "a")
        if "b" in context.op_execution_context.selected_output_names:
            yield dg.Output(x + 1, "b")
        if "c" in context.op_execution_context.selected_output_names:
            c = x + 2
            yield dg.Output(c, "c")
        if "d" in context.op_execution_context.selected_output_names:
            d = y + 1
            yield dg.Output(d, "d")
        if "e" in context.op_execution_context.selected_output_names:
            yield dg.Output(c + 1, "e")  # pyright: ignore[reportPossiblyUnboundVariable]
        if "f" in context.op_execution_context.selected_output_names:
            yield dg.Output(d + 1, "f")  # pyright: ignore[reportPossiblyUnboundVariable]

    @dg.asset
    def x(a):
        return a + 1

    @dg.asset
    def y(b, c):
        return b + c

    job = dg.Definitions(
        assets=[foo, x, y],
        resources={"io_manager": io_manager_def},
    ).resolve_implicit_global_asset_job_def()

    # should produce a job with foo -> x -> foo -> y -> foo
    assert len(list(job.graph.iterate_op_defs())) == 5
    result = job.execute_in_process()

    assert _all_asset_keys(result) == {dg.AssetKey(x) for x in "a,b,c,d,e,f,x,y".split(",")}
    assert result.output_for_node("x") == 2
    assert result.output_for_node("y") == 7
    assert result.output_for_node("foo_3", "f") == 9


@ignore_warning("Class `SourceAsset` is deprecated and will be removed in 2.0.0.")
def test_subset_cycle_resolution_basic():
    """Ops:
        foo produces: a, b
        foo_prime produces: a', b'
    Assets:
        s -> a -> a' -> b -> b'.
    """
    io_manager_obj, io_manager_def = asset_aware_io_manager()
    for item in "a,b,a_prime,b_prime".split(","):
        io_manager_obj.db[dg.AssetKey(item)] = None
    # some value for the source
    io_manager_obj.db[dg.AssetKey("s")] = 0

    s = dg.SourceAsset("s")

    @dg.multi_asset(
        outs={"a": dg.AssetOut(is_required=False), "b": dg.AssetOut(is_required=False)},
        internal_asset_deps={
            "a": {dg.AssetKey("s")},
            "b": {dg.AssetKey("a_prime")},
        },
        can_subset=True,
    )
    def foo(context, s, a_prime):
        context.log.info(context.selected_asset_keys)
        if dg.AssetKey("a") in context.selected_asset_keys:
            yield dg.Output(s + 1, "a")
        if dg.AssetKey("b") in context.selected_asset_keys:
            yield dg.Output(a_prime + 1, "b")

    @dg.multi_asset(
        outs={"a_prime": dg.AssetOut(is_required=False), "b_prime": dg.AssetOut(is_required=False)},
        internal_asset_deps={
            "a_prime": {dg.AssetKey("a")},
            "b_prime": {dg.AssetKey("b")},
        },
        can_subset=True,
    )
    def foo_prime(context, a, b):
        context.log.info(context.selected_asset_keys)
        if dg.AssetKey("a_prime") in context.selected_asset_keys:
            yield dg.Output(a + 1, "a_prime")
        if dg.AssetKey("b_prime") in context.selected_asset_keys:
            yield dg.Output(b + 1, "b_prime")

    job = dg.Definitions(
        assets=[foo, foo_prime, s],
        resources={"io_manager": io_manager_def},
    ).resolve_implicit_global_asset_job_def()

    # should produce a job with foo -> foo_prime -> foo_2 -> foo_prime_2
    assert len(list(job.graph.iterate_op_defs())) == 4

    result = job.execute_in_process()
    assert result.output_for_node("foo", "a") == 1
    assert result.output_for_node("foo_prime", "a_prime") == 2
    assert result.output_for_node("foo_2", "b") == 3
    assert result.output_for_node("foo_prime_2", "b_prime") == 4

    assert _all_asset_keys(result) == {
        dg.AssetKey("a"),
        dg.AssetKey("b"),
        dg.AssetKey("a_prime"),
        dg.AssetKey("b_prime"),
    }


def test_subset_cycle_resolution_with_checks():
    """Ops:
        foo produces: a, b
        foo_prime produces: a', b'
    Assets:
        s -> a -> a' -> b -> b'.
    """

    @dg.multi_asset(
        specs=[
            dg.AssetSpec("a", deps=["s"], skippable=True),
            dg.AssetSpec("b", deps=["a_prime"], skippable=True),
        ],
        can_subset=True,
    )
    def foo(context): ...

    @dg.multi_asset(
        specs=[
            dg.AssetSpec("a_prime", deps=["a"], skippable=True),
            dg.AssetSpec("b_prime", deps=["b"], skippable=True),
        ],
        check_specs=[
            dg.AssetCheckSpec("a_prime_is_good", asset="a_prime", additional_deps=["b"]),
        ],
        can_subset=True,
    )
    def foo_prime(context): ...

    defs = dg.Definitions(assets=[foo, foo_prime])

    Definitions.validate_loadable(defs)

    job = defs.resolve_implicit_global_asset_job_def()

    # should produce a job with foo -> foo_prime -> foo_2 -> foo_prime_2
    assert len(list(job.graph.iterate_op_defs())) == 4


@ignore_warning("Class `SourceAsset` is deprecated and will be removed in 2.0.0.")
def test_subset_cycle_resolution_asset_result():
    """Ops:
        foo produces: a, b
        foo_prime produces: a', b'
    Assets:
        s -> a -> a' -> b -> b'.
    """
    io_manager_obj, io_manager_def = asset_aware_io_manager()
    for item in "a,b,a_prime,b_prime".split(","):
        io_manager_obj.db[dg.AssetKey(item)] = None
    # some value for the source
    io_manager_obj.db[dg.AssetKey("s")] = 0

    s = dg.SourceAsset("s")

    @dg.multi_asset(
        outs={"a": dg.AssetOut(is_required=False), "b": dg.AssetOut(is_required=False)},
        internal_asset_deps={
            "a": {dg.AssetKey("s")},
            "b": {dg.AssetKey("a_prime")},
        },
        can_subset=True,
    )
    def foo(context, s, a_prime):
        context.log.info(context.selected_asset_keys)
        if dg.AssetKey("a") in context.selected_asset_keys:
            yield dg.MaterializeResult(asset_key=dg.AssetKey("a"))
        if dg.AssetKey("b") in context.selected_asset_keys:
            yield dg.MaterializeResult(asset_key=dg.AssetKey("b"))

    @dg.multi_asset(
        outs={"a_prime": dg.AssetOut(is_required=False), "b_prime": dg.AssetOut(is_required=False)},
        internal_asset_deps={
            "a_prime": {dg.AssetKey("a")},
            "b_prime": {dg.AssetKey("b")},
        },
        can_subset=True,
    )
    def foo_prime(context, a, b):
        context.log.info(context.selected_asset_keys)
        if dg.AssetKey("a_prime") in context.selected_asset_keys:
            yield dg.MaterializeResult(asset_key=dg.AssetKey("a_prime"))
        if dg.AssetKey("b_prime") in context.selected_asset_keys:
            yield dg.MaterializeResult(asset_key=dg.AssetKey("b_prime"))

    job = dg.Definitions(
        assets=[foo, foo_prime, s],
        resources={"io_manager": io_manager_def},
    ).resolve_implicit_global_asset_job_def()

    # should produce a job with foo -> foo_prime -> foo_2 -> foo_prime_2
    assert len(list(job.graph.iterate_op_defs())) == 4

    result = job.execute_in_process()

    assert _all_asset_keys(result) == {
        dg.AssetKey("a"),
        dg.AssetKey("b"),
        dg.AssetKey("a_prime"),
        dg.AssetKey("b_prime"),
    }


@ignore_warning("Class `SourceAsset` is deprecated and will be removed in 2.0.0.")
def test_subset_cycle_resolution_with_asset_check():
    """Ops:
        foo produces: a, b
        foo_prime produces: a', b'
    Assets:
        s -> a -> a' -> b -> b'.
    """
    io_manager_obj, io_manager_def = asset_aware_io_manager()
    for item in "a,b,a_prime,b_prime".split(","):
        io_manager_obj.db[dg.AssetKey(item)] = None
    # some value for the source
    io_manager_obj.db[dg.AssetKey("s")] = 0

    s = dg.SourceAsset("s")

    @dg.multi_asset(
        outs={"a": dg.AssetOut(is_required=False), "b": dg.AssetOut(is_required=False)},
        internal_asset_deps={
            "a": {dg.AssetKey("s")},
            "b": {dg.AssetKey("a_prime")},
        },
        can_subset=True,
    )
    def foo(context, s, a_prime):
        context.log.info(context.selected_asset_keys)
        if dg.AssetKey("a") in context.selected_asset_keys:
            yield dg.Output(s + 1, "a")
        if dg.AssetKey("b") in context.selected_asset_keys:
            yield dg.Output(a_prime + 1, "b")

    @dg.multi_asset(
        outs={"a_prime": dg.AssetOut(is_required=False), "b_prime": dg.AssetOut(is_required=False)},
        internal_asset_deps={
            "a_prime": {dg.AssetKey("a")},
            "b_prime": {dg.AssetKey("b")},
        },
        can_subset=True,
    )
    def foo_prime(context, a, b):
        context.log.info(context.selected_asset_keys)
        if dg.AssetKey("a_prime") in context.selected_asset_keys:
            yield dg.Output(a + 1, "a_prime")
        if dg.AssetKey("b_prime") in context.selected_asset_keys:
            yield dg.Output(b + 1, "b_prime")

    @dg.asset_check(asset="a_prime")
    def check_a_prime(a_prime):
        return dg.AssetCheckResult(passed=True)

    job = dg.Definitions(
        assets=[foo, foo_prime, s],
        asset_checks=[check_a_prime],
        resources={"io_manager": io_manager_def},
    ).resolve_implicit_global_asset_job_def()

    # should produce a job with foo -> foo_prime -> foo_2 -> foo_prime_2
    assert len(list(job.graph.iterate_op_defs())) == 5

    result = job.execute_in_process()
    assert result.output_for_node("foo", "a") == 1
    assert result.output_for_node("foo_prime", "a_prime") == 2
    assert result.output_for_node("foo_2", "b") == 3
    assert result.output_for_node("foo_prime_2", "b_prime") == 4

    assert _all_asset_keys(result) == {
        dg.AssetKey("a"),
        dg.AssetKey("b"),
        dg.AssetKey("a_prime"),
        dg.AssetKey("b_prime"),
    }


def test_subset_cycle_dependencies():
    """Ops:
        foo produces: top, a, b
        python produces: python
    Assets:
        top -> python -> b
        a -> b.
    """
    io_manager_obj, io_manager_def = asset_aware_io_manager()
    for item in "a,b,a_prime,b_prime".split(","):
        io_manager_obj.db[dg.AssetKey(item)] = None

    @dg.multi_asset(
        outs={
            "top": dg.AssetOut(is_required=False),
            "a": dg.AssetOut(is_required=False),
            "b": dg.AssetOut(is_required=False),
        },
        ins={
            "python": dg.AssetIn(dagster_type=Nothing),
        },
        internal_asset_deps={
            "top": set(),
            "a": set(),
            "b": {dg.AssetKey("a"), dg.AssetKey("python")},
        },
        can_subset=True,
    )
    def foo(context):
        for output in ["top", "a", "b"]:
            if output in context.op_execution_context.selected_output_names:
                yield dg.Output(output, output)

    @dg.asset(deps=[dg.AssetKey("top")])
    def python():
        return 1

    defs = dg.Definitions(
        assets=[foo, python],
        resources={"io_manager": io_manager_def},
    )
    job = defs.resolve_implicit_global_asset_job_def()

    # should produce a job with foo -> python -> foo_2
    assert len(list(job.graph.iterate_op_defs())) == 3
    assert job.graph.dependencies == {
        dg.NodeInvocation(name="foo"): {},
        dg.NodeInvocation(name="foo", alias="foo_2"): {
            "__subset_input__a": dg.DependencyDefinition(node="foo", output="a"),
            "python": dg.DependencyDefinition(node="python", output="result"),
        },
        dg.NodeInvocation(name="python"): {
            "top": dg.DependencyDefinition(node="foo", output="top")
        },
    }

    result = job.execute_in_process()
    assert result.success
    assert _all_asset_keys(result) == {
        dg.AssetKey("a"),
        dg.AssetKey("b"),
        dg.AssetKey("top"),
        dg.AssetKey("python"),
    }

    # now create a job that just executes a and b
    job = job.get_subset(asset_selection={dg.AssetKey("a"), dg.AssetKey("b")})
    # can satisfy this with just a single op
    assert len(list(job.graph.iterate_op_defs())) == 1
    assert job.graph.dependencies == {dg.NodeInvocation(name="foo"): {}}
    result = job.execute_in_process()
    assert result.success
    assert _all_asset_keys(result) == {dg.AssetKey("a"), dg.AssetKey("b")}


def test_subset_recongeal() -> None:
    # In this test, we create a job that requires multi-asset `acd` to be broken up into two pieces
    # in order to accomodate the inclusion of `b` in the job, as `b` depends on `a`, but is depended
    # on by `c` and `d`.
    #
    # We ensure that this subsetting happens, and then ensure that when we subset this job to include
    # only `a` and `c`, the resulting graph "recongeals", and puts the multi-asset back together again,
    # as it is no longer necessary to break it apart.
    import dagster as dg

    @dg.multi_asset(
        specs=[
            dg.AssetSpec("a", skippable=True),
            dg.AssetSpec("c", deps="b", skippable=True),
            dg.AssetSpec("d", deps=["a", "b"], skippable=True),
        ],
        can_subset=True,
    )
    def acd(context: dg.AssetExecutionContext):
        context.log.info(f"{context.selected_asset_keys}")
        for selected in sorted(context.op_execution_context.selected_output_names):
            yield dg.Output(None, selected)

    @dg.asset(deps=["a"])
    def b() -> None: ...

    defs = dg.Definitions(assets=[acd, b])
    all_job = defs.resolve_implicit_global_asset_job_def()
    subset_job = all_job.get_subset(asset_selection={dg.AssetKey("a"), dg.AssetKey("c")})
    assert len(list(subset_job.graph.iterate_op_defs())) == 1
    assert all_job.graph.dependencies == {
        dg.NodeInvocation(name="acd"): {},
        dg.NodeInvocation(name="b"): {
            "a": dg.DependencyDefinition(node="acd", output="a"),
        },
        dg.NodeInvocation(name="acd", alias="acd_2"): {
            "__subset_input__a": dg.DependencyDefinition(node="acd", output="a"),
            "b": dg.DependencyDefinition(node="b", output="result"),
        },
    }
    result = all_job.execute_in_process()
    assert result.success
    assert _all_asset_keys(result) == {
        dg.AssetKey("a"),
        dg.AssetKey("b"),
        dg.AssetKey("c"),
        dg.AssetKey("d"),
    }
    # only need a single op to make this work
    assert len(list(subset_job.graph.iterate_op_defs())) == 1
    assert subset_job.graph.dependencies == {dg.NodeInvocation(name="acd"): {}}
    result = subset_job.execute_in_process()
    assert result.success
    assert _all_asset_keys(result) == {dg.AssetKey("a"), dg.AssetKey("c")}


def test_exclude_assets_without_keys():
    @dg.asset
    def foo():
        pass

    # This is a valid AssetsDefinition but has no keys. It should not be executed.
    @dg.multi_asset()
    def ghost():
        assert False

    foo_job = dg.Definitions(
        assets=[foo, ghost],
        jobs=[dg.define_asset_job("foo_job", [foo])],
    ).resolve_job_def("foo_job")

    assert foo_job.execute_in_process().success


def test_mixed_asset_job():
    with disable_dagster_warnings():

        class MyIOManager(dg.IOManager):
            def handle_output(self, context, obj):
                pass

            def load_input(self, context):
                return 5

        @dg.observable_source_asset
        def foo():
            return dg.DataVersion("alpha")

        @dg.asset
        def bar(foo):
            return foo + 1

        defs = dg.Definitions(
            assets=[foo, bar],
            jobs=[dg.define_asset_job("mixed_assets_job", [foo, bar])],
            resources={"io_manager": MyIOManager()},
        )

        job_def = defs.resolve_job_def("mixed_assets_job")
        result = job_def.execute_in_process()
        assert result.success
        assert len(result.asset_materializations_for_node("foo")) == 0
        assert len(result.asset_observations_for_node("foo")) == 1
        assert len(result.asset_materializations_for_node("bar")) == 1
        assert len(result.asset_observations_for_node("bar")) == 0


def test_partial_dependency_on_upstream_multi_asset():
    class MyIOManager(dg.IOManager):
        def __init__(self):
            self.values: dict[dg.AssetKey, int] = {}

        def handle_output(self, context: OutputContext, obj: object):
            self.values[context.asset_key] = obj  # pyright: ignore[reportArgumentType]

        def load_input(self, context: InputContext) -> object:
            return self.values[context.asset_key]

    @dg.multi_asset(
        outs={
            "foo": dg.AssetOut(),
            "bar": dg.AssetOut(),
        }
    )
    def foo_bar():
        yield dg.Output(1, "foo")
        yield dg.Output(1, "bar")

    @dg.asset
    def baz(foo):
        return foo + 1

    # populate storage with foo/bar values
    resources = {"io_manager": MyIOManager()}
    create_test_asset_job([foo_bar]).execute_in_process(resources=resources)

    job_def = create_test_asset_job([baz, foo_bar], selection=[baz])
    assert job_def.execute_in_process(resources=resources).success


def test_job_definition_with_resolution_error():
    @dg.asset
    def foo():
        return 1

    defs = dg.Definitions(
        assets=[foo],
        jobs=[
            dg.define_asset_job("invalid_job", selection=AssetSelection.assets(["does_not_exist"]))
        ],
    )

    with pytest.raises(
        dg.DagsterInvalidDefinitionError, match="Failed to resolve asset job invalid_job"
    ):
        defs.get_repository_def().get_all_jobs()
