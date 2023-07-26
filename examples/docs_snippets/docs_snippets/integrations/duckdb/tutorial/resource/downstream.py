from create_table import iris_dataset
from dagster_duckdb.resource import DuckDBResource

# start_example
from dagster import asset

from ..io_manager.source_asset import iris_harvest_data

# this example uses the iris_dataset asset from Step 1


@asset(deps=[iris_dataset])
def iris_setosa(duckdb: DuckDBResource) -> None:
    with duckdb.get_connection() as conn:
        conn.execute(
            "CREATE TABLE iris.iris_setosa AS SELECT * FROM iris.iris_dataset WHERE"
            " species = 'Iris-setosa'"
        )


# end_example
