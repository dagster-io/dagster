import json
from pathlib import Path
from typing import Mapping, Optional

import pytest
from dagster import RunConfig
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster_dbt import DbtManifestAssetSelection, build_schedule_from_dbt_selection, dbt_assets

manifest_path = Path(__file__).joinpath("..", "..", "sample_manifest.json").resolve()
with open(manifest_path, "r") as f:
    manifest = json.load(f)


@pytest.mark.parametrize(
    [
        "job_name",
        "cron_schedule",
        "dbt_select",
        "dbt_exclude",
        "tags",
        "config",
        "execution_timezone",
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
        ),
        (
            "test_job",
            "0 * * * *",
            "fqn:*",
            "fqn:staging.*",
            {"my": "tag"},
            RunConfig(ops={"my_op": {"config": "value"}}),
            "America/Vancouver",
        ),
    ],
)
def test_dbt_build_schedule(
    job_name: str,
    cron_schedule: str,
    dbt_select: str,
    dbt_exclude: Optional[str],
    tags: Optional[Mapping[str, str]],
    config: Optional[RunConfig],
    execution_timezone: Optional[str],
) -> None:
    @dbt_assets(manifest=manifest)
    def my_dbt_assets():
        ...

    test_daily_schedule = build_schedule_from_dbt_selection(
        [my_dbt_assets],
        job_name=job_name,
        cron_schedule=cron_schedule,
        dbt_select=dbt_select,
        dbt_exclude=dbt_exclude,
        tags=tags,
        config=config,
        execution_timezone=execution_timezone,
    )

    assert test_daily_schedule.name == f"{job_name}_schedule"
    assert test_daily_schedule.job.name == job_name
    assert test_daily_schedule.execution_timezone == execution_timezone

    job = test_daily_schedule.job

    assert isinstance(job, UnresolvedAssetJobDefinition)
    assert isinstance(job.selection, DbtManifestAssetSelection)
    assert job.selection.select == (dbt_select or "fqn:*")
    assert job.selection.exclude == (dbt_exclude or "")
    assert job.tags == (tags or {})
    assert job.config == (config.to_config_dict() if config else None)
