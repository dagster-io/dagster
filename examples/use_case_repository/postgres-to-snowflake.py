from dagster import Definitions, EnvVar, asset, ResourceParam
from dagster_snowflake import SnowflakeResource
from sqlalchemy import create_engine, Engine
import pandas as pd
from snowflake.connector.pandas_tools import write_pandas

# Step 1: Configure Connections
# Define Snowflake resource
snowflake_resource = SnowflakeResource(
    account="your_snowflake_account",
    user=EnvVar("SNOWFLAKE_USER"),
    password=EnvVar("SNOWFLAKE_PASSWORD"),
    database="your_snowflake_database",
    schema="your_snowflake_schema",
)

# Define Postgres connection
postgres_engine = create_engine("postgresql://user:password@localhost:5432/your_database")

defs = Definitions(
    resources={
        "snowflake": snowflake_resource,
        "postgres": postgres_engine,
    }
)


# Step 2: Define the Extraction Asset
@asset
def extract_data(postgres: ResourceParam[Engine]) -> pd.DataFrame:
    with postgres.connect() as conn:
        query = "SELECT * FROM your_table"
        df = pd.read_sql_query(query, conn)
    return df


# Step 3: Define the Transformation and Loading Asset
@asset
def transform_and_load_data(extract_data: pd.DataFrame, snowflake: SnowflakeResource):
    # Perform any necessary transformations
    transformed_data = extract_data  # Add your transformation logic here

    # Load data into Snowflake
    with snowflake.get_connection() as conn:
        write_pandas(
            conn, transformed_data, "your_snowflake_table", auto_create_table=True, overwrite=True
        )
