iris_data = None

# start_example

import pandas as pd

from dagster import asset

# this example uses the iris_data asset from Step 2


@asset
def iris_setosa(iris_data: pd.DataFrame) -> pd.DataFrame:
    return iris_data[iris_data["species"] == "Iris-setosa"]


# end_example
