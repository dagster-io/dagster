from dagster import asset


@asset
def iris_dataset():
    return None


# start_configuration

from dagster_deltalake import LocalConfig
from dagster_deltalake_polars import DeltaLakePolarsIOManager

from dagster import Definitions

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": DeltaLakePolarsIOManager(
            root_uri="path/to/deltalake",  # required
            storage_options=LocalConfig(),  # required
            schema="iris",  # optional, defaults to PUBLIC
        )
    },
)

# end_configuration
