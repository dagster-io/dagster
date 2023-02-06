from dagster._cli import job


def scope_define_instance():
    # start_define_databricks_client_instance
    from dagster_databricks import databricks_client

    databricks_client_instance = databricks_client.configured(
        {
            "host": {"env": "DATABRICKS_HOST"},
            "token": {"env": "DATABRICKS_TOKEN"},
        }
    )
    # end_define_databricks_client_instance


DATABRICKS_JOB_ID = 1


def scope_define_databricks_custom_ops_and_assets():
    # start_define_databricks_custom_ops_and_assets
    from databricks_cli.sdk import JobsService

    from dagster import OpExecutionContext, asset, job, op

    @asset(required_resource_keys={"databricks"})
    def my_databricks_table(context: OpExecutionContext) -> None:
        databricks_api_client = context.resources.databricks.api_client
        jobs_service = JobsService(databricks_api_client)

        jobs_service.run_now(job_id=DATABRICKS_JOB_ID)

    @op(required_resource_keys={"databricks"})
    def my_databricks_op(context: OpExecutionContext) -> None:
        databricks_api_client = context.resources.databricks.api_client
        jobs_service = JobsService(databricks_api_client)

        jobs_service.run_now(job_id=DATABRICKS_JOB_ID)

    @job
    def my_databricks_job():
        my_databricks_op()

    # end_define_databricks_custom_ops_and_assets


def scope_define_databricks_op_factories():
    DATABRICKS_JOB_ID = 1
    # start_define_databricks_op_factories
    from dagster_databricks import (
        create_databricks_run_now_op,
        create_databricks_submit_run_op,
    )

    my_databricks_run_now_op = create_databricks_run_now_op(databricks_job_id=DATABRICKS_JOB_ID)

    my_databricks_submit_run_op = create_databricks_submit_run_op(
        databricks_job_configuration={
            "job": {
                "new_cluster": {
                    "spark_version": "2.1.0-db3-scala2.11",
                    "num_workers": 2,
                },
                "notebook_task": {
                    "notebook_path": "/Users/dagster@example.com/PrepareData",
                },
            }
        },
    )

    @job
    def my_databricks_job():
        my_databricks_run_now_op()
        my_databricks_submit_run_op()

    # end_define_databricks_op_factories


def scope_schedule_databricks():
    from dagster_databricks import databricks_client as databricks_client_instance

    from dagster import asset, job

    @asset
    def my_databricks_table():
        ...

    @job
    def my_databricks_job():
        ...

    # start_schedule_databricks
    from dagster import (
        AssetSelection,
        Definitions,
        ScheduleDefinition,
        define_asset_job,
    )

    materialize_databricks_table = define_asset_job(
        name="materialize_databricks_table",
        selection=AssetSelection.keys("my_databricks_table").downstream(),
    )

    defs = Definitions(
        assets=[my_databricks_table],
        schedules=[
            ScheduleDefinition(
                job=materialize_databricks_table,
                cron_schedule="@daily",
            ),
            ScheduleDefinition(
                job=my_databricks_job,
                cron_schedule="@daily",
            ),
        ],
        jobs=[my_databricks_job],
        resources={"databricks": databricks_client_instance},
    )
    # end_schedule_databricks
