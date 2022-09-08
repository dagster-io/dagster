import pytest
from dagster_dbt import dbt_build_op, dbt_cli_resource, dbt_run_op, dbt_seed_op, dbt_test_op

from dagster import build_op_context, job


def test_seed_op(conn_string, test_project_dir, dbt_config_dir):  # pylint: disable=unused-argument

    dbt_resource = dbt_cli_resource.configured(
        {"project_dir": test_project_dir, "profiles_dir": dbt_config_dir}
    )
    dbt_result = dbt_seed_op(build_op_context(resources={"dbt": dbt_resource}))
    assert len(dbt_result.result["results"]) == 1


@pytest.mark.parametrize("yield_asset_events", [True, False])
def test_build_op(
    dbt_seed, conn_string, test_project_dir, dbt_config_dir, yield_asset_events
):  # pylint: disable=unused-argument

    dbt_resource = dbt_cli_resource.configured(
        {"project_dir": test_project_dir, "profiles_dir": dbt_config_dir}
    )
    if not yield_asset_events:
        test_op = dbt_build_op.configured({"yield_asset_events": False}, name="foo")
    else:
        test_op = dbt_build_op
    dbt_results = list(test_op(build_op_context(resources={"dbt": dbt_resource})))

    if yield_asset_events:
        # 1 Output, 6 Materializations, 17 Observations
        assert len(dbt_results) == 1 + 6 + 17
    else:
        # 1 Output
        assert len(dbt_results) == 1

    # 6 Materializations, 17 Observations
    assert len(dbt_results[-1].value.result["results"]) == 6 + 17


def test_run_op(
    dbt_seed, conn_string, test_project_dir, dbt_config_dir
):  # pylint: disable=unused-argument

    dbt_resource = dbt_cli_resource.configured(
        {"project_dir": test_project_dir, "profiles_dir": dbt_config_dir}
    )
    dbt_results = list(dbt_run_op(build_op_context(resources={"dbt": dbt_resource})))

    # includes asset materializations
    assert len(dbt_results) == 5

    assert len(dbt_results[-1].value.result["results"]) == 4


def test_run_op_with_select(
    dbt_build, conn_string, test_project_dir, dbt_config_dir
):  # pylint: disable=unused-argument

    dbt_resource = dbt_cli_resource.configured(
        {"project_dir": test_project_dir, "profiles_dir": dbt_config_dir, "select": "least_caloric"}
    )
    dbt_results = list(dbt_run_op(build_op_context(resources={"dbt": dbt_resource})))

    # includes asset materializations
    assert len(dbt_results) == 2

    assert len(dbt_results[-1].value.result["results"]) == 1


def test_run_test_job(
    dbt_seed, conn_string, test_project_dir, dbt_config_dir
):  # pylint: disable=unused-argument

    dbt_resource = dbt_cli_resource.configured(
        {"project_dir": test_project_dir, "profiles_dir": dbt_config_dir}
    )

    @job(resource_defs={"dbt": dbt_resource})
    def run_test_job():
        dbt_test_op(start_after=dbt_run_op())

    dbt_result = run_test_job.execute_in_process()

    dbt_run_result = dbt_result.output_for_node("dbt_run_op")
    dbt_test_result = dbt_result.output_for_node("dbt_test_op")

    assert len(dbt_run_result.result["results"]) == 4
    assert len(dbt_test_result.result["results"]) == 17
