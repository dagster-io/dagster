import pytest
from dagster import asset, materialize_to_memory
from dagster_postgres import PostgresResource


class CustomError(Exception):
    pass


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
        [pg_create_table, pg_query_table], resources={"postgres": PostgresResource(dsn=conn_string)}
    )

    assert result.success


# Make sure that our resource behavior is analogous to the psycopg connection behaviour:
# https://www.psycopg.org/docs/usage.html#transactions-control
# Transactions should be commited on succesful exits from the context manager,
# and rolled back if an exception is thrown.
def test_transaction_is_rolled_back_on_exception(hostname, conn_string):
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
    def pg_failing_asset(postgres: PostgresResource):
        with postgres.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO films (title, year)"
                    " VALUES ('the return of the king', 2003)"
                    " ON CONFLICT (title) DO NOTHING;"
                )
            raise CustomError()

    @asset
    def pg_query_table(postgres: PostgresResource):
        with postgres.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM films;")
                assert len(cur.fetchall()) == 2

    # Add 2 rows to the 'films' table, and make sure the 2 rows were written succesfully.
    result = materialize_to_memory(
        [pg_create_table, pg_query_table], resources={"postgres": PostgresResource(dsn=conn_string)}
    )
    assert result.success

    # Add a third row, but since an exception is thrown later, we should rollback the transaction.
    with pytest.raises(CustomError):
        materialize_to_memory(
            [pg_failing_asset], resources={"postgres": PostgresResource(dsn=conn_string)}
        )

    # Make sure there are only 2 rows in the 'films' table.
    result = materialize_to_memory(
        [pg_query_table], resources={"postgres": PostgresResource(dsn=conn_string)}
    )
    assert result.success
