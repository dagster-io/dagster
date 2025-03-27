import pandas as pd
from dagster_duckdb_pandas import DuckDBPandasIOManager

import dagster as dg


@dg.asset(
    key_prefix=["my_schema"]  # will be used as the schema in duckdb
)
def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
    return pd.DataFrame()


defs = dg.Definitions(
    assets=[my_table],
    resources={"io_manager": DuckDBPandasIOManager(database="my_db.duckdb")},
)
