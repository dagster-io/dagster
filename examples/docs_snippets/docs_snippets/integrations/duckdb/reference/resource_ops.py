# start
from dagster_duckdb import DuckDBResource

from dagster import op


@op
def export_iris_data(duckdb: DuckDBResource) -> None:
    with duckdb.get_connection() as conn:  # conn is a DuckDBPyConnection
        conn.cursor().execute(
            "EXPORT DATABASE 'iris_copy' (FORMAT CSV, DELIMITER '|');"
        )


# end
