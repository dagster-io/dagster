import pandas as pd
from dagster_aws.s3 import S3Resource

import dagster as dg


@dg.asset
def my_s3_compatible_asset(s3: S3Resource):
    df = pd.DataFrame({"column1": [1, 2, 3], "column2": ["A", "B", "C"]})

    csv_data = df.to_csv(index=False)

    s3_compatible_client = s3.get_client()

    s3_compatible_client.put_object(
        Bucket="my-cool-bucket",
        Key="path/to/my_dataframe.csv",
        Body=csv_data,
    )


# ``S3Resource`` works with any S3-compatible object store (for example,
# Backblaze B2, Cloudflare R2, or MinIO) by setting ``endpoint_url`` to the
# provider's S3 endpoint. Replace the placeholder below with that endpoint.
defs = dg.Definitions(
    assets=[my_s3_compatible_asset],
    resources={
        "s3": S3Resource(
            endpoint_url="https://your-s3-endpoint.example.com",
            aws_access_key_id="<your-access-key-id>",
            aws_secret_access_key="<your-secret-access-key>",
        )
    },
)
