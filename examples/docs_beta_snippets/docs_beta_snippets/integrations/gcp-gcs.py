import pandas as pd
from dagster_gcp.gcs import GCSResource

import dagster as dg


@dg.asset
def my_gcs_asset(gcs: GCSResource):
    df = pd.DataFrame({"column1": [1, 2, 3], "column2": ["A", "B", "C"]})

    csv_data = df.to_csv(index=False)

    gcs_client = gcs.get_client()

    bucket = gcs_client.bucket("my-cool-bucket")
    blob = bucket.blob("path/to/my_dataframe.csv")
    blob.upload_from_string(csv_data)


defs = dg.Definitions(
    assets=[my_gcs_asset],
    resources={"gcs": GCSResource(project="my-gcp-project")},
)
