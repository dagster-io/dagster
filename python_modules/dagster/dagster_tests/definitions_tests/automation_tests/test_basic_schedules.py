from typing import Sequence

from dagster import ScheduleDefinition, asset, job, op
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.schedule_definition import AutomationTarget, make_syntetic_job_name


def make_automations_aware_definitions(schedules: Sequence[ScheduleDefinition]):
    job_defs = []
    assets_defs = []
    for schedule_def in schedules:
        if isinstance(schedule_def.automation_target, AutomationTarget):
            job_defs.append(schedule_def.automation_target.target_executable)
            assets_defs.extend(schedule_def.automation_target.passed_assets_defs)

    return Definitions(schedules=schedules, assets=assets_defs)


def test_basic_schedule_single_asset() -> None:
    @asset
    def my_asset() -> None: ...

    schedule = ScheduleDefinition(name="a_schedule", cron_schedule="* * * * *", target=my_asset)

    defs = make_automations_aware_definitions([schedule])

    assert isinstance(defs, Definitions)

    assert isinstance(defs.get_job_def(make_syntetic_job_name(schedule.name)), JobDefinition)
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

    assert isinstance(defs.get_job_def(make_syntetic_job_name(schedule.name)), JobDefinition)
    assert isinstance(defs.get_assets_def("asset_one"), AssetsDefinition)
    assert isinstance(defs.get_assets_def("asset_two"), AssetsDefinition)
    assert not defs.get_asset_graph().has(AssetKey.from_coercible("slkjdfklsjdfl"))


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
