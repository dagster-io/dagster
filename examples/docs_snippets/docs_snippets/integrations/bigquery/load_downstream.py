iris_data = None

# start_example

import pandas as pd

from dagster import asset

# this example uses the iris_data asset from Step 2


@asset
def iris_cleaned(iris_data: pd.DataFrame) -> pd.DataFrame:
    return iris_data.dropna().drop_duplicates()


# end_example
