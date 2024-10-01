import pytest
from dagster import (
    AssetCheckKey,
    AssetCheckSpec,
    AssetDep,
    AssetKey,
    AssetSpec,
    Definitions,
    MaterializeResult,
    ScheduleDefinition,
    SourceAsset,
    asset,
    asset_check,
    define_asset_job,
    materialize,
    multi_asset,
    sensor,
)
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.definitions_class import map_asset_keys


class DefinitionsWithMapAssetMethods(Definitions):
    map_asset_keys = map_asset_keys


def test_map_asset_keys_two_specs_with_dep() -> None:
    mapped_defs = DefinitionsWithMapAssetMethods(
        assets=[AssetSpec("a1"), AssetSpec("a2", deps=[AssetDep("a1")])]
    ).map_asset_keys(lambda spec: spec.key.with_prefix(["prefix"]))
    all_asset_specs = mapped_defs.get_all_asset_specs()
    assert len(all_asset_specs) == 2

    assert all_asset_specs[0].key == AssetKey(["prefix", "a1"])
    assert all_asset_specs[1].key == AssetKey(["prefix", "a2"])
    assert all_asset_specs[1].deps == [AssetDep(["prefix", "a1"])]


def test_map_asset_keys_two_defs_with_dep() -> None:
    @asset
    def a1(): ...

    @asset(deps=[a1])
    def a2(): ...

    mapped_defs = DefinitionsWithMapAssetMethods(assets=[a1, a2]).map_asset_keys(
        lambda spec: spec.key.with_prefix(["prefix"])
    )
    all_asset_specs = mapped_defs.get_all_asset_specs()
    assert len(all_asset_specs) == 2

    mapped_specs_by_key = {spec.key: spec for spec in all_asset_specs}
    assert mapped_specs_by_key.keys() == {AssetKey(["prefix", "a1"]), AssetKey(["prefix", "a2"])}
    assert mapped_specs_by_key[AssetKey(["prefix", "a2"])].deps == [AssetDep(["prefix", "a1"])]

    result = materialize(mapped_defs.assets)
    assert result.success
    assert {
        e.event_specific_data.materialization.asset_key
        for e in result.get_asset_materialization_events()
    } == {AssetKey(["prefix", "a1"]), AssetKey(["prefix", "a2"])}


def test_map_asset_keys_independent_asset_check() -> None:
    @asset_check(asset="a1")
    def asset_check1():
        return AssetCheckResult(passed=True)

    mapped_defs = DefinitionsWithMapAssetMethods(
        assets=[AssetSpec("a1")], asset_checks=[asset_check1]
    ).map_asset_keys(lambda spec: spec.key.with_prefix(["prefix"]))
    all_asset_specs = mapped_defs.get_all_asset_specs()
    assert len(all_asset_specs) == 1
    assert all_asset_specs[0].key == AssetKey(["prefix", "a1"])

    asset_graph = mapped_defs.get_asset_graph()
    with pytest.raises(KeyError):
        asset_graph.get(AssetCheckKey(AssetKey(["a1"]), "asset_check1"))
    assert asset_graph.get(AssetCheckKey(AssetKey(["prefix", "a1"]), "asset_check1"))


def test_map_asset_keys_internal_dep():
    @multi_asset(specs=[AssetSpec("a1"), AssetSpec("a2", deps=[AssetDep("a1")])])
    def assets(context):
        yield MaterializeResult(asset_key=AssetKey(["prefix", "a1"]))
        yield MaterializeResult(asset_key=AssetKey(["prefix", "a2"]))

    mapped_defs = DefinitionsWithMapAssetMethods(assets=[assets]).map_asset_keys(
        lambda spec: spec.key.with_prefix(["prefix"])
    )
    all_asset_specs = mapped_defs.get_all_asset_specs()
    assert len(all_asset_specs) == 2

    mapped_specs_by_key = {spec.key: spec for spec in all_asset_specs}
    assert mapped_specs_by_key.keys() == {AssetKey(["prefix", "a1"]), AssetKey(["prefix", "a2"])}
    assert mapped_specs_by_key[AssetKey(["prefix", "a2"])].deps == [AssetDep(["prefix", "a1"])]

    result = materialize(mapped_defs.assets)
    assert result.success
    assert {
        e.event_specific_data.materialization.asset_key
        for e in result.get_asset_materialization_events()
    } == {AssetKey(["prefix", "a1"]), AssetKey(["prefix", "a2"])}


