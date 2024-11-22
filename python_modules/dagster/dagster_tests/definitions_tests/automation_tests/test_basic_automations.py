from typing import TYPE_CHECKING, List, Optional, Sequence, Union

from dagster import ScheduleDefinition, asset, job, op, sensor
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.schedule_decorator import schedule
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.target import _make_anonymous_asset_job_name

if TYPE_CHECKING:
    from dagster._core.definitions.source_asset import SourceAsset
    from dagster._core.definitions.unresolved_asset_job_definition import (
        UnresolvedAssetJobDefinition,
    )


def make_automations_aware_definitions(
    schedules: Optional[Sequence[ScheduleDefinition]] = None,
    sensors: Optional[Sequence[SensorDefinition]] = None,
):
    job_defs: list[Union[JobDefinition, UnresolvedAssetJobDefinition]] = []
    assets_defs: list[Union[AssetsDefinition, SourceAsset]] = []
    for schedule_def in schedules or []:
        job_defs.append(schedule_def.target.job_def)
        assets_defs.extend(schedule_def.target.assets_defs)

    for sensor_def in sensors or []:
        for target in sensor_def.targets:
            job_defs.append(target.job_def)
            assets_defs.extend(target.assets_defs)

    return Definitions(schedules=schedules, sensors=sensors, assets=assets_defs)


def test_basic_schedule_single_asset() -> None:
    @asset
    def my_asset() -> None: ...

    schedule = ScheduleDefinition(name="a_schedule", cron_schedule="* * * * *", target=my_asset)

    defs = make_automations_aware_definitions([schedule])

    assert isinstance(defs, Definitions)

    assert isinstance(
        defs.get_job_def(_make_anonymous_asset_job_name(schedule.name)), JobDefinition
    )
    assert isinstance(defs.get_assets_def("my_asset"), AssetsDefinition)


def test_basic_schedule_multiple_assets() -> None:
    @asset
    def asset_one() -> None: ...

    @asset(deps=[asset_one])
    def asset_two() -> None: ...

    schedule = ScheduleDefinition(
        name="a_schedule", cron_schedule="* * * * *", target=[asset_one, asset_two]
    )

    defs = make_automations_aware_definitions([schedule])

    assert isinstance(defs, Definitions)

    assert isinstance(
        defs.get_job_def(_make_anonymous_asset_job_name(schedule.name)), JobDefinition
    )
    assert isinstance(defs.get_assets_def("asset_one"), AssetsDefinition)
    assert isinstance(defs.get_assets_def("asset_two"), AssetsDefinition)
    assert not defs.get_asset_graph().has(AssetKey.from_coercible("slkjdfklsjdfl"))


def test_decorator_schedule() -> None:
    @asset
    def my_asset() -> None: ...

    @schedule(cron_schedule="* * * * *", target=my_asset)
    def a_schedule(_) -> dict:
        return {}

    defs = make_automations_aware_definitions(schedules=[a_schedule])
    assert isinstance(defs.get_schedule_def("a_schedule"), ScheduleDefinition)


def test_legacy_job() -> None:
    @op
    def an_op() -> None: ...
    @job
    def a_job() -> None:
        an_op()

    schedule = ScheduleDefinition(name="a_schedule", cron_schedule="* * * * *", target=a_job)

    defs = make_automations_aware_definitions([schedule])

    assert isinstance(defs, Definitions)

    assert isinstance(defs.get_job_def("a_job"), JobDefinition)


def test_basic_sensor_definition() -> None:
    @asset
    def my_asset() -> None: ...

    defs = make_automations_aware_definitions(
        sensors=[
            SensorDefinition(
                name="a_sensor",
                target=my_asset,
                evaluation_fn=lambda _: ...,
            )
        ]
    )
    assert isinstance(defs, Definitions)
    assert isinstance(defs.get_sensor_def("a_sensor"), SensorDefinition)


def test_sensor_decorator() -> None:
    @asset
    def my_asset() -> None: ...

    @sensor(target=my_asset, name="a_sensor")
    def a_sensor() -> None: ...

    defs = make_automations_aware_definitions(sensors=[a_sensor])
    assert isinstance(defs.get_sensor_def("a_sensor"), SensorDefinition)
