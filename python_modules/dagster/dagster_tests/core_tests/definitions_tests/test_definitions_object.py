import warnings

import dagster as dg
import pytest
from dagster import Definitions, schedule
from dagster._core.definitions.job_definition import JobDefinition
from dagster_shared.check.functions import CheckError


def ensure_get_job_def_warns(defs: Definitions, name: str) -> str:
    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        defs.get_job_def(name)
        assert len(w) == 1
    message = str(w[0].message)
    assert message
    return message


def ensure_resolve_job_succeeds(defs: Definitions, name: str) -> None:
    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        job_def = defs.resolve_job_def(name)
        assert len(w) == 0
        assert isinstance(job_def, dg.JobDefinition)
        assert job_def.name == name


def ensure_get_direct_job_def_succeeds(defs: Definitions, original_job_def: JobDefinition) -> None:
    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        job_def = defs.get_job_def(original_job_def.name)
        assert len(w) == 0
        assert job_def is original_job_def


def test_direct_job_def() -> None:
    @dg.op
    def _op(_context): ...

    @dg.job
    def a_job():
        _op()

    defs = dg.Definitions(jobs=[a_job])

    ensure_get_direct_job_def_succeeds(defs, a_job)
    # resolves job anyway til 1.11
    assert defs.has_resolved_repository_def()


def test_resolve_direct_asset_job() -> None:
    @dg.asset
    def _asset(_context): ...

    asset_job = dg.define_asset_job(name="asset_job", selection="*")

    defs = dg.Definitions(jobs=[asset_job])

    ensure_resolve_job_succeeds(defs, "asset_job")
    assert defs.has_resolved_repository_def()


def test_get_direct_asset_job_fails() -> None:
    @dg.asset
    def _asset(_context): ...

    asset_job = dg.define_asset_job(name="asset_job", selection="*")

    defs = dg.Definitions(jobs=[asset_job])

    assert "Found asset job named asset_job" in ensure_get_job_def_warns(defs, "asset_job")
    assert defs.has_resolved_repository_def()


def test_sensor_target_job_resolve_succeeds() -> None:
    @dg.asset
    def _asset(_context): ...

    asset_job = dg.define_asset_job(name="asset_job", selection="*")

    @dg.sensor(target=asset_job)
    def my_sensor(context): ...

    defs = dg.Definitions(sensors=[my_sensor])

    ensure_resolve_job_succeeds(defs, "asset_job")
    assert defs.has_resolved_repository_def()


def test_sensor_target_job_get_fails() -> None:
    @dg.asset
    def _asset(_context): ...

    asset_job = dg.define_asset_job(name="asset_job", selection="*")

    @dg.sensor(target=asset_job)
    def my_sensor(context): ...

    defs = dg.Definitions(sensors=[my_sensor])

    assert "Found job or graph named asset_job" in ensure_get_job_def_warns(defs, "asset_job")
    assert defs.has_resolved_repository_def()


def test_sensor_get_direct_job_succeeds() -> None:
    @dg.op
    def _op(_context): ...

    @dg.job
    def direct_job():
        _op()

    @dg.sensor(target=direct_job)
    def my_sensor(context): ...

    defs = dg.Definitions(sensors=[my_sensor])

    assert "Found job or graph named direct_job" in ensure_get_job_def_warns(defs, direct_job.name)
    assert defs.has_resolved_repository_def()


def test_schedule_target_job_resolve_succeeds() -> None:
    @dg.asset
    def _asset(_context): ...

    asset_job = dg.define_asset_job(name="asset_job", selection="*")

    @schedule(job=asset_job, cron_schedule="* * * * *")
    def my_schedule(context): ...

    defs = dg.Definitions(schedules=[my_schedule])

    ensure_resolve_job_succeeds(defs, "asset_job")
    assert defs.has_resolved_repository_def()


def test_schedule_target_job_get_fails() -> None:
    @dg.asset
    def _asset(_context): ...

    asset_job = dg.define_asset_job(name="asset_job", selection="*")

    @schedule(job=asset_job, cron_schedule="* * * * *")
    def my_schedule(context): ...

    defs = dg.Definitions(schedules=[my_schedule])

    assert "Found job named asset_job" in ensure_get_job_def_warns(defs, "asset_job")
    assert defs.has_resolved_repository_def()


def test_schedule_get_direct_job_succeeds() -> None:
    @dg.op
    def _op(_context): ...

    @dg.job
    def direct_job():
        _op()

    @schedule(job=direct_job, cron_schedule="* * * * *")
    def my_schedule(context): ...

    defs = dg.Definitions(schedules=[my_schedule])

    assert "Found job named direct_job" in ensure_get_job_def_warns(defs, direct_job.name)
    assert defs.has_resolved_repository_def()


def test_get_sensor_def_warns() -> None:
    @dg.sensor(name="my_sensor")
    def my_sensor(context): ...

    defs = dg.Definitions(sensors=[my_sensor])

    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        defs.get_sensor_def("my_sensor")
        assert len(w) == 1
        assert "dagster 1.11" in str(w[0].message)
    assert defs.has_resolved_repository_def()  # this should invert once get_sensor_def does not automatically resolve (2025-06-02 -- schrockn)


