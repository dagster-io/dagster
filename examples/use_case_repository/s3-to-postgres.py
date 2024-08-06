from dagster import Definitions, EnvVar, asset
from dagster_aws.s3 import S3Resource
from dagster_postgres import PostgresResource
import pandas as pd
import io

# Step 2: Configure AWS S3 and Postgres Resources
s3_resource = S3Resource(
    region_name="us-west-1",
    aws_access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=EnvVar("AWS_SESSION_TOKEN"),
)

postgres_resource = PostgresResource(
    host="your-postgres-host",
    port="5432",
    username=EnvVar("POSTGRES_USER"),
    password=EnvVar("POSTGRES_PASSWORD"),
    database="your-database",
)


# Step 3: Define Assets to Extract Data from S3
@asset(required_resource_keys={"s3"})
def extract_data_from_s3(context):
    s3_client = context.resources.s3.get_client()
    response = s3_client.get_object(Bucket="your-bucket", Key="your-key")
    data = pd.read_csv(io.BytesIO(response["Body"].read()))
    return data


# Step 4: Define Assets to Transform Data (Optional)
@asset
def transform_data(extract_data_from_s3):
    # Example transformation: filter rows where column 'value' > 10
    transformed_data = extract_data_from_s3[extract_data_from_s3["value"] > 10]
    return transformed_data


# Step 5: Define Assets to Load Data into Postgres
@asset(required_resource_keys={"postgres"})
def load_data_to_postgres(context, transform_data):
    engine = context.resources.postgres.get_engine()
    transform_data.to_sql("your_table", engine, if_exists="replace", index=False)


# Step 6: Combine Assets in Definitions
defs = Definitions(
    assets=[extract_data_from_s3, transform_data, load_data_to_postgres],
    resources={
        "s3": s3_resource,
        "postgres": postgres_resource,
    },
)
