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


def scope_define_databricks_custom_asset():
    # start_define_databricks_custom_asset
    from databricks_cli.sdk import JobsService

    from dagster import (
        AssetExecutionContext,
        AssetSelection,
        asset,
        define_asset_job,
    )

    @asset(required_resource_keys={"databricks"})
    def my_databricks_table(context: AssetExecutionContext) -> None:
        databricks_api_client = context.resources.databricks.api_client
        jobs_service = JobsService(databricks_api_client)

        jobs_service.run_now(job_id=DATABRICKS_JOB_ID)

    materialize_databricks_table = define_asset_job(
        name="materialize_databricks_table",
        selection=AssetSelection.keys("my_databricks_table"),
    )

    # end_define_databricks_custom_asset


def scope_define_databricks_custom_op():
    from dagster_databricks import databricks_client as databricks_client_instance

    # start_define_databricks_custom_op
    from databricks_cli.sdk import DbfsService

    from dagster import (
        AssetExecutionContext,
        job,
        op,
    )

    @op(required_resource_keys={"databricks"})
    def my_databricks_op(context: AssetExecutionContext) -> None:
        databricks_api_client = context.resources.databricks.api_client
        dbfs_service = DbfsService(databricks_api_client)

        dbfs_service.read(path="/tmp/HelloWorld.txt")

    @job(resource_defs={"databricks": databricks_client_instance})
    def my_databricks_job():
        my_databricks_op()

    # end_define_databricks_custom_op


def scope_define_databricks_op_factories():
    from dagster_databricks import databricks_client as databricks_client_instance

    DATABRICKS_JOB_ID = 1
    # start_define_databricks_op_factories
    from dagster_databricks import create_databricks_run_now_op

    my_databricks_run_now_op = create_databricks_run_now_op(
        databricks_job_id=DATABRICKS_JOB_ID,
    )

    @job(resource_defs={"databricks": databricks_client_instance})
    def my_databricks_job():
        my_databricks_run_now_op()

    # end_define_databricks_op_factories


def scope_schedule_databricks():
    from dagster_databricks import databricks_client as databricks_client_instance

    from dagster import AssetSelection, asset, define_asset_job, job

    @asset
    def my_databricks_table():
        ...

    materialize_databricks_table = define_asset_job(
        name="materialize_databricks_table",
        selection=AssetSelection.keys("my_databricks_table"),
    )

    @job
    def my_databricks_job():
        ...

    # start_schedule_databricks
    from dagster import (
        AssetSelection,
        Definitions,
        ScheduleDefinition,
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
