from dagster import asset


@asset
def iris_dataset():
    return None


# start_example

from dagster_clickhouse_pandas import ClickhousePandasIOManager

from dagster import Definitions

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": ClickhousePandasIOManager(
            host="localhost",
            port=9000,
            database="default",
            schema="iris",
        )
    },
)


# end_example