def test_map_asset_keys_asset_and_check_same_op():
    @asset(check_specs=[AssetCheckSpec(asset="a1", name="c1")])
    def a1(context):
        for ak in context.selected_asset_keys:
            yield MaterializeResult(asset_key=ak)
        for ck in context.selected_asset_check_keys:
            yield AssetCheckResult(asset_key=ck.asset_key, check_name=ck.name, passed=True)

    mapped_defs = DefinitionsWithMapAssetMethods(assets=[a1]).map_asset_keys(
        lambda spec: spec.key.with_prefix(["prefix"])
    )
    all_asset_specs = mapped_defs.get_all_asset_specs()
    assert len(all_asset_specs) == 1
    assert all_asset_specs[0].key == AssetKey(["prefix", "a1"])
    asset_graph = mapped_defs.get_asset_graph()
    check_key = AssetCheckKey(asset_key=AssetKey(["prefix", "a1"]), name="c1")
    assert asset_graph.get(check_key) is not None

    result = materialize(mapped_defs.assets)
    assert result.success
    assert {
        e.event_specific_data.materialization.asset_key
        for e in result.get_asset_materialization_events()
    } == {AssetKey(["prefix", "a1"])}

    assert {e.asset_check_key for e in result.get_asset_check_evaluations()} == {check_key}


def test_map_asset_keys_source_asset():
    mapped_defs = DefinitionsWithMapAssetMethods(
        assets=[SourceAsset("a1", group_name="abc"), AssetSpec("a2", deps=["a1"])]
    ).map_asset_keys(lambda spec: spec.key.with_prefix(["prefix"]))
    all_asset_specs = mapped_defs.get_all_asset_specs()
    assert len(all_asset_specs) == 2

    mapped_specs_by_key = {spec.key: spec for spec in all_asset_specs}
    assert mapped_specs_by_key.keys() == {AssetKey(["prefix", "a1"]), AssetKey(["prefix", "a2"])}
    assert mapped_specs_by_key[AssetKey(["prefix", "a2"])].deps == [AssetDep(["prefix", "a1"])]
    assert mapped_specs_by_key[AssetKey(["prefix", "a1"])].group_name == "abc"


def test_map_asset_keys_job_def():
    @asset
    def asset1(): ...

    job1 = define_asset_job("job1", selection=["asset1"])
    defs = DefinitionsWithMapAssetMethods(assets=[asset1], jobs=[job1])
    mapped_defs = defs.map_asset_keys(lambda x: AssetKey("asset2"))
    result = mapped_defs.get_job_def("job1").execute_in_process()
    assert len(result.get_asset_materialization_events()) == 1


def test_map_asset_keys_job_def_and_schedule():
    @asset
    def asset1(): ...

    job1 = define_asset_job("job1", selection=["asset1"])
    schedule1 = ScheduleDefinition(job=job1, cron_schedule="@daily")
    defs = DefinitionsWithMapAssetMethods(assets=[asset1], jobs=[job1], schedules=[schedule1])
    mapped_defs = defs.map_asset_keys(lambda x: AssetKey("asset2"))
    result = mapped_defs.get_job_def("job1").execute_in_process()
    assert len(result.get_asset_materialization_events()) == 1


def test_map_asset_keys_job_def_inside_schedule():
    @asset
    def asset1(): ...

    job1 = define_asset_job("job1", selection=["asset1"])
    schedule1 = ScheduleDefinition(job=job1, cron_schedule="@daily")
    defs = DefinitionsWithMapAssetMethods(assets=[asset1], schedules=[schedule1])
    mapped_defs = defs.map_asset_keys(lambda x: AssetKey("asset2"))
    result = mapped_defs.get_job_def("job1").execute_in_process()
    assert len(result.get_asset_materialization_events()) == 1


def test_map_asset_keys_job_def_and_sensor():
    @asset
    def asset1(): ...

    job1 = define_asset_job("job1", selection=["asset1"])

    @sensor(job=job1)
    def sensor1():
        return True

    defs = DefinitionsWithMapAssetMethods(assets=[asset1], jobs=[job1], sensors=[sensor1])
    mapped_defs = defs.map_asset_keys(lambda x: AssetKey("asset2"))
    result = mapped_defs.get_job_def("job1").execute_in_process()
    assert len(result.get_asset_materialization_events()) == 1


def test_map_asset_keys_job_def_inside_sensor():
    @asset
    def asset1(): ...

    job1 = define_asset_job("job1", selection=["asset1"])

    @sensor(job=job1)
    def sensor1():
        return True

    defs = DefinitionsWithMapAssetMethods(assets=[asset1], sensors=[sensor1])
    mapped_defs = defs.map_asset_keys(lambda x: AssetKey("asset2"))
    result = mapped_defs.get_job_def("job1").execute_in_process()
    assert len(result.get_asset_materialization_events()) == 1
