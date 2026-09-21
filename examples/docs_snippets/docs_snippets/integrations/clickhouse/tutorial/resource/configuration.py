from dagster import asset


@asset
def iris_dataset():
    return None


# start_example

from dagster_clickhouse import ClickhouseResource  # ty: ignore[unresolved-import]

from dagster import Definitions

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "clickhouse": ClickhouseResource(
            host="localhost",
            port=9000,
        )
    },
)


# end_example
