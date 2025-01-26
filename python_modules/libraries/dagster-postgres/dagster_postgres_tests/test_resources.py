from dagster._utils.test.postgres_instance import TestPostgresInstance
from dagster._utils import file_relative_path
from dagster import asset, materialize_to_memory
from dagster_postgres import PostgresResource

import yaml
import time

def test_resource(hostname, conn_string):
    @asset
    def pg_create_table(postgres: PostgresResource):
        with postgres.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS films ("
                    " title varchar(40) NOT NULL,"
                    " year integer NOT NULL, "
                    " PRIMARY KEY(title));"
                )
                cur.execute(
                    "INSERT INTO films (title, year)"
                    " VALUES ('the matrix', 1999)"
                    " ON CONFLICT (title) DO NOTHING;"
                )
                cur.execute(
                    "INSERT INTO films (title, year)"
                    " VALUES ('fight club', 1999)"
                    " ON CONFLICT (title) DO NOTHING;"
                )
    
    @asset
    def pg_query_table(postgres: PostgresResource): 
        with postgres.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM films;")
                assert len(cur.fetchall()) == 2

    result = materialize_to_memory(
        [pg_create_table, pg_query_table],
        resources={
            "postgres": PostgresResource(
                dsn=conn_string
            )
        }
    )