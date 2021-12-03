import os

import pytest
from dagster import (
    AssetKey,
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    IOManager,
    io_manager,
)
from dagster.core.asset_defs import AssetIn, ForeignAsset, asset, build_assets_job
from dagster.core.snap import DependencyStructureIndex
from dagster.core.snap.dep_snapshot import (
    OutputHandleSnap,
    build_dep_structure_snapshot_from_icontains_solids,
)
from dagster.utils import safe_tempfile_path


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
    assert job.execute_in_process().success


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


def test_asset_key_for_asset_with_namespace():
    @asset(namespace="hello")
    def asset_foo():
        return "foo"

    @asset(
        ins={"foo": AssetIn(asset_key=AssetKey("asset_foo"))}
    )  # Should fail because asset_foo is defined with namespace, so has asset key ["hello", "asset_foo"]
    def failing_asset(foo):
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
    ):
        build_assets_job("lol", [asset_foo, failing_asset])

    @asset(ins={"foo": AssetIn(asset_key=AssetKey(["hello", "asset_foo"]))})
    def success_asset(foo):
        return foo

    job = build_assets_job("lol", [asset_foo, success_asset])

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("success_asset") == "foo"


def test_foreign_asset():
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
        source_assets=[ForeignAsset(AssetKey("source1"), io_manager_key="special_io_manager")],
        resource_defs={"special_io_manager": my_io_manager},
    )
    assert job.graph.node_defs == [asset1.op]
    assert job.execute_in_process().success


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
    assert job.execute_in_process().success


def test_non_argument_deps():
    with safe_tempfile_path() as path:

        @asset
        def foo():
            with open(path, "w") as ff:
                ff.write("yup")

        @asset(non_argument_deps={AssetKey("foo")})
        def bar():
            # assert that the foo asset already executed
            assert os.path.exists(path)

        job = build_assets_job("a", [foo, bar])
        assert job.execute_in_process().success


def test_multiple_non_argument_deps():
    @asset
    def foo():
        pass

    @asset
    def bar():
        pass

    @asset
    def baz():
        return 1

    @asset(non_argument_deps={AssetKey("foo"), AssetKey("bar")})
    def qux(baz):
        return baz

    job = build_assets_job("a", [foo, bar, baz, qux])

    dep_structure_snapshot = build_dep_structure_snapshot_from_icontains_solids(job.graph)
    index = DependencyStructureIndex(dep_structure_snapshot)

    assert index.get_invocation("foo")
    assert index.get_invocation("bar")
    assert index.get_invocation("baz")

    assert index.get_upstream_outputs("qux", "foo") == [
        OutputHandleSnap("foo", "result"),
    ]
    assert index.get_upstream_outputs("qux", "bar") == [OutputHandleSnap("bar", "result")]
    assert index.get_upstream_outputs("qux", "baz") == [OutputHandleSnap("baz", "result")]

    result = job.execute_in_process()
    assert result.success
    assert result.output_for_node("qux") == 1
