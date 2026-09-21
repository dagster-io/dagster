# start
from dagster_clickhouse import ClickhouseResource  # ty: ignore[unresolved-import]

from dagster import asset

# This example executes a query against the `iris.iris_dataset` table created in the
# Using ClickHouse with Dagster guide.
iris_dataset = asset(name="iris_dataset")(lambda: None)


@asset(deps=[iris_dataset])
def small_petals(clickhouse: ClickhouseResource) -> None:
    with clickhouse.get_connection() as client:
        client.execute("DROP TABLE IF EXISTS iris.small_petals")
        client.execute(
            "CREATE TABLE iris.small_petals ENGINE = MergeTree() ORDER BY tuple() AS"
            " SELECT * FROM iris.iris_dataset WHERE petal_length_cm < 2 AND petal_width_cm < 0.5"
        )


# end
