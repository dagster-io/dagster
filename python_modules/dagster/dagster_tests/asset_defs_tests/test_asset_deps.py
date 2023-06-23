# TODO - for ease of initial review, putting all of these tests in a single file. After a review pass,
# I can sort them out into the files that make sense for each test

import pytest
from dagster import AssetKey, AssetOut, IOManager, SourceAsset, asset, materialize, multi_asset
from dagster._check import CheckError
from dagster._core.types.dagster_type import DagsterTypeKind


class TestingIOManager(IOManager):
    def handle_output(self, context, obj):
        return None

    def load_input(self, context):
        # we should be bypassing the IO Manager, so fail if try to load an input
        assert False


def test_single_asset_deps_via_assets_definition():
    @asset
    def asset_1():
        return None

    @asset(deps=[asset_1])
    def asset_2():
        return None

    assert len(asset_2.input_names) == 1
    assert asset_2.op.ins["asset_1"].dagster_type.kind == DagsterTypeKind.NOTHING

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_single_asset_deps_via_string():
    @asset
    def asset_1():
        return None

    @asset(deps=["asset_1"])
    def asset_2():
        return None

    assert len(asset_2.input_names) == 1
    assert asset_2.op.ins["asset_1"].dagster_type.kind == DagsterTypeKind.NOTHING

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_single_asset_deps_via_asset_key():
    @asset
    def asset_1():
        return None

    @asset(deps=[AssetKey("asset_1")])
    def asset_2():
        return None

    assert len(asset_2.input_names) == 1
    assert asset_2.op.ins["asset_1"].dagster_type.kind == DagsterTypeKind.NOTHING

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_single_asset_deps_via_mixed_types():
    @asset
    def via_definition():
        return None

    @asset
    def via_string():
        return None

    @asset
    def via_asset_key():
        return None

    @asset(deps=[via_definition, "via_string", AssetKey("via_asset_key")])
    def downstream():
        return None

    assert len(downstream.input_names) == 3
    assert downstream.op.ins["via_definition"].dagster_type.kind == DagsterTypeKind.NOTHING
    assert downstream.op.ins["via_string"].dagster_type.kind == DagsterTypeKind.NOTHING
    assert downstream.op.ins["via_asset_key"].dagster_type.kind == DagsterTypeKind.NOTHING

    res = materialize(
        [via_definition, via_string, via_asset_key, downstream],
        resources={"io_manager": TestingIOManager()},
    )
    assert res.success


def test_mulit_asset_deps_via_string():
    @multi_asset(
        outs={
            "asset_1": AssetOut(),
            "asset_2": AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @asset(deps=["asset_1"])
    def depends_on_one_sub_asset():
        return None

    assert len(depends_on_one_sub_asset.input_names) == 1
    assert depends_on_one_sub_asset.op.ins["asset_1"].dagster_type.kind == DagsterTypeKind.NOTHING

    @asset(deps=["asset_1", "asset_2"])
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.kind == DagsterTypeKind.NOTHING
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.kind == DagsterTypeKind.NOTHING

    res = materialize(
        [a_multi_asset, depends_on_one_sub_asset, depends_on_both_sub_assets],
        resources={"io_manager": TestingIOManager()},
    )
    assert res.success


def test_mulit_asset_deps_via_key():
    @multi_asset(
        outs={
            "asset_1": AssetOut(),
            "asset_2": AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @asset(deps=[AssetKey("asset_1")])
    def depends_on_one_sub_asset():
        return None

    assert len(depends_on_one_sub_asset.input_names) == 1
    assert depends_on_one_sub_asset.op.ins["asset_1"].dagster_type.kind == DagsterTypeKind.NOTHING

    @asset(deps=[AssetKey("asset_1"), AssetKey("asset_2")])
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.kind == DagsterTypeKind.NOTHING
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.kind == DagsterTypeKind.NOTHING

    res = materialize(
        [a_multi_asset, depends_on_one_sub_asset, depends_on_both_sub_assets],
        resources={"io_manager": TestingIOManager()},
    )
    assert res.success


def test_mulit_asset_deps_via_mixed_types():
    @multi_asset(
        outs={
            "asset_1": AssetOut(),
            "asset_2": AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @asset(deps=[AssetKey("asset_1"), "asset_2"])
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.kind == DagsterTypeKind.NOTHING
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.kind == DagsterTypeKind.NOTHING

    res = materialize(
        [a_multi_asset, depends_on_both_sub_assets], resources={"io_manager": TestingIOManager()}
    )
    assert res.success


def test_mulit_asset_deps_via_assets_definition_fails():
    @multi_asset(
        outs={
            "asset_1": AssetOut(),
            "asset_2": AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    with pytest.raises(
        CheckError,
        match="Tried to retrieve asset key from an assets definition with multiple asset keys",
    ):

        @asset(deps=[a_multi_asset])
        def depends_on_both_sub_assets():
            return None


def test_source_asset_deps_via_assets_definition():
    a_source_asset = SourceAsset("a_key")

    @asset(deps=[a_source_asset])
    def depends_on_source_asset():
        return None

    assert len(depends_on_source_asset.input_names) == 1
    assert depends_on_source_asset.op.ins["a_key"].dagster_type.kind == DagsterTypeKind.NOTHING

    res = materialize([depends_on_source_asset], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_source_asset_deps_via_string():
    a_source_asset = SourceAsset("a_key")  # noqa: F841

    @asset(deps=["a_key"])
    def depends_on_source_asset():
        return None

    assert len(depends_on_source_asset.input_names) == 1
    assert depends_on_source_asset.op.ins["a_key"].dagster_type.kind == DagsterTypeKind.NOTHING

    res = materialize([depends_on_source_asset], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_source_asset_deps_via_key():
    a_source_asset = SourceAsset("a_key")  # noqa: F841

    @asset(deps=[AssetKey("a_key")])
    def depends_on_source_asset():
        return None

    assert len(depends_on_source_asset.input_names) == 1
    assert depends_on_source_asset.op.ins["a_key"].dagster_type.kind == DagsterTypeKind.NOTHING

    res = materialize([depends_on_source_asset], resources={"io_manager": TestingIOManager()})
    assert res.success
