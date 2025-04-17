import responses
from dagster_dbt.asset_utils import (
    DAGSTER_DBT_INDIRECT_SELECTION_METADATA_KEY,
    DAGSTER_DBT_OTHER_ARGS_METADATA_KEY,
)
from dagster_dbt.cloud_v2.asset_decorator import dbt_cloud_assets
from dagster_dbt.cloud_v2.resources import (
    DBT_CLOUD_DEFAULT_EXCLUDE,
    DBT_CLOUD_DEFAULT_SELECT,
    DbtCloudWorkspace,
)
from dagster_dbt.cloud_v2.schedule_builder import build_schedules_from_dbt_cloud_workspace

from dagster_dbt_tests.cloud_v2.conftest import (
    TEST_CRON_SCHEDULE,
    TEST_JOB_EXCLUDE_ARG_VALUE,
    TEST_JOB_INDIRECT_SELECTION_ARG_VALUE,
    TEST_JOB_OTHER_ARGS,
    TEST_JOB_SELECT_ARG_VALUE,
)


def test_schedules_builder(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    @dbt_cloud_assets(workspace=workspace)
    def my_dbt_cloud_assets(): ...

    schedules = build_schedules_from_dbt_cloud_workspace([my_dbt_cloud_assets], workspace=workspace)

    assert len(schedules) == 1

    schedule = next(iter(schedules))
    assert schedule.cron_schedule == TEST_CRON_SCHEDULE

    job = schedule.job
    assert DAGSTER_DBT_INDIRECT_SELECTION_METADATA_KEY in job.tags
    assert (
        job.tags[DAGSTER_DBT_INDIRECT_SELECTION_METADATA_KEY]
        == TEST_JOB_INDIRECT_SELECTION_ARG_VALUE
    )
    assert DAGSTER_DBT_OTHER_ARGS_METADATA_KEY in job.tags
    assert job.tags[DAGSTER_DBT_OTHER_ARGS_METADATA_KEY] == TEST_JOB_OTHER_ARGS

    operands_iter = iter(job.selection.operands)
    asset_defs_selection = next(operands_iter)
    job_def_selection = next(operands_iter)

    assert asset_defs_selection.select == DBT_CLOUD_DEFAULT_SELECT
    assert asset_defs_selection.exclude == DBT_CLOUD_DEFAULT_EXCLUDE

    assert job_def_selection.select == TEST_JOB_SELECT_ARG_VALUE
    assert job_def_selection.exclude == TEST_JOB_EXCLUDE_ARG_VALUE
