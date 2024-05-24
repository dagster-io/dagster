import os

# start_clone_db
from dagster_snowflake import SnowflakeResource

from dagster import In, Nothing, graph, op


@op
def drop_database_clone(snowflake: SnowflakeResource):
    with snowflake.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DROP DATABASE IF EXISTS"
            f" PRODUCTION_CLONE_{os.environ['DAGSTER_CLOUD_PULL_REQUEST_ID']}"
        )


@op(ins={"start": In(Nothing)})
def clone_production_database(snowflake: SnowflakeResource):
    with snowflake.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
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
