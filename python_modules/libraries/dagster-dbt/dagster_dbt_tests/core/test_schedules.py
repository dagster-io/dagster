from typing import Any, Dict, Mapping, Optional, Sequence, cast

import pytest
from dagster import DefaultScheduleStatus, RunConfig
from dagster._core.definitions.asset_selection import AndAssetSelection
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster_dbt import DbtManifestAssetSelection, build_schedule_from_dbt_selection, dbt_assets


@pytest.mark.parametrize(
    [
        "job_name",
        "cron_schedule",
        "dbt_select",
        "dbt_exclude",
        "schedule_name",
        "tags",
        "config",
        "execution_timezone",
        "default_status",
    ],
    [
        (
            "test_job",
            "0 0 * * *",
            "fqn:*",
            None,
            None,
            None,
            None,
            None,
            DefaultScheduleStatus.STOPPED,
        ),
        (
            "test_job",
            "0 * * * *",
            "fqn:*",
            "fqn:staging.*",
            "my_custom_schedule",
            {"my": "tag"},
            RunConfig(ops={"my_op": {"config": "value"}}),
            "America/Vancouver",
            DefaultScheduleStatus.RUNNING,
        ),
    ],
)
def test_dbt_build_schedule(
    test_jaffle_shop_manifest: dict[str, Any],
    job_name: str,
    cron_schedule: str,
    dbt_select: str,
    dbt_exclude: Optional[str],
    schedule_name: Optional[str],
    tags: Optional[Mapping[str, str]],
    config: Optional[RunConfig],
    execution_timezone: Optional[str],
    default_status: DefaultScheduleStatus,
) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def my_dbt_assets(): ...

    test_daily_schedule = build_schedule_from_dbt_selection(
        [my_dbt_assets],
        job_name=job_name,
        cron_schedule=cron_schedule,
        dbt_select=dbt_select,
        schedule_name=schedule_name,
        dbt_exclude=dbt_exclude,
        tags=tags,
        config=config,
        execution_timezone=execution_timezone,
        default_status=default_status,
    )

    assert test_daily_schedule.name == schedule_name or f"{job_name}_schedule"
    assert test_daily_schedule.job.name == job_name
    assert test_daily_schedule.execution_timezone == execution_timezone
    assert test_daily_schedule.default_status == default_status

    job = test_daily_schedule.job

    assert isinstance(job, UnresolvedAssetJobDefinition)
    assert job.tags == (tags or {})
    assert job.config == (config.to_config_dict() if config else None)

    assert isinstance(job.selection, AndAssetSelection)
    assert len(job.selection.operands) == 2

    [dbt_assets_selection, job_selection] = cast(
        Sequence[DbtManifestAssetSelection], job.selection.operands
    )
    assert dbt_assets_selection.select == "fqn:*"
    assert dbt_assets_selection.exclude == ""
    assert job_selection.select == (dbt_select or "fqn:*")
    assert job_selection.exclude == (dbt_exclude or "")
