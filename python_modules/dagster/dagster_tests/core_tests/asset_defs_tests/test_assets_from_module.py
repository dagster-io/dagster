import re
import pytest
from dagster import (
    asset,
    AssetKey,
    SourceAsset,
    DagsterInvalidDefinitionError,
    assets_from_modules,
    assets_from_current_module,
    assets_from_package_module,
    assets_from_package_name,
)


def test_asset_group_from_package_name():
    from . import asset_package

    assets, source_assets = assets_from_package_name(asset_package.__name__)
    assert len(assets) == 6

    assets_1 = [asset.op.name for asset in assets]
    source_assets_1 = [source_asset.key for source_asset in source_assets]

    assets_2, source_assets_2 = assets_from_package_name(asset_package.__name__)
    assert len(assets_2) == 6

    assets_2 = [asset.op.name for asset in assets_2]
    source_assets_2 = [source_asset.key for source_asset in source_assets_2]

    assert assets_1 == assets_2
    assert source_assets_1 == source_assets_2


def test_asset_group_from_package_module():
    from . import asset_package

    assets_1, source_assets_1 = assets_from_package_module(asset_package)
    assert len(assets_1) == 6

    assets_1 = [asset.op.name for asset in assets_1]
    source_assets_1 = [source_asset.key for source_asset in source_assets_1]

    assets_2, source_assets_2 = assets_from_package_module(asset_package)
    assert len(assets_2) == 6

    assets_2 = [asset.op.name for asset in assets_2]
    source_assets_2 = [source_asset.key for source_asset in source_assets_2]

    assert assets_1 == assets_2
    assert source_assets_1 == source_assets_2


def test_asset_group_from_modules(monkeypatch):
    from . import asset_package
    from .asset_package import module_with_assets

    collection_1 = assets_from_modules([asset_package, module_with_assets])

    assets_1 = [asset.op.name for asset in collection_1[0]]
    source_assets_1 = [source_asset.key for source_asset in collection_1[1]]

    collection_2 = assets_from_modules([asset_package, module_with_assets])

    assets_2 = [asset.op.name for asset in collection_2[0]]
    source_assets_2 = [source_asset.key for source_asset in collection_2[1]]

    assert assets_1 == assets_2
    assert source_assets_1 == source_assets_2

    with monkeypatch.context() as m:

        @asset
        def little_richard():
            pass

        m.setattr(asset_package, "little_richard_dup", little_richard, raising=False)
        with pytest.raises(
            DagsterInvalidDefinitionError,
            match=re.escape(
                "Asset key AssetKey(['little_richard']) is defined multiple times. "
                "Definitions found in modules: dagster_tests.core_tests.asset_defs_tests.asset_package."
            ),
        ):
            assets_from_modules([asset_package, module_with_assets])


@asset
def asset_in_current_module():
    pass


source_asset_in_current_module = SourceAsset(AssetKey("source_asset_in_current_module"))


def test_asset_group_from_current_module():
    assets, source_assets = assets_from_current_module()
    assert {asset.op.name for asset in assets} == {"asset_in_current_module"}
    assert len(assets) == 1
    assert {source_asset.key for source_asset in source_assets} == {
        AssetKey("source_asset_in_current_module")
    }
    assert len(source_assets) == 1
