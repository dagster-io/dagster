import pytest
from dagster import (
    AssetCheckKey,
    AssetCheckSpec,
    AssetDep,
    AssetKey,
    AssetsDefinition,
    AssetSpec,
    Definitions,
    MaterializeResult,
    SourceAsset,
    asset,
    asset_check,
    materialize,
    multi_asset,
)
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.errors import DagsterInvalidDefinitionError


def test_single_basic_asset() -> None:
    @asset
    def asset1():
        pass

    mapped_defs = Definitions(assets=[asset1]).map_asset_specs(
        lambda spec: spec._replace(group_name="yolo")
    )
    all_asset_specs = mapped_defs.get_all_asset_specs()
    assert len(all_asset_specs) == 1
    assert all_asset_specs[0].group_name == "yolo"
    assert all_asset_specs[0].key == asset1.key
    assert len(mapped_defs.assets) == 1
    assert isinstance(mapped_defs.assets[0], AssetsDefinition)


def test_a_couple_specs() -> None:
    mapped_defs = Definitions(assets=[AssetSpec("a1"), AssetSpec("a2")]).map_asset_specs(
        lambda spec: spec._replace(group_name="yolo")
    )
    all_asset_specs = mapped_defs.get_all_asset_specs()
    assert len(all_asset_specs) == 2

    assert all_asset_specs[0].group_name == "yolo"
    assert all_asset_specs[0].key == AssetKey("a1")
    assert all_asset_specs[1].group_name == "yolo"
    assert all_asset_specs[1].key == AssetKey("a2")

    assert len(mapped_defs.assets) == 2


def test_two_specs_with_dep() -> None:
    mapped_defs = Definitions(
        assets=[AssetSpec("a1"), AssetSpec("a2", deps=[AssetDep("a1")])]
    ).map_asset_specs(lambda spec: spec._replace(key=spec.key.with_prefix(["prefix"])))
    all_asset_specs = mapped_defs.get_all_asset_specs()
    assert len(all_asset_specs) == 2

    assert all_asset_specs[0].key == AssetKey(["prefix", "a1"])
    assert all_asset_specs[1].key == AssetKey(["prefix", "a2"])
    assert all_asset_specs[1].deps == [AssetDep(["prefix", "a1"])]

    assert len(mapped_defs.assets) == 2


def test_two_defs_with_dep() -> None:
    @asset
    def a1(): ...

    @asset(deps=[a1])
    def a2(): ...

    mapped_defs = Definitions(assets=[a1, a2]).map_asset_specs(
        lambda spec: spec._replace(key=spec.key.with_prefix(["prefix"]))
    )
    all_asset_specs = mapped_defs.get_all_asset_specs()
    assert len(all_asset_specs) == 2

    mapped_specs_by_key = {spec.key: spec for spec in all_asset_specs}
    assert mapped_specs_by_key.keys() == {AssetKey(["prefix", "a1"]), AssetKey(["prefix", "a2"])}
    assert mapped_specs_by_key[AssetKey(["prefix", "a2"])].deps == [AssetDep(["prefix", "a1"])]

    assert len(mapped_defs.assets) == 2
    result = materialize(mapped_defs.assets)
    assert result.success
    assert {
        e.event_specific_data.materialization.asset_key
        for e in result.get_asset_materialization_events()
    } == {AssetKey(["prefix", "a1"]), AssetKey(["prefix", "a2"])}


def test_independent_asset_check() -> None:
    @asset_check(asset="a1")
    def asset_check1():
        return AssetCheckResult(passed=True)

    mapped_defs = Definitions(
        assets=[AssetSpec("a1")], asset_checks=[asset_check1]
    ).map_asset_specs(lambda spec: spec._replace(key=spec.key.with_prefix(["prefix"])))
    all_asset_specs = mapped_defs.get_all_asset_specs()
    assert len(all_asset_specs) == 1

    assert all_asset_specs[0].key == AssetKey(["prefix", "a1"])
    assert len(mapped_defs.assets) == 1
    assert len(mapped_defs.asset_checks) == 1
    assert len(mapped_defs.asset_checks[0].check_specs) == 1
    assert next(iter(mapped_defs.asset_checks[0].check_specs)).asset_key == AssetKey(
        ["prefix", "a1"]
    )


