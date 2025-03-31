import datetime

from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace, get_dagster_adhoc_job_name
from dagster_dbt.cloud_v2.types import (
    DbtCloudEnvironment,
    DbtCloudJob,
    DbtCloudJobRunStatusType,
    DbtCloudProject,
    DbtCloudRun,
)


def test_cloud_job_apis(
    workspace: DbtCloudWorkspace,
    project_id: int,
    environment_id: int,
) -> None:
    """Tests that we can create / destroy a dagster job."""
    client = workspace.get_client()
    project = DbtCloudProject.from_project_details(
        project_details=client.get_project_details(project_id=project_id)
    )
    environment = DbtCloudEnvironment.from_environment_details(
        environment_details=client.get_environment_details(environment_id=environment_id)
    )
    job_name = get_dagster_adhoc_job_name(
        project_id=project.id,
        project_name=project.name,
        environment_id=environment.id,
        environment_name=environment.name,
    )
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

    start_run_process = datetime.datetime.utcnow()
    run = DbtCloudRun.from_run_details(
        run_details=client.trigger_job_run(
            job_id=created_job.id, steps_override=["dbt run --select tag:test"]
        )
    )
    polled_run = DbtCloudRun.from_run_details(
        run_details=client.poll_run(run_id=run.id, poll_timeout=600)
    )
    end_run_process = datetime.datetime.utcnow()

    assert run.id == polled_run.id
    assert polled_run.status == DbtCloudJobRunStatusType.SUCCESS

    batched_runs, total_count = client.get_runs_batch(
        project_id=project_id,
        environment_id=environment_id,
        finished_at_lower_bound=start_run_process,
        finished_at_upper_bound=end_run_process,
    )
    # If this test is executed multiple times in parallel, e.g. in another PR, there might be more than one run.
    assert total_count >= 1
    assert len(batched_runs) >= 1
    assert any(
        run.id == DbtCloudRun.from_run_details(run_details=batched_run).id
        for batched_run in batched_runs
    )

    run_artifacts = client.list_run_artifacts(run_id=run.id)
    assert "run_results.json" in run_artifacts

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
