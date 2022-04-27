import os

import pytest

from dagster import (
    AssetKey,
    AssetsDefinition,
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    DependencyDefinition,
    GraphOut,
    IOManager,
    Out,
    ResourceDefinition,
    graph,
    io_manager,
    op,
)
from dagster.core.asset_defs import AssetIn, SourceAsset, asset, build_assets_job
from dagster.core.snap import DependencyStructureIndex
from dagster.core.snap.dep_snapshot import (
    OutputHandleSnap,
    build_dep_structure_snapshot_from_icontains_solids,
)
from dagster.utils import safe_tempfile_path


def _asset_keys_for_node(result, node_name):
    mats = result.asset_materializations_for_node(node_name)
    ret = {mat.asset_key for mat in mats}
    assert len(mats) == len(ret)
    return ret


def test_single_asset_pipeline():
    @asset
    def asset1():
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

    @asset(ins={"hello": AssetIn(asset_key=AssetKey("asset1"))})
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
        ins={"asset_bar": AssetIn(asset_key=AssetKey("asset_foo"))}
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

    @asset(ins={"foo": AssetIn(asset_key=AssetKey("asset_foo"))})
    def asset_baz(foo, asset_bar):
        return foo + asset_bar

    job = build_assets_job("hello", [asset_foo, asset_bar, asset_baz])
    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("asset_baz") == 7
    assert _asset_keys_for_node(result, "asset_baz") == {AssetKey("asset_baz")}


def test_asset_key_for_asset_with_namespace_list():
    @asset(namespace=["hell", "o"])
    def asset_foo():
        return "foo"

    @asset(
        ins={"foo": AssetIn(asset_key=AssetKey("asset_foo"))}
    )  # Should fail because asset_foo is defined with namespace, so has asset key ["hello", "asset_foo"]
    def failing_asset(foo):  # pylint: disable=unused-argument
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
    ):
        build_assets_job("lol", [asset_foo, failing_asset])

    @asset(ins={"foo": AssetIn(asset_key=AssetKey(["hell", "o", "asset_foo"]))})
    def success_asset(foo):
        return foo

    job = build_assets_job("lol", [asset_foo, success_asset])

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("success_asset") == "foo"
    assert _asset_keys_for_node(result, "hell__o__asset_foo") == {
        AssetKey(["hell", "o", "asset_foo"])
    }


def test_asset_key_for_asset_with_namespace_str():
    @asset(namespace="hello")
    def asset_foo():
        return "foo"

    @asset(ins={"foo": AssetIn(asset_key=AssetKey(["hello", "asset_foo"]))})
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
            return 5

    @io_manager(config_schema={"a": int}, required_resource_keys={"subresource"})
    def my_io_manager(_):
        return MyIOManager()

    job = build_assets_job(
        "a",
        [asset1],
        source_assets=[SourceAsset(AssetKey("source1"), io_manager_key="special_io_manager")],
        resource_defs={
            "special_io_manager": my_io_manager.configured({"a": 7}),
            "subresource": ResourceDefinition.hardcoded_resource(9),
        },
    )
    assert job.graph.node_defs == [asset1.op]
    result = job.execute_in_process()
    assert result.success
    assert _asset_keys_for_node(result, "asset1") == {AssetKey("asset1")}


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


def test_multiple_non_argument_deps():
    @asset
    def foo():
        pass

    @asset(namespace="namespace")
    def bar():
        pass

    @asset
    def baz():
        return 1

    @asset(non_argument_deps={AssetKey("foo"), AssetKey(["namespace", "bar"])})
    def qux(baz):
        return baz

    job = build_assets_job("a", [foo, bar, baz, qux])

    dep_structure_snapshot = build_dep_structure_snapshot_from_icontains_solids(job.graph)
    index = DependencyStructureIndex(dep_structure_snapshot)

    assert index.get_invocation("foo")
    assert index.get_invocation("namespace__bar")
    assert index.get_invocation("baz")

    assert index.get_upstream_outputs("qux", "foo") == [
        OutputHandleSnap("foo", "result"),
    ]
    assert index.get_upstream_outputs("qux", "namespace_bar") == [
        OutputHandleSnap("namespace__bar", "result")
    ]
    assert index.get_upstream_outputs("qux", "baz") == [OutputHandleSnap("baz", "result")]

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("qux") == 1
    assert _asset_keys_for_node(result, "namespace__bar") == {AssetKey(["namespace", "bar"])}
    assert _asset_keys_for_node(result, "qux") == {AssetKey("qux")}


def test_basic_graph_asset():
    @op
    def return_one():
        return 1

    @op
    def add_one(in1):
        pass

    @graph
    def create_cool_thing():
        return add_one(add_one(return_one()))

    cool_thing_asset = AssetsDefinition(
        asset_keys_by_input_name={},
        asset_keys_by_output_name={"result": AssetKey("cool_thing")},
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
        asset_keys_by_input_name={"a": AssetKey("a"), "b": AssetKey("b")},
        asset_keys_by_output_name={"result": AssetKey("cool_thing")},
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
        asset_keys_by_input_name={"a": AssetKey("a"), "b": AssetKey("b")},
        asset_keys_by_output_name={"o1": AssetKey("out_asset1"), "o2": AssetKey("out_asset2")},
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
        asset_keys_by_input_name={"a": AssetKey("a"), "b": AssetKey("b")},
        asset_keys_by_output_name={"o1": AssetKey("out_asset1"), "o2": AssetKey("out_asset2")},
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


def test_fail_with_get_output_asset_key():
    @io_manager
    def my_io_manager(context):
        class Mine(IOManager):
            def get_output_asset_key(self, context):
                return AssetKey("hey")

            def handle_output(self, context, obj):
                pass

            def load_input(self, context):
                return None

        return Mine()

    @asset
    def foo():
        return 1

    @asset
    def bar(foo):
        return foo + 1

    job = build_assets_job("x", [foo, bar], resource_defs={"io_manager": my_io_manager})
    with pytest.raises(
        DagsterInvariantViolationError,
        match='The IOManager of output "result" on node "foo" associates it with asset key '
        "\"AssetKey\(\['hey'\]\)\", but this output has already been defined to produce asset "
        "\"AssetKey\(\['foo'\]\)\"",
    ):
        job.execute_in_process()
