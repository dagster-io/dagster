import pandas as pd

import dagster as dg


@dg.asset
def processed_data():
    ## Read data from the CSV
    df = pd.read_csv("data/sample_data.csv")

    ## Add an age_group column based on the value of age
    df["age_group"] = pd.cut(
        df["age"], bins=[0, 30, 40, 100], labels=["Young", "Middle", "Senior"]
    )

    ## Save processed data
    df.to_csv("data/processed_data.csv", index=False)
    return "Data loaded successfully"


## Tell Dagster about the assets that make up the pipeline by
## passing it to the Definitions object
## This allows Dagster to manage the assets' execution and dependencies
defs = dg.Definitions(assets=[processed_data])
