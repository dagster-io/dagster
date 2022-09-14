# pylint: disable=unused-variable


def scope_dbt_cloud_job():
    # start_dbt_cloud_job
    from dagster_dbt import dbt_cloud_resource, dbt_cloud_run_op

    from dagster import job

    # configure an operation to run the specific job
    run_dbt_nightly_sync = dbt_cloud_run_op.configured(
        {"job_id": 33333}, name="run_dbt_nightly_sync"
    )

    # configure a resource to connect to your dbt Cloud instance
    my_dbt_cloud_resource = dbt_cloud_resource.configured(
        {"auth_token": {"env": "DBT_CLOUD_AUTH_TOKEN"}, "account_id": 11111}
    )

    # create a job that uses your op and resource
    @job(resource_defs={"dbt_cloud": my_dbt_cloud_resource})
    def my_dbt_cloud_job():
        run_dbt_nightly_sync()

    # end_dbt_cloud_job


def scope_dbt_cloud_job2():
    from dagster import ResourceDefinition, job, op

    @op
    def another_op():
        return 1

    run_dbt_nightly_sync = another_op
    my_dbt_cloud_resource = ResourceDefinition.none_resource()

    # start_dbt_cloud_job2
    @job(resource_defs={"dbt_cloud": my_dbt_cloud_resource})
    def my_two_op_job():
        run_dbt_nightly_sync(start_after=another_op())

    # end_dbt_cloud_job2


def scope_schedule_dbt_cloud():
    from dagster import job, op

    @op
    def foo():
        pass

    @job
    def my_dbt_cloud_job():
        foo()

    # start_schedule_dbt_cloud
    from dagster import ScheduleDefinition, repository

    @repository
    def my_repo():
        return [
            ScheduleDefinition(
                job=my_dbt_cloud_job,
                cron_schedule="@daily",
            ),
        ]

    # end_schedule_dbt_cloud
