import os

from dagster_snowflake import SnowflakeResource

import dagster as dg


@dg.op
def drop_database_clone(snowflake: SnowflakeResource):
    with snowflake.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DROP DATABASE IF EXISTS"
            f" PRODUCTION_CLONE_{os.environ['DAGSTER_CLOUD_PULL_REQUEST_ID']}"
        )


@dg.op(ins={"start": dg.In(dg.Nothing)})
def clone_production_database(snowflake: SnowflakeResource):
    with snowflake.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "CREATE DATABASE"
            f" PRODUCTION_CLONE_{os.environ['DAGSTER_CLOUD_PULL_REQUEST_ID']} CLONE"
            ' "PRODUCTION"'
        )


@dg.graph
def clone_prod():
    clone_production_database(start=drop_database_clone())


@dg.graph
def drop_prod_clone():
    drop_database_clone()
