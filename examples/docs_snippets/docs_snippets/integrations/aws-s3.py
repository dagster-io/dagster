import pandas as pd
from dagster_aws.s3 import S3Resource

import dagster as dg


@dg.asset
def my_s3_asset(s3: S3Resource):
    df = pd.DataFrame({"column1": [1, 2, 3], "column2": ["A", "B", "C"]})

    csv_data = df.to_csv(index=False)

    s3_client = s3.get_client()

    s3_client.put_object(
        Bucket="my-cool-bucket",
        Key="path/to/my_dataframe.csv",
        Body=csv_data,
    )


defs = dg.Definitions(
    assets=[my_s3_asset],
    resources={"s3": S3Resource(region_name="us-west-2")},
)