def test_internal_dep():
    @multi_asset(specs=[AssetSpec("a1"), AssetSpec("a2", deps=[AssetDep("a1")])])
    def assets(context):
        yield MaterializeResult(asset_key=AssetKey(["prefix", "a1"]))
        yield MaterializeResult(asset_key=AssetKey(["prefix", "a2"]))

    mapped_defs = Definitions(assets=[assets]).map_asset_specs(
        lambda spec: spec._replace(key=spec.key.with_prefix(["prefix"]))
    )
    all_asset_specs = mapped_defs.get_all_asset_specs()
    assert len(all_asset_specs) == 2

    mapped_specs_by_key = {spec.key: spec for spec in all_asset_specs}
    assert mapped_specs_by_key.keys() == {AssetKey(["prefix", "a1"]), AssetKey(["prefix", "a2"])}
    assert mapped_specs_by_key[AssetKey(["prefix", "a2"])].deps == [AssetDep(["prefix", "a1"])]

    assert len(mapped_defs.assets) == 1
    result = materialize(mapped_defs.assets)
    assert result.success
    assert {
        e.event_specific_data.materialization.asset_key
        for e in result.get_asset_materialization_events()
    } == {AssetKey(["prefix", "a1"]), AssetKey(["prefix", "a2"])}


def test_asset_and_check_same_op():
    @asset(check_specs=[AssetCheckSpec(asset="a1", name="c1")])
    def a1(context):
        for ak in context.selected_asset_keys:
            yield MaterializeResult(asset_key=ak)
        for ck in context.selected_asset_check_keys:
            yield AssetCheckResult(asset_key=ck.asset_key, check_name=ck.name, passed=True)

    mapped_defs = Definitions(assets=[a1]).map_asset_specs(
        lambda spec: spec._replace(key=spec.key.with_prefix(["prefix"]))
    )
    all_asset_specs = mapped_defs.get_all_asset_specs()
    assert len(all_asset_specs) == 1
    assert all_asset_specs[0].key == AssetKey(["prefix", "a1"])
    asset_graph = mapped_defs.get_asset_graph()
    check_key = AssetCheckKey(asset_key=AssetKey(["prefix", "a1"]), name="c1")
    assert asset_graph.get(check_key) is not None

    assert len(mapped_defs.assets) == 1
    result = materialize(mapped_defs.assets)
    assert result.success
    assert {
        e.event_specific_data.materialization.asset_key
        for e in result.get_asset_materialization_events()
    } == {AssetKey(["prefix", "a1"])}

    assert {e.asset_check_key for e in result.get_asset_check_evaluations()} == {check_key}


def test_source_asset():
    mapped_defs = Definitions(
        assets=[SourceAsset("a1", group_name="abc"), AssetSpec("a2", deps=["a1"])]
    ).map_asset_specs(lambda spec: spec._replace(key=spec.key.with_prefix(["prefix"])))
    all_asset_specs = mapped_defs.get_all_asset_specs()
    assert len(all_asset_specs) == 2

    mapped_specs_by_key = {spec.key: spec for spec in all_asset_specs}
    assert mapped_specs_by_key.keys() == {AssetKey(["prefix", "a1"]), AssetKey(["prefix", "a2"])}
    assert mapped_specs_by_key[AssetKey(["prefix", "a2"])].deps == [AssetDep(["prefix", "a1"])]
    assert mapped_specs_by_key[AssetKey(["prefix", "a1"])].group_name == "abc"

    assert len(mapped_defs.assets) == 2
    assert any(
        isinstance(el, SourceAsset) and el.key == AssetKey(["prefix", "a1"])
        for el in mapped_defs.assets
    )


def test_cacheable_assets_definition():
    class FooCacheableAssetsDefinition(CacheableAssetsDefinition):
        def compute_cacheable_data(self):
            return []

        def build_definitions(self, *_args, **_kwargs):
            return []

    defs = Definitions(assets=[FooCacheableAssetsDefinition("abc")])

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Can't use map_asset_specs on Definitions objects that contain CacheableAssetsDefinitions.",
    ):
        defs.map_asset_specs(lambda spec: spec._replace(key=spec.key.with_prefix(["prefix"])))
