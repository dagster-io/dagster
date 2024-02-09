# start_example
import pandas as pd
from create_table import iris_dataset
from dagster_snowflake import SnowflakeResource

from dagster import asset

# this example uses the iris_dataset asset from Step 2


@asset(deps=[iris_dataset])
def iris_setosa(snowflake: SnowflakeResource) -> None:
    with snowflake.get_connection() as conn:
        conn.execute(
            "CREATE TABLE iris.iris_setosa AS SELECT * FROM iris.iris_dataset WHERE"
            " species = 'Iris-setosa'"
        )


# end_example
