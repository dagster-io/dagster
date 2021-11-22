from dagster_dbt import DbtCloudOutput

from .utils import sample_run_details, sample_run_results


def test_timestamps():

    run_details = sample_run_details()["data"]

    dbt_cloud_output = DbtCloudOutput(run_details, sample_run_results())

    assert dbt_cloud_output.created_at.isoformat(" ") == run_details["created_at"]
    assert dbt_cloud_output.updated_at.isoformat(" ") == run_details["updated_at"]
    assert dbt_cloud_output.dequeued_at.isoformat(" ") == run_details["dequeued_at"]
    assert dbt_cloud_output.started_at.isoformat(" ") == run_details["started_at"]
    assert dbt_cloud_output.finished_at.isoformat(" ") == run_details["finished_at"]


def test_included_related():

    run_details = sample_run_details()["data"]
    dbt_cloud_output = DbtCloudOutput(run_details, sample_run_results())
    assert dbt_cloud_output.job_name is None

    run_details = sample_run_details(include_related=["job"])["data"]
    dbt_cloud_output = DbtCloudOutput(run_details, sample_run_results())
    assert dbt_cloud_output.job_name == "MyCoolJob"
