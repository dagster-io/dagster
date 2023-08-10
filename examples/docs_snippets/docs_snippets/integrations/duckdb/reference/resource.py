# pyright: reportGeneralTypeIssues=none
# pyright: reportOptionalMemberAccess=none

# start
import pandas as pd
from dagster_duckdb import DuckDBResource

from dagster import Definitions, asset

# this example executes a query against the IRIS_DATASET table created in Step 2 of the
# Using Dagster with DuckDB tutorial


@asset
def small_petals(duckdb: DuckDBResource) -> pd.DataFrame:
    with duckdb.get_connection() as conn:
        return (
            conn.cursor()
            .execute(
                "SELECT * FROM IRIS_DATASET WHERE 'petal_length_cm' < 1 AND"
                " 'petal_width_cm' < 1"
            )
            .fetch_df()
        )


defs = Definitions(
    assets=[small_petals],
    resources={
        "duckdb": DuckDBResource(
            database="path/to/my_duckdb_database.duckdb",
            schema="IRIS",
        )
    },
)

# end
