from dagster_clickhouse import ClickhouseResource

# ruff: isort: split
# start_example
from dagster import asset

# This example executes a query against the `iris.iris_dataset` table created in the
# Using ClickHouse with Dagster guide.
iris_dataset = asset(name="iris_dataset")(lambda: None)


@asset(deps=[iris_dataset])
def iris_setosa(clickhouse: ClickhouseResource) -> None:
    with clickhouse.get_connection() as client:
        client.execute("DROP TABLE IF EXISTS iris.iris_setosa")
        client.execute(
            "CREATE TABLE iris.iris_setosa ENGINE = MergeTree() ORDER BY tuple() AS"
            " SELECT * FROM iris.iris_dataset WHERE species = 'Iris-setosa'"
        )


# end_example
