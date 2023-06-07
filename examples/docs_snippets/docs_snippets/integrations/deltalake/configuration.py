from dagster import asset


@asset
def iris_dataset():
    return None


# start_example

from dagster_deltalake import LocalConfig
from dagster_deltalake_pandas import DeltaLakePandasIOManager

from dagster import Definitions

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": DeltaLakePandasIOManager(
            root_uri="path/to/deltalake",  # required
            storage_options=LocalConfig(),  # required
            schema="iris",  # optional, defaults to "public"
        )
    },
)

# end_example
