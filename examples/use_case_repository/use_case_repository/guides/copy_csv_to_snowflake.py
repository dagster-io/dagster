from pathlib import Path

from dagster import AssetExecutionContext, Definitions, EnvVar, asset
from dagster_snowflake import SnowflakeResource

snowflake = SnowflakeResource(
    account=EnvVar("SNOWFLAKE_ACCOUNT"),
    user=EnvVar("SNOWFLAKE_USER"),
    password=EnvVar("SNOWFLAKE_PASSWORD"),
    warehouse=EnvVar("SNOWFLAKE_WAREHOUSE"),
    database=EnvVar("SNOWFLAKE_DATABASE"),
    schema=EnvVar("SNOWFLAKE_SCHEMA"),
    role=EnvVar("SNOWFLAKE_ROLE"),
)


@asset
def load_csv_to_snowflake(context: AssetExecutionContext, snowflake: SnowflakeResource):
    file_name = "example.csv"
    file_path = Path(__file__).parent / file_name
    table_name = "example_table"

    create_format = """
    create or replace file format csv_format
        type = 'CSV',
        field_optionally_enclosed_by = '"'
    """

    create_stage = """
    create or replace stage temporary_stage
        file_format = csv_format
    """

    put_file = f"""
    put 'file://{file_path}' @temporary_stage
        auto_compress=TRUE
    """

    create_table = f"""
    create table if not exists {table_name} (
        user_id INT,
        first_name VARCHAR,
        last_name VARCHAR,
        occupation VARCHAR
    )
    """

    copy_into = f"""
    copy into {table_name}
    from @temporary_stage/{file_name}.gz
    file_format = csv_format;
    """

    with snowflake.get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(create_format)
            curs.execute(create_stage)
            curs.execute(put_file)
            curs.execute(create_table)
            curs.execute(copy_into)

    context.log.info(f"Loaded data from {file_path} into {table_name}")


defs = Definitions(assets=[load_csv_to_snowflake], resources={"snowflake": snowflake})
