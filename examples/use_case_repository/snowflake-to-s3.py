import pandas as pd
from dagster import AssetExecutionContext, Definitions, EnvVar, asset, materialize
from dagster_aws.s3 import S3Resource
from dagster_snowflake import SnowflakeResource

# Step 1: Set Up Snowflake and S3 Resources
snowflake_resource = SnowflakeResource(
    account=EnvVar("SNOWFLAKE_ACCOUNT"),
    user=EnvVar("SNOWFLAKE_USER"),
    password=EnvVar("SNOWFLAKE_PASSWORD"),
    warehouse=EnvVar("SNOWFLAKE_WAREHOUSE"),
    database=EnvVar("SNOWFLAKE_DATABASE"),
    role=EnvVar("SNOWFLAKE_ROLE"),
)

s3_resource = S3Resource(
    bucket=EnvVar("S3_BUCKET"),
    access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),
    secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),
)

defs = Definitions(
    resources={
        "snowflake": snowflake_resource,
        "s3": s3_resource,
    }
)


# Step 2: Define the Data Extraction Asset
@asset(required_resource_keys={"snowflake", "s3"})
def extract_data_from_snowflake(context: AssetExecutionContext):
    query = "SELECT * FROM your_table"
    snowflake = context.resources.snowflake
    s3 = context.resources.s3

    # Execute the query and fetch the data
    df = pd.read_sql(query, snowflake.get_connection())

    # Convert DataFrame to CSV and upload to S3
    csv_buffer = df.to_csv(index=False)
    s3.put_object(Key="data/your_table.csv", Body=csv_buffer)


# Step 3: Materialize the Asset
materialize(
    [extract_data_from_snowflake], resources={"snowflake": snowflake_resource, "s3": s3_resource}
)
