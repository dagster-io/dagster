import re
from typing import Sequence, Union, cast

import pytest
from dagster import (
    AssetKey,
    AssetsDefinition,
    DagsterInvalidDefinitionError,
    FreshnessPolicy,
    SourceAsset,
    asset,
    load_assets_from_current_module,
    load_assets_from_modules,
    load_assets_from_package_module,
    load_assets_from_package_name,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition

get_unique_asset_identifier = lambda asset: (
    asset.node_def.name if isinstance(asset, AssetsDefinition) else asset.key
)


def check_asset_group(assets):
    for a in assets:
        if isinstance(a, AssetsDefinition):
            asset_keys = a.keys
            for asset_key in asset_keys:
                assert a.group_names_by_key.get(asset_key) == "my_cool_group"
        elif isinstance(a, SourceAsset):
            assert a.group_name == "my_cool_group"


def check_freshness_policy(assets, freshness_policy):
    for a in assets:
        if isinstance(a, AssetsDefinition):
            asset_keys = a.keys
            for asset_key in asset_keys:
                assert a.freshness_policies_by_key.get(asset_key) == freshness_policy, asset_key


def check_auto_materialize_policy(assets, auto_materialize_policy):
    for a in assets:
        if isinstance(a, AssetsDefinition):
            asset_keys = a.keys
            for asset_key in asset_keys:
                assert (
                    a.auto_materialize_policies_by_key.get(asset_key) == auto_materialize_policy
                ), asset_key


def assert_assets_have_prefix(
    prefix: Union[str, Sequence[str]], assets: Sequence[AssetsDefinition]
) -> None:
    for a in assets:
        if isinstance(a, AssetsDefinition):
            asset_keys = a.keys
            for asset_key in asset_keys:
                observed_prefix = asset_key.path[:-1]
                if len(observed_prefix) == 1:
                    observed_prefix = observed_prefix[0]
                assert observed_prefix == prefix


def get_assets_def_with_key(
    assets: Sequence[Union[AssetsDefinition, SourceAsset]], key: AssetKey
) -> AssetsDefinition:
    assets_by_key = {
        key: assets_def
        for assets_def in assets
        if isinstance(assets_def, AssetsDefinition)
        for key in assets_def.keys
    }
    return assets_by_key[key]


def get_source_asset_with_key(
    assets: Sequence[Union[AssetsDefinition, SourceAsset]], key: AssetKey
) -> SourceAsset:
    source_assets_by_key = {
        source_asset.key: source_asset
        for source_asset in assets
        if isinstance(source_asset, SourceAsset)
    }
    return source_assets_by_key[key]


def test_load_assets_from_package_name():
    from dagster_tests.asset_defs_tests import asset_package

    assets_defs = load_assets_from_package_name(asset_package.__name__)
    assert len(assets_defs) == 11

    assets_1 = [get_unique_asset_identifier(asset) for asset in assets_defs]

    assets_defs_2 = load_assets_from_package_name(asset_package.__name__)
    assert len(assets_defs_2) == 11

    assets_2 = [get_unique_asset_identifier(asset) for asset in assets_defs]

    assert assets_1 == assets_2


def test_load_assets_from_package_module():
    from dagster_tests.asset_defs_tests import asset_package

    assets_1 = load_assets_from_package_module(asset_package)
    assert len(assets_1) == 11

    assets_1 = [get_unique_asset_identifier(asset) for asset in assets_1]

    assets_2 = load_assets_from_package_module(asset_package)
    assert len(assets_2) == 11

    assets_2 = [get_unique_asset_identifier(asset) for asset in assets_2]

    assert assets_1 == assets_2


def test_load_assets_from_modules(monkeypatch):
    from dagster_tests.asset_defs_tests import asset_package
    from dagster_tests.asset_defs_tests.asset_package import module_with_assets

    collection_1 = load_assets_from_modules([asset_package, module_with_assets])

    assets_1 = [get_unique_asset_identifier(asset) for asset in collection_1]

    collection_2 = load_assets_from_modules([asset_package, module_with_assets])

    assets_2 = [get_unique_asset_identifier(asset) for asset in collection_2]

    assert assets_1 == assets_2

    with monkeypatch.context() as m:

        @asset
        def little_richard():
            pass

        m.setattr(asset_package, "little_richard_dup", little_richard, raising=False)
        with pytest.raises(
            DagsterInvalidDefinitionError,
            match=re.escape(
                "Asset key AssetKey(['little_richard']) is defined multiple times. "
                "Definitions found in modules: dagster_tests.asset_defs_tests.asset_package."
            ),
        ):
            load_assets_from_modules([asset_package, module_with_assets])


@asset(group_name="my_group")
def asset_in_current_module():
    pass


source_asset_in_current_module = SourceAsset(AssetKey("source_asset_in_current_module"))


def test_load_assets_from_current_module():
    assets = load_assets_from_current_module()
    assets = [get_unique_asset_identifier(asset) for asset in assets]
    assert assets == ["asset_in_current_module", AssetKey("source_asset_in_current_module")]
    assert len(assets) == 2


def test_load_assets_from_modules_with_group_name():
    from dagster_tests.asset_defs_tests import asset_package
    from dagster_tests.asset_defs_tests.asset_package import module_with_assets

    assets = load_assets_from_modules(
        [asset_package, module_with_assets], group_name="my_cool_group"
    )
    check_asset_group(assets)

    assets = load_assets_from_package_module(asset_package, group_name="my_cool_group")
    check_asset_group(assets)


def test_respect_existing_groups():
    assets = load_assets_from_current_module()
    assert assets[0].group_names_by_key.get(AssetKey("asset_in_current_module")) == "my_group"

    with pytest.raises(DagsterInvalidDefinitionError):
        load_assets_from_current_module(group_name="yay")


def test_load_assets_with_freshness_policy():
    from dagster_tests.asset_defs_tests import asset_package
    from dagster_tests.asset_defs_tests.asset_package import module_with_assets

    assets = load_assets_from_modules(
        [asset_package, module_with_assets],
        freshness_policy=FreshnessPolicy(maximum_lag_minutes=50),
    )
    check_freshness_policy(assets, FreshnessPolicy(maximum_lag_minutes=50))

    assets = load_assets_from_package_module(
        asset_package, freshness_policy=FreshnessPolicy(maximum_lag_minutes=50)
    )
    check_freshness_policy(assets, FreshnessPolicy(maximum_lag_minutes=50))


def test_load_assets_with_auto_materialize_policy():
    from dagster_tests.asset_defs_tests import asset_package
    from dagster_tests.asset_defs_tests.asset_package import module_with_assets

    assets = load_assets_from_modules(
        [asset_package, module_with_assets], auto_materialize_policy=AutoMaterializePolicy.eager()
    )
    check_auto_materialize_policy(assets, AutoMaterializePolicy.eager())

    assets = load_assets_from_package_module(
        asset_package, auto_materialize_policy=AutoMaterializePolicy.lazy()
    )
    check_auto_materialize_policy(assets, AutoMaterializePolicy.lazy())


@pytest.mark.parametrize(
    "prefix",
    [
        "my_cool_prefix",
        ["foo", "my_cool_prefix"],
        ["foo", "bar", "baz", "my_cool_prefix"],
    ],
)
def test_prefix(prefix):
    from dagster_tests.asset_defs_tests import asset_package
    from dagster_tests.asset_defs_tests.asset_package import module_with_assets

    assets = load_assets_from_modules([asset_package, module_with_assets], key_prefix=prefix)
    assert_assets_have_prefix(prefix, assets)

    assets = load_assets_from_package_module(asset_package, key_prefix=prefix)
    assert_assets_have_prefix(prefix, assets)


def _load_assets_from_module_with_assets(**kwargs):
    from dagster_tests.asset_defs_tests.asset_package import module_with_assets

    return load_assets_from_modules([module_with_assets], **kwargs)


@pytest.mark.parametrize(
    "load_fn",
    [
        _load_assets_from_module_with_assets,
        lambda **kwargs: load_assets_from_package_name(
            "dagster_tests.asset_defs_tests.asset_package", **kwargs
        ),
    ],
)
def test_source_key_prefix(load_fn):
    prefix = ["foo", "my_cool_prefix"]
    assets_without_prefix_sources = load_fn(key_prefix=prefix)
    assert get_source_asset_with_key(assets_without_prefix_sources, AssetKey(["elvis_presley"]))
    assert get_assets_def_with_key(
        assets_without_prefix_sources, AssetKey(["foo", "my_cool_prefix", "chuck_berry"])
    ).dependency_keys == {
        AssetKey(["elvis_presley"]),
        AssetKey(["foo", "my_cool_prefix", "miles_davis"]),
    }

    assets_with_prefix_sources = load_fn(
        key_prefix=prefix, source_key_prefix=["bar", "cooler_prefix"]
    )
    assert get_source_asset_with_key(
        assets_with_prefix_sources, AssetKey(["bar", "cooler_prefix", "elvis_presley"])
    )
    assert get_assets_def_with_key(
        assets_with_prefix_sources, AssetKey(["foo", "my_cool_prefix", "chuck_berry"])
    ).dependency_keys == {
        AssetKey(["bar", "cooler_prefix", "elvis_presley"]),
        AssetKey(["foo", "my_cool_prefix", "miles_davis"]),
    }

    assets_with_str_prefix_sources = load_fn(key_prefix=prefix, source_key_prefix="string_prefix")
    assert get_source_asset_with_key(
        assets_with_str_prefix_sources, AssetKey(["string_prefix", "elvis_presley"])
    )


@pytest.mark.parametrize(
    "load_fn",
    [
        load_assets_from_package_module,
        lambda x, **kwargs: load_assets_from_package_name(x.__name__, **kwargs),
    ],
)
@pytest.mark.parametrize(
    "prefix",
    [
        "my_cool_prefix",
        ["foo", "my_cool_prefix"],
        ["foo", "bar", "baz", "my_cool_prefix"],
    ],
)
def test_load_assets_cacheable(load_fn, prefix):
    """Tests the load-from-module and load-from-package-name functinos with cacheable assets."""
    from dagster_tests.asset_defs_tests import asset_package_with_cacheable

    assets_defs = load_fn(asset_package_with_cacheable)
    assert len(assets_defs) == 3

    assets_defs = load_fn(asset_package_with_cacheable, group_name="my_cool_group")
    assert len(assets_defs) == 3

    for assets_def in assets_defs:
        cacheable_def = cast(CacheableAssetsDefinition, assets_def)
        resolved_asset_defs = cacheable_def.build_definitions(
            cacheable_def.compute_cacheable_data()
        )

        check_asset_group(resolved_asset_defs)

    assets_defs = load_fn(asset_package_with_cacheable, key_prefix=prefix)
    assert len(assets_defs) == 3

    for assets_def in assets_defs:
        cacheable_def = cast(CacheableAssetsDefinition, assets_def)
        resolved_asset_defs = cacheable_def.build_definitions(
            cacheable_def.compute_cacheable_data()
        )

        assert_assets_have_prefix(prefix, resolved_asset_defs)
