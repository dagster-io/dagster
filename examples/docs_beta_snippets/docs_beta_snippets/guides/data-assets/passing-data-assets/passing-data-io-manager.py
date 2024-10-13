import pandas as pd
from dagster_duckdb_pandas import DuckDBPandasIOManager

import dagster as dg

# highlight-start
duckdb_io_manager = DuckDBPandasIOManager(
    database="my_database.duckdb", schema="my_schema"
)


@dg.asset
def people():
    return pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})


@dg.asset
def birds():
    return pd.DataFrame({"id": [1, 2, 3], "name": ["Bluebird", "Robin", "Eagle"]})


@dg.asset
def combined_data(people, birds):
    return pd.concat([people, birds])
    # highlight-end


defs = dg.Definitions(
    assets=[people, birds, combined_data],
    resources={"io_manager": duckdb_io_manager},
)

if __name__ == "__main__":
    dg.materialize(assets=[people, birds, combined_data])
