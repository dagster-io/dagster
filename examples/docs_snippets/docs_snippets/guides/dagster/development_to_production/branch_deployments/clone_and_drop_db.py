import os

from dagster import In, Nothing, job, op


# start_clone_db
@op(required_resource_keys={"snowflake"})
def drop_database_clone(context):
    context.resources.snowflake.execute_query(
        "DROP DATABASE IF EXISTS"
        f" PRODUCTION_CLONE_{os.environ['DAGSTER_CLOUD_PULL_REQUEST_ID']}"
    )


@op(required_resource_keys={"snowflake"}, ins={"start": In(Nothing)})
def clone_production_database(context):
    context.resources.snowflake.execute_query(
        "CREATE DATABASE"
        f" PRODUCTION_CLONE_{os.environ['DAGSTER_CLOUD_PULL_REQUEST_ID']} CLONE"
        ' "PRODUCTION"'
    )


@job
def clone_prod():
    clone_production_database(start=drop_database_clone())


# end_clone_db
