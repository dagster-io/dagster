iris_dataset = None
rose_dataset = None

# start_example

from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler
from dagster_snowflake_pyspark import SnowflakePySparkTypeHandler

from dagster import Definitions

snowflake_io_manager = build_snowflake_io_manager(
    [SnowflakePandasTypeHandler(), SnowflakePySparkTypeHandler()]
)

defs = Definitions(
    assets=[iris_dataset, rose_dataset],
    resources={
        "io_manager": snowflake_io_manager.configured(
            {
                "account": "abc1234.us-east-1",
                "user": {"env": "SNOWFLAKE_USER"},
                "password": {"env": "SNOWFLAKE_PASSWORD"},
                "database": "FLOWERS",
                "warehouse": "PLANTS",
            }
        )
    },
)


# end_example
