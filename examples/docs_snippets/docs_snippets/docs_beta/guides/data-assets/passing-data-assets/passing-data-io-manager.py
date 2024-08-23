import pandas as pd
from dagster_duckdb_pandas import DuckDBPandasIOManager

from dagster import Definitions, asset

# highlight-start
duckdb_io_manager = DuckDBPandasIOManager(
    database="my_database.duckdb", schema="my_schema"
)


@asset
def people():
    return pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})


@asset
def birds():
    return pd.DataFrame({"id": [1, 2, 3], "name": ["Bluebird", "Robin", "Eagle"]})


@asset
def combined_data(people, birds):
    return pd.concat([people, birds])
    # highlight-end


defs = Definitions(
    assets=[people, birds, combined_data],
    resources={"io_manager": duckdb_io_manager},
)

if __name__ == "__main__":
    from dagster import materialize

    materialize(assets=[people, birds, combined_data])
