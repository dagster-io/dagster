import warnings

import pytest
from dagster import (
    DailyPartitionsDefinition,
    Definitions,
    asset,
    build_schedule_from_partitioned_job,
    define_asset_job,
    job,
    op,
    schedule,
    sensor,
)
from dagster._core.definitions.job_definition import JobDefinition


def ensure_get_job_def_warns(defs: Definitions, name: str) -> None:
    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        defs.get_job_def(name)
        assert len(w) == 1
        assert "require a call to resolve_job_def" in str(w[0].message)


def ensure_resolve_job_succeeds(defs: Definitions, name: str) -> None:
    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        job_def = defs.resolve_job_def(name)
        assert len(w) == 0
        assert isinstance(job_def, JobDefinition)
        assert job_def.name == name


def ensure_get_direct_job_def_succeeds(defs: Definitions, original_job_def: JobDefinition) -> None:
    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        job_def = defs.get_job_def(original_job_def.name)
        assert len(w) == 0
        assert job_def is original_job_def


def test_direct_job_def() -> None:
    @op
    def _op(_context): ...

    @job
    def a_job():
        _op()

    defs = Definitions(jobs=[a_job])

    ensure_get_direct_job_def_succeeds(defs, a_job)


def test_resolve_direct_asset_job() -> None:
    @asset
    def _asset(_context): ...

    asset_job = define_asset_job(name="asset_job", selection="*")

    defs = Definitions(jobs=[asset_job])

    ensure_resolve_job_succeeds(defs, "asset_job")


def test_get_direct_asset_job_fails() -> None:
    @asset
    def _asset(_context): ...

    asset_job = define_asset_job(name="asset_job", selection="*")

    defs = Definitions(jobs=[asset_job])

    ensure_get_job_def_warns(defs, "asset_job")


def test_sensor_target_job_resolve_succeeds() -> None:
    @asset
    def _asset(_context): ...

    asset_job = define_asset_job(name="asset_job", selection="*")

    @sensor(target=asset_job)
    def my_sensor(context): ...

    defs = Definitions(sensors=[my_sensor])

    ensure_resolve_job_succeeds(defs, "asset_job")


def test_sensor_target_job_get_fails() -> None:
    @asset
    def _asset(_context): ...

    asset_job = define_asset_job(name="asset_job", selection="*")

    @sensor(target=asset_job)
    def my_sensor(context): ...

    defs = Definitions(sensors=[my_sensor])

    ensure_get_job_def_warns(defs, "asset_job")


def test_sensor_get_direct_job_succeeds() -> None:
    @op
    def _op(_context): ...

    @job
    def direct_job():
        _op()

    @sensor(target=direct_job)
    def my_sensor(context): ...

    defs = Definitions(sensors=[my_sensor])

    ensure_get_direct_job_def_succeeds(defs, direct_job)


def test_schedule_target_job_resolve_succeeds() -> None:
    @asset
    def _asset(_context): ...

    asset_job = define_asset_job(name="asset_job", selection="*")

    @schedule(job=asset_job, cron_schedule="* * * * *")
    def my_schedule(context): ...

    defs = Definitions(schedules=[my_schedule])

    ensure_resolve_job_succeeds(defs, "asset_job")


def test_schedule_target_job_get_fails() -> None:
    @asset
    def _asset(_context): ...

    asset_job = define_asset_job(name="asset_job", selection="*")

    @schedule(job=asset_job, cron_schedule="* * * * *")
    def my_schedule(context): ...

    defs = Definitions(schedules=[my_schedule])

    ensure_get_job_def_warns(defs, "asset_job")


def test_schedule_get_direct_job_succeeds() -> None:
    @op
    def _op(_context): ...

    @job
    def direct_job():
        _op()

    @schedule(job=direct_job, cron_schedule="* * * * *")
    def my_schedule(context): ...

    defs = Definitions(schedules=[my_schedule])

    ensure_get_direct_job_def_succeeds(defs, direct_job)


def test_get_sensor_def_warns() -> None:
    @sensor(name="my_sensor")
    def my_sensor(context): ...

    defs = Definitions(sensors=[my_sensor])

    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        defs.get_sensor_def("my_sensor")
        assert len(w) == 1
        assert "dagster 1.11" in str(w[0].message)


def test_get_unresolved_sensor_def_succeeds() -> None:
    @sensor(name="my_sensor")
    def my_sensor(context): ...

    defs = Definitions(sensors=[my_sensor])

    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        assert defs.get_unresolved_sensor_def("my_sensor") is my_sensor
        assert len(w) == 0


def test_get_schedule_def_warns() -> None:
    @schedule(name="my_schedule", cron_schedule="* * * * *", target="*")
    def my_schedule(context): ...

    defs = Definitions(schedules=[my_schedule])

    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        defs.get_schedule_def("my_schedule")
        assert len(w) == 1
        assert "dagster 1.11" in str(w[0].message)


def test_get_unresolved_schedule_def_succeeds() -> None:
    @schedule(name="my_schedule", cron_schedule="* * * * *", target="*")
    def my_schedule(context): ...

    defs = Definitions(schedules=[my_schedule])

    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        assert defs.get_unresolved_schedule_def("my_schedule") is my_schedule
        assert len(w) == 0


def test_resolve_build_schedule_from_partitioned_job_succeeds() -> None:
    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"))
    def asset1(): ...

    asset1_job = define_asset_job("asset1_job", selection=[asset1])
    schedule = build_schedule_from_partitioned_job(asset1_job, name="my_schedule")

    ensure_resolve_job_succeeds(Definitions(assets=[asset1], schedules=[schedule]), "asset1_job")

    defs = Definitions(assets=[asset1], schedules=[schedule])
    with pytest.raises(ValueError, match="ScheduleDefinition with name no_schedule not found"):
        defs.get_unresolved_schedule_def("no_schedule")

    with pytest.raises(ValueError, match="is an UnresolvedPartitionedAssetScheduleDefinition"):
        defs.get_unresolved_schedule_def("my_schedule")
