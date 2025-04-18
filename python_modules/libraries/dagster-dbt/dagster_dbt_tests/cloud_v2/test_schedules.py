import pytest
import responses
from dagster import AssetExecutionContext, AssetSelection, define_asset_job
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.test_utils import instance_for_test
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
from dagster_dbt.cloud_v2.schedule_builder import (
    build_schedules_from_dbt_cloud_workspace,
    execute_step_to_args,
)

from dagster_dbt_tests.cloud_v2.conftest import (
    TEST_CRON_SCHEDULE,
    TEST_JOB_EXCLUDE_ARG_VALUE,
    TEST_JOB_INDIRECT_SELECTION_ARG_VALUE,
    TEST_JOB_OTHER_ARGS,
    TEST_JOB_SELECT_ARG_VALUE,
)


def test_schedules_builder(
    workspace: DbtCloudWorkspace,
    cli_invocation_api_mocks: responses.RequestsMock,
) -> None:
    @dbt_cloud_assets(workspace=workspace)
    def my_dbt_cloud_assets(context: AssetExecutionContext, dbt_cloud: DbtCloudWorkspace):
        yield from dbt_cloud.cli(args=["run"], context=context).wait()

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

    materialize_assets = define_asset_job(
        name="materialize_assets",
        selection=AssetSelection.assets(my_dbt_cloud_assets),
    ).resolve(
        asset_graph=AssetGraph.from_assets([my_dbt_cloud_assets]),
        resource_defs={"dbt_cloud": workspace},
    )

    with instance_for_test() as instance:
        result = materialize_assets.execute_in_process(instance=instance)

    assert result.success


@pytest.mark.parametrize(
    [
        "execute_step",
        "expected_command",
        "expected_select",
        "expected_exclude",
        "expected_indirect_selection",
        "expected_other_args",
    ],
    [
        ("dbt run", "run", None, None, None, None),
        ("dbt run --select my_model", "run", "my_model", None, None, None),
        ("dbt run --exclude my_model", "run", None, "my_model", None, None),
        ("dbt run --indirect-selection cautious", "run", None, None, "cautious", None),
        ("dbt run --full-refresh", "run", None, None, None, "--full-refresh"),
        (
            (
                "dbt run --select my_model+ --exclude another_model --full-refresh "
                "--indirect-selection cautious --debug --defer --state path/to/artifacts --fail-fast"
            ),
            "run",
            "my_model+",
            "another_model",
            "cautious",
            "--full-refresh --debug --defer --state path/to/artifacts --fail-fast",
        ),
        ("dbt build", "build", None, None, None, None),
        ("dbt clean", "clean", None, None, None, None),
        ("dbt clone", "clone", None, None, None, None),
        ("dbt compile", "compile", None, None, None, None),
        ("dbt deps", "deps", None, None, None, None),
        ("dbt ls", "ls", None, None, None, None),
    ],
    ids=[
        "basic_command",
        "basic_selection",
        "basic_exclusion",
        "basic_indirect_selection",
        "basic_other_args",
        "complex_command",
        "dbt_build",
        "dbt_clean",
        "dbt_clone",
        "dbt_compile",
        "dbt_deps",
        "dbt_ls",
    ],
)
def test_execute_step_to_args(
    execute_step: str,
    expected_command: str,
    expected_select: str,
    expected_exclude: str,
    expected_indirect_selection: str,
    expected_other_args: str,
) -> None:
    command, select, exclude, indirect_selection, other_args = execute_step_to_args(execute_step)
    assert command == expected_command
    assert select == expected_select
    assert exclude == expected_exclude
    assert indirect_selection == expected_indirect_selection
    assert other_args == expected_other_args
