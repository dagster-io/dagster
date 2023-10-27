iris_dataset = None

# start_example

import pandas as pd

from dagster import asset

# this example uses the iris_dataset asset from Step 2


@asset
def iris_setosa(iris_dataset: pd.DataFrame) -> pd.DataFrame:
    return iris_dataset[iris_dataset["species"] == "Iris-setosa"]


# end_example