def test_get_unresolved_sensor_def_succeeds() -> None:
    @dg.sensor(name="my_sensor")
    def my_sensor(context): ...

    defs = dg.Definitions(sensors=[my_sensor])

    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        assert defs.get_unresolved_sensor_def("my_sensor") is my_sensor
        assert len(w) == 0
    assert not defs.has_resolved_repository_def()


def test_get_schedule_def_warns() -> None:
    @schedule(name="my_schedule", cron_schedule="* * * * *", target="*")
    def my_schedule(context): ...

    defs = dg.Definitions(schedules=[my_schedule])

    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        defs.get_schedule_def("my_schedule")
        assert len(w) == 1
        assert "dagster 1.11" in str(w[0].message)
    assert defs.has_resolved_repository_def()  # this should invert once get_schedule_def does not automatically resolve (2025-06-02 -- schrockn)


def test_get_unresolved_schedule_def_succeeds() -> None:
    @schedule(name="my_schedule", cron_schedule="* * * * *", target="*")
    def my_schedule(context): ...

    defs = dg.Definitions(schedules=[my_schedule])

    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        assert defs.get_unresolved_schedule_def("my_schedule") is my_schedule
        assert len(w) == 0
    assert not defs.has_resolved_repository_def()


def test_resolve_build_schedule_from_partitioned_job_succeeds() -> None:
    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2020-01-01"))
    def asset1(): ...

    asset1_job = dg.define_asset_job("asset1_job", selection=[asset1])
    schedule = dg.build_schedule_from_partitioned_job(asset1_job, name="my_schedule")

    ensure_resolve_job_succeeds(dg.Definitions(assets=[asset1], schedules=[schedule]), "asset1_job")

    defs = dg.Definitions(assets=[asset1], schedules=[schedule])
    with pytest.raises(ValueError, match="ScheduleDefinition with name no_schedule not found"):
        defs.get_unresolved_schedule_def("no_schedule")

    with pytest.raises(ValueError, match="is an UnresolvedPartitionedAssetScheduleDefinition"):
        defs.get_unresolved_schedule_def("my_schedule")

    assert not defs.has_resolved_repository_def()


def test_map_asset_specs_fails() -> None:
    @dg.asset
    def asset1(): ...

    defs = dg.Definitions(assets=[asset1])
    with pytest.raises(
        CheckError,
        match="The selection parameter is no longer supported for map_asset_specs, Please use map_resolved_asset_specs instead",
    ):
        defs.map_asset_specs(func=lambda s: s, selection="something")


def test_get_directly_asset_specs_succeeds() -> None:
    assert dg.Definitions(assets=[dg.AssetSpec("asset1")]).get_all_asset_specs()[
        0
    ].key == dg.AssetKey("asset1")

    @dg.asset
    def asset1(): ...

    defs = dg.Definitions(assets=[asset1])
    assert defs.get_all_asset_specs()[0].key == dg.AssetKey("asset1")
    assert defs.has_resolved_repository_def()

    defs_with_asset_checks = dg.Definitions(asset_checks=[asset1])
    assert defs_with_asset_checks.get_all_asset_specs()[0].key == dg.AssetKey("asset1")
    assert defs_with_asset_checks.has_resolved_repository_def()


def test_get_all_asset_specs_warns() -> None:
    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        dg.Definitions(assets=[dg.AssetSpec("asset1")]).get_all_asset_specs()
        assert len(w) == 1
        assert "get_all_asset_specs" in str(w[0].message)


def test_resolve_all_asset_specs_succeeds() -> None:
    defs = dg.Definitions(assets=[dg.SourceAsset("asset1")])
    assert defs.resolve_all_asset_specs()[0].key == dg.AssetKey("asset1")
    assert defs.has_resolved_repository_def()

    @dg.observable_source_asset
    def asset1(): ...

    assert dg.Definitions(assets=[asset1]).resolve_all_asset_specs()[0].key == dg.AssetKey("asset1")

    @dg.multi_observable_source_asset(specs=[dg.AssetSpec("asset1")])
    def _the_mosa(): ...

    assert dg.Definitions(assets=[_the_mosa]).resolve_all_asset_specs()[0].key == dg.AssetKey(
        "asset1"
    )


def test_get_assets_def() -> None:
    @dg.asset
    def asset1(): ...

    defs = dg.Definitions(assets=[asset1])
    assert defs.get_assets_def("asset1").key == dg.AssetKey("asset1")
    assert not defs.has_resolved_repository_def()

    defs_with_asset_checks = dg.Definitions(asset_checks=[asset1])
    assert defs_with_asset_checks.get_assets_def("asset1").key == dg.AssetKey("asset1")
    assert not defs_with_asset_checks.has_resolved_repository_def()

    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        defs = dg.Definitions(assets=[dg.AssetSpec("asset1")])
        assert defs.get_assets_def("asset1").key == dg.AssetKey("asset1")
        assert len(w) == 1
        assert "Could not find assets_def with key" in str(w[0].message)
        assert defs.has_resolved_repository_def()

    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        defs_with_asset_checks = dg.Definitions(asset_checks=[asset1])
        assert defs_with_asset_checks.resolve_assets_def("asset1").key == dg.AssetKey("asset1")
        assert len(w) == 0
        assert defs_with_asset_checks.has_resolved_repository_def()
