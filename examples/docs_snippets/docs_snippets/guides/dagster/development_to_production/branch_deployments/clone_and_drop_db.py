import os

# start_clone_db
from dagster_snowflake import SnowflakeConnection

from dagster import In, Nothing, ResourceParam, graph, op


@op(required_resource_keys={"snowflake"})
def drop_database_clone(snowflake: ResourceParam[SnowflakeConnection]):
    snowflake.execute_query(
        "DROP DATABASE IF EXISTS"
        f" PRODUCTION_CLONE_{os.environ['DAGSTER_CLOUD_PULL_REQUEST_ID']}"
    )


@op(ins={"start": In(Nothing)})
def clone_production_database(snowflake: ResourceParam[SnowflakeConnection]):
    snowflake.execute_query(
        "CREATE DATABASE"
        f" PRODUCTION_CLONE_{os.environ['DAGSTER_CLOUD_PULL_REQUEST_ID']} CLONE"
        ' "PRODUCTION"'
    )


@graph
def clone_prod():
    clone_production_database(start=drop_database_clone())


@graph
def drop_prod_clone():
    drop_database_clone()


# end_clone_db
