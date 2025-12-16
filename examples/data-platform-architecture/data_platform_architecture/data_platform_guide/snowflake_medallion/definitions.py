from dagster import Definitions, EnvVar

from data_platform_architecture.data_platform_guide.snowflake_medallion.defs.resources import (
    SnowflakeResource,
    create_dbt_resource,
)

definitions = Definitions(
    assets=[],
    resources={
        "snowflake": SnowflakeResource(
            account=EnvVar("SNOWFLAKE_ACCOUNT").get_value() or "",
            user=EnvVar("SNOWFLAKE_USER").get_value() or "",
            password=EnvVar("SNOWFLAKE_PASSWORD").get_value() or "",
            warehouse=EnvVar("SNOWFLAKE_WAREHOUSE").get_value() or "",
            database=EnvVar("SNOWFLAKE_DATABASE").get_value() or "",
            db_schema=EnvVar("SNOWFLAKE_SCHEMA").get_value() or "PUBLIC",
            demo_mode=not bool(EnvVar("SNOWFLAKE_ACCOUNT").get_value()),
        ),
        "dbt": create_dbt_resource(demo_mode=not bool(EnvVar("SNOWFLAKE_ACCOUNT").get_value())),
    },
)
