from dagster import AssetExecutionContext, Definitions, EnvVar, asset
from dagster_snowflake import SnowflakeResource

snowflake = SnowflakeResource(
    account=EnvVar("SNOWFLAKE_ACCOUNT"),
    user=EnvVar("SNOWFLAKE_USER"),
    password=EnvVar("SNOWFLAKE_PASSWORD"),
    warehouse="YOUR_WAREHOUSE",
    database="YOUR_DATABASE",
    schema="YOUR_SCHEMA",
    role="YOUR_ROLE",
)


# highlight-start
@asset
def load_csv_to_snowflake(context: AssetExecutionContext, snowflake: SnowflakeResource):
    csv_file_path = "path/to/your/file.csv"
    table_name = "your_table_name"

    copy_query = f"""
    COPY INTO {table_name}
    FROM 'file://{csv_file_path}'
    FILE_FORMAT = (TYPE = 'CSV', FIELD_OPTIONALLY_ENCLOSED_BY = '"')
    ON_ERROR = 'CONTINUE';
    """

    with snowflake.get_connection() as conn:
        conn.cursor().execute(copy_query)

    context.log.info(f"Loaded data from {csv_file_path} into {table_name}")


defs = Definitions(assets=[load_csv_to_snowflake], resources={"snowflake": snowflake})
# highlight-end
