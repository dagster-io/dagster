from dagster_snowflake import SnowflakeResource

# Define a resource named `iris_db`
iris_db = SnowflakeResource(
    # Passwords in code is bad practice; we'll fix this later
    password="snowflake_password",
    warehouse="snowflake_warehouse",
    account="snowflake_account",
    user="snowflake_user",
    database="iris_database",
    schema="iris_schema",
)
