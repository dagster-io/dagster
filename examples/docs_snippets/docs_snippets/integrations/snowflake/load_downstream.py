iris_dataset = None

# start_example

import pandas as pd

from dagster import asset

# this example uses the iris_dataset asset from Step 2


@asset
def iris_cleaned(iris_dataset: pd.DataFrame) -> pd.DataFrame:
    return iris_dataset.dropna().drop_duplicates()


# end_example
