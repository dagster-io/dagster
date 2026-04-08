from dagster_clickhouse import ClickhouseResource

from .create_table import iris_dataset

# ruff: isort: split
# start_example
from dagster import asset


@asset(deps=[iris_dataset])
def iris_setosa(clickhouse: ClickhouseResource) -> None:
    with clickhouse.get_connection() as client:
        client.execute("DROP TABLE IF EXISTS iris.iris_setosa")
        client.execute(
            "CREATE TABLE iris.iris_setosa ENGINE = MergeTree() ORDER BY tuple() AS"
            " SELECT * FROM iris.iris_dataset WHERE species = 'Iris-setosa'"
        )


# end_example
