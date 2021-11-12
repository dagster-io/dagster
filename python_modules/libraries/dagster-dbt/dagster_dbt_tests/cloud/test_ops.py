import pytest
import responses
from dagster import Failure, job
from dagster.check import CheckError
from dagster_dbt import dbt_cloud_resource, dbt_cloud_run_op

from .utils import (
    SAMPLE_ACCOUNT_ID,
    SAMPLE_API_PREFIX,
    SAMPLE_JOB_ID,
    SAMPLE_RUN_ID,
    sample_job_details,
    sample_run_details,
    sample_run_results,
)


@pytest.mark.parametrize(
    "final_status,expected_behavior",
    [("Success", 0), ("Error", 1), ("Cancelled", 1), ("Running", 2), ("FooBarBaz", 3)],
)
def test_run_materializations(final_status, expected_behavior):
    my_dbt_cloud = dbt_cloud_run_op.configured(
        {"job_id": SAMPLE_JOB_ID, "poll_interval": 0.05, "poll_timeout": 1}, name="my_dbt_cloud"
    )

    @job(
        resource_defs={
            "dbt_cloud": dbt_cloud_resource.configured(
                {"auth_token": "some_auth_token", "account_id": SAMPLE_ACCOUNT_ID}
            )
        }
    )
    def dbt_job():
        my_dbt_cloud()

    with responses.RequestsMock() as rsps:
        # endpoint for job details info
        rsps.add(rsps.GET, f"{SAMPLE_API_PREFIX}/jobs/{SAMPLE_JOB_ID}/", json=sample_run_details())
        # endpoint for disabling job schedule
        rsps.add(rsps.POST, f"{SAMPLE_API_PREFIX}/jobs/{SAMPLE_JOB_ID}/", json=sample_job_details())
        # endpoint for launching run
        rsps.add(
            rsps.POST, f"{SAMPLE_API_PREFIX}/jobs/{SAMPLE_JOB_ID}/run/", json=sample_run_details()
        )
        # endpoint for polling run details
        for i in range(10):
            if i == 0:
                status = "Queued"
            elif i == 1:
                status = "Starting"
            elif i < 9:
                status = "Running"
            else:
                status = final_status
            rsps.add(
                rsps.GET,
                f"{SAMPLE_API_PREFIX}/runs/{SAMPLE_RUN_ID}/",
                json=sample_run_details(status_humanized=status),
            )
        if expected_behavior == 0:
            # endpoint for run_results.json
            rsps.add(
                rsps.GET,
                f"{SAMPLE_API_PREFIX}/runs/{SAMPLE_RUN_ID}/artifacts/run_results.json",
                json=sample_run_results(),
            )
        if expected_behavior == 2:
            # endpoint for cancelling run
            rsps.add(
                rsps.POST,
                f"{SAMPLE_API_PREFIX}/runs/{SAMPLE_RUN_ID}/cancel/",
                json=sample_run_details(),
            )

        if expected_behavior == 0:
            execution_result = dbt_job.execute_in_process()
            assert execution_result.success
            dbt_cloud_output = execution_result.output_for_node("my_dbt_cloud")
            assert dbt_cloud_output.result == sample_run_results()
            assert dbt_cloud_output.run_details == sample_run_details()["data"]

            asset_materializations = [
                event
                for event in execution_result.events_for_node("my_dbt_cloud")
                if event.event_type_value == "ASSET_MATERIALIZATION"
            ]
            assert len(asset_materializations) == 2
        elif expected_behavior == 1:
            with pytest.raises(Failure, match=f"Run {SAMPLE_RUN_ID} failed"):
                dbt_job.execute_in_process()
        elif expected_behavior == 2:
            with pytest.raises(Failure, match=f"Run {SAMPLE_RUN_ID} timed out"):
                dbt_job.execute_in_process()
        elif expected_behavior == 3:
            with pytest.raises(CheckError, match=f"Received unexpected status '{final_status}'"):
                dbt_job.execute_in_process()
