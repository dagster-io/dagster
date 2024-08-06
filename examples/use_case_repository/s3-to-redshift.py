from io import StringIO

import pandas as pd
from dagster import Definitions, EnvVar, asset
from dagster_aws.redshift import RedshiftClientResource
from dagster_aws.s3 import S3Resource

# Step 1: Configure AWS Resources
s3_resource = S3Resource(
    region_name="us-west-1",
    aws_access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=EnvVar("AWS_SESSION_TOKEN"),
)

redshift_resource = RedshiftClientResource(
    host="my-redshift-cluster.us-west-1.redshift.amazonaws.com",
    port=5439,
    user="dagster",
    password=EnvVar("DAGSTER_REDSHIFT_PASSWORD"),
    database="dev",
)


# Step 2: Define the S3 to Redshift Asset
@asset
def s3_to_redshift(context, s3: S3Resource, redshift: RedshiftClientResource):
    # Read data from S3
    s3_key = "path/to/your/data.csv"
    s3_object = s3.get_object(Bucket="your-s3-bucket", Key=s3_key)
    data = s3_object["Body"].read().decode("utf-8")
    df = pd.read_csv(StringIO(data))

    # Transform data if necessary
    # df = transform_data(df)

    # Load data into Redshift
    redshift.get_client().execute_query(
        f"""
        COPY your_table
        FROM 's3://your-s3-bucket/{s3_key}'
        IAM_ROLE 'arn:aws:iam::your-account-id:role/your-redshift-role'
        CSV
        IGNOREHEADER 1;
        """
    )


defs = Definitions(
    assets=[s3_to_redshift],
    resources={
        "s3": s3_resource,
        "redshift": redshift_resource,
    },
)
