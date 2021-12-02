import pytest
from dagster import (
    AssetKey,
    DependencyDefinition,
    IOManager,
    io_manager,
    DagsterInvalidDefinitionError,
)
from dagster.core.asset_defs import ForeignAsset, asset, build_assets_job, AssetIn


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


def test_asset_key_for_asset_with_namespace():
    @asset(namespace="hello")
    def asset_foo():
        return "foo"

    @asset(
        ins={"foo": AssetIn(asset_key=AssetKey("asset_foo"))}
    )  # Should fail because asset_foo is defined with namespace, so has asset key ["hello", "asset_foo"]
    def failing_asset(foo):
        pass

    with pytest.raises(DagsterInvalidDefinitionError):
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
