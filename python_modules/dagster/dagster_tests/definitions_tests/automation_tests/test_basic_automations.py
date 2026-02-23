from collections.abc import Sequence
from typing import TYPE_CHECKING

import dagster as dg
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.schedule_decorator import schedule
from dagster._core.definitions.target import _make_anonymous_asset_job_name

if TYPE_CHECKING:
    from dagster._core.definitions.unresolved_asset_job_definition import (
        UnresolvedAssetJobDefinition,
    )


def make_automations_aware_definitions(
    schedules: Sequence[dg.ScheduleDefinition] | None = None,
    sensors: Sequence[dg.SensorDefinition] | None = None,
):
    job_defs: list[dg.JobDefinition | UnresolvedAssetJobDefinition] = []
    assets_defs: list[dg.AssetsDefinition | dg.SourceAsset] = []
    for schedule_def in schedules or []:
        job_defs.append(schedule_def.target.job_def)
        assets_defs.extend(schedule_def.target.assets_defs)

    for sensor_def in sensors or []:
        for target in sensor_def.targets:
            job_defs.append(target.job_def)
            assets_defs.extend(target.assets_defs)

    return dg.Definitions(schedules=schedules, sensors=sensors, assets=assets_defs)


def test_basic_schedule_single_asset() -> None:
    @dg.asset
    def my_asset() -> None: ...

    schedule = dg.ScheduleDefinition(name="a_schedule", cron_schedule="* * * * *", target=my_asset)

    defs = make_automations_aware_definitions([schedule])

    assert isinstance(defs, dg.Definitions)

    assert isinstance(
        defs.resolve_job_def(_make_anonymous_asset_job_name(schedule.name)), dg.JobDefinition
    )
    assert isinstance(defs.resolve_assets_def("my_asset"), dg.AssetsDefinition)


def test_basic_schedule_multiple_assets() -> None:
    @dg.asset
    def asset_one() -> None: ...

    @dg.asset(deps=[asset_one])
    def asset_two() -> None: ...

    schedule = dg.ScheduleDefinition(
        name="a_schedule", cron_schedule="* * * * *", target=[asset_one, asset_two]
    )

    defs = make_automations_aware_definitions([schedule])

    assert isinstance(defs, dg.Definitions)

    assert isinstance(
        defs.resolve_job_def(_make_anonymous_asset_job_name(schedule.name)), dg.JobDefinition
    )
    assert isinstance(defs.resolve_assets_def("asset_one"), dg.AssetsDefinition)
    assert isinstance(defs.resolve_assets_def("asset_two"), dg.AssetsDefinition)
    assert not defs.resolve_asset_graph().has(AssetKey.from_coercible("slkjdfklsjdfl"))


def test_decorator_schedule() -> None:
    @dg.asset
    def my_asset() -> None: ...

    @schedule(cron_schedule="* * * * *", target=my_asset)
    def a_schedule(_) -> dict:
        return {}

    defs = make_automations_aware_definitions(schedules=[a_schedule])
    assert isinstance(defs.resolve_schedule_def("a_schedule"), dg.ScheduleDefinition)


def test_legacy_job() -> None:
    @dg.op
    def an_op() -> None: ...
    @dg.job
    def a_job() -> None:
        an_op()

    schedule = dg.ScheduleDefinition(name="a_schedule", cron_schedule="* * * * *", target=a_job)

    defs = make_automations_aware_definitions([schedule])

    assert isinstance(defs, dg.Definitions)

    assert isinstance(defs.resolve_job_def("a_job"), dg.JobDefinition)


def test_basic_sensor_definition() -> None:
    @dg.asset
    def my_asset() -> None: ...

    defs = make_automations_aware_definitions(
        sensors=[
            dg.SensorDefinition(
                name="a_sensor",
                target=my_asset,
                evaluation_fn=lambda _: None,
            )
        ]
    )
    assert isinstance(defs, dg.Definitions)
    assert isinstance(defs.resolve_sensor_def("a_sensor"), dg.SensorDefinition)


def test_sensor_decorator() -> None:
    @dg.asset
    def my_asset() -> None: ...

    @dg.sensor(target=my_asset, name="a_sensor")
    def a_sensor() -> None: ...

    defs = make_automations_aware_definitions(sensors=[a_sensor])
    assert isinstance(defs.resolve_sensor_def("a_sensor"), dg.SensorDefinition)
