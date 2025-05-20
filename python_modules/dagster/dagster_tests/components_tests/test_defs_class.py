from dagster import AssetKey, asset, asset_check
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_key import AssetCheckKey
from dagster._core.definitions.decorators.source_asset_decorator import observable_source_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.external_asset import create_external_asset_from_source_asset
from dagster._core.definitions.source_asset import SourceAsset
from dagster.components.defs import Defs


def test_basic_defs() -> None:
    defs = Defs(Definitions())
    assert defs.asset_specs == {}
    assert defs.assets_defs == {}
    assert defs.asset_checks_defs == {}
    assert defs.asset_check_specs == {}


def test_assets_def_to_assets() -> None:
    @asset
    def asset_1():
        pass

    defs = Defs(Definitions(assets=[asset_1]))

    assert set(defs.assets_defs.keys()) == {AssetKey(["asset_1"])}
    assert defs.get_asset_spec("asset_1").key == AssetKey(["asset_1"])
    assert defs.get_asset_spec(AssetKey(["asset_1"])).key == AssetKey(["asset_1"])
    assert defs.asset_checks_defs == {}
    assert defs.asset_check_specs == {}


def test_assets_def_to_assets_checks() -> None:
    @asset
    def asset_1():
        pass

    defs = Defs(Definitions(asset_checks=[asset_1]))

    assert set(defs.assets_defs.keys()) == {AssetKey(["asset_1"])}
    assert defs.get_asset_spec("asset_1").key == AssetKey(["asset_1"])
    assert defs.get_asset_spec(AssetKey(["asset_1"])).key == AssetKey(["asset_1"])
    assert defs.asset_checks_defs == {}
    assert defs.asset_check_specs == {}


def test_assets_checks_def_to_assets_checks() -> None:
    @asset_check(asset="asset_1")
    def check_1() -> AssetCheckResult: ...

    defs = Defs(Definitions(asset_checks=[check_1]))

    assert set(defs.asset_checks_defs.keys()) == {
        AssetCheckKey(asset_key=AssetKey(["asset_1"]), name="check_1")
    }
    assert defs.get_asset_check_spec(
        AssetCheckKey(asset_key=AssetKey(["asset_1"]), name="check_1")
    ).key == AssetCheckKey(asset_key=AssetKey(["asset_1"]), name="check_1")
    assert defs.get_asset_check_spec(
        AssetCheckKey(asset_key=AssetKey(["asset_1"]), name="check_1")
    ).asset_key == AssetKey(["asset_1"])

    assert defs.assets_defs == {}
    # external assets are not implicitly generated from references
    assert defs.asset_specs == {}


def test_assets_checks_def_to_assets() -> None:
    @asset_check(asset="asset_1")
    def check_1() -> AssetCheckResult: ...

    defs = Defs(Definitions(assets=[check_1]))

    assert set(defs.asset_checks_defs.keys()) == {
        AssetCheckKey(asset_key=AssetKey(["asset_1"]), name="check_1")
    }
    assert defs.get_asset_check_spec(
        AssetCheckKey(asset_key=AssetKey(["asset_1"]), name="check_1")
    ).key == AssetCheckKey(asset_key=AssetKey(["asset_1"]), name="check_1")
    assert defs.get_asset_check_spec(
        AssetCheckKey(asset_key=AssetKey(["asset_1"]), name="check_1")
    ).asset_key == AssetKey(["asset_1"])

    assert defs.assets_defs == {}
    # external assets are not implicitly generated from references
    assert defs.asset_specs == {}


def test_canonicalize_source_asset() -> None:
    source_asset = SourceAsset("asset_1")
    defs = Defs(Definitions(assets=[source_asset]))

    external_assets_def = create_external_asset_from_source_asset(source_asset)
    assert not external_assets_def.is_observable

    assert defs.get_asset_spec("asset_1").key == AssetKey(["asset_1"])
    assert defs.get_asset_spec(AssetKey(["asset_1"])).key == AssetKey(["asset_1"])
    assert set(defs.assets_defs.keys()) == set()
    assert defs.asset_checks_defs == {}
    assert defs.asset_check_specs == {}


def test_canonicalize_observable_source_asset() -> None:
    @observable_source_asset()
    def asset_1(): ...

    defs = Defs(Definitions(assets=[asset_1]))

    assert defs.get_asset_spec("asset_1").key == AssetKey(["asset_1"])
    assert defs.get_asset_spec(AssetKey(["asset_1"])).key == AssetKey(["asset_1"])
    assert set(defs.assets_defs.keys()) == {AssetKey(["asset_1"])}
    assert defs.asset_checks_defs == {}
    assert defs.asset_check_specs == {}
