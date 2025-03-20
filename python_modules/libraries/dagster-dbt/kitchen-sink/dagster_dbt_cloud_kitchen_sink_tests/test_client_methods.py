from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace, get_dagster_adhoc_job_name
from dagster_dbt.cloud_v2.types import DbtCloudJob, DbtCloudJobRunStatusType, DbtCloudRun


def test_cloud_job_apis(
    workspace: DbtCloudWorkspace,
    project_id: int,
    environment_id: int,
) -> None:
    """Tests that we can create / destroy a dagster job."""
    client = workspace.get_client()
    job_name = get_dagster_adhoc_job_name(project_id=project_id, environment_id=environment_id)
    created_job = DbtCloudJob.from_job_details(
        job_details=client.create_job(
            project_id=project_id,
            environment_id=environment_id,
            job_name=job_name,
        )
    )
    job = DbtCloudJob.from_job_details(job_details=client.get_job_details(job_id=created_job.id))
    assert job.name == job_name
    jobs = [
        DbtCloudJob.from_job_details(job_details=job_details)
        for job_details in client.list_jobs(
            project_id=project_id,
            environment_id=environment_id,
        )
    ]
    assert created_job.id in set([job.id for job in jobs])

    run = DbtCloudRun.from_run_details(
        run_details=client.trigger_job_run(
            job_id=created_job.id, steps_override=["dbt run --select tag:test"]
        )
    )
    polled_run = DbtCloudRun.from_run_details(
        run_details=client.poll_run(run_id=run.id, poll_timeout=600)
    )
    assert run.id == polled_run.id
    assert polled_run.status == DbtCloudJobRunStatusType.SUCCESS
    run_results = client.get_run_results_json(run_id=polled_run.id)
    assert {result["unique_id"] for result in run_results["results"]} == {
        "model.test_environment.customers",
        "model.test_environment.stg_customers",
        "model.test_environment.stg_orders",
    }

    client.destroy_job(job_id=created_job.id)
    jobs = [
        DbtCloudJob.from_job_details(job_details=job_details)
        for job_details in client.list_jobs(
            project_id=project_id,
            environment_id=environment_id,
        )
    ]
    assert created_job.id not in set([job.id for job in jobs])
