from ..tutorial.resource.create_table import iris_dataset  # noqa: I001


# start
from dagster_clickhouse import ClickhouseResource

from dagster import asset


@asset(deps=[iris_dataset])
def small_petals(clickhouse: ClickhouseResource) -> None:
    with clickhouse.get_connection() as client:
        client.execute("DROP TABLE IF EXISTS iris.small_petals")
        client.execute(
            "CREATE TABLE iris.small_petals ENGINE = MergeTree() ORDER BY tuple() AS"
            " SELECT * FROM iris.iris_dataset WHERE petal_length_cm < 2 AND petal_width_cm < 0.5"
        )


# end
