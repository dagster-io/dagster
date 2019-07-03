# dagster-slack

##Introduction
This library provides an integration with the [Snowflake](https://www.snowflake.com/) data warehouse.

Presently, it provides two solids for interacting with Snowflake, `SnowflakeSolidDefinition` for issuing SQL queries, and `SnowflakeLoadSolidDefinition` for loading Parquet files into Snowflake.

Both of these solids depend on `snowflake_resource`, which is a Dagster resource for configuring Snowflake connections.

## Getting Started
To use this library, you should first ensure that you have an appropriate [Snowflake user](https://docs.snowflake.net/manuals/user-guide/admin-user-management.html) configured to access your data warehouse.

A simple example of loading data into Snowflake and subsequently querying that data is shown below:

```
from dagster import execute_pipeline, DependencyDefinition, ModeDefinition, PipelineDefinition
from dagster_snowflake import (
    snowflake_resource,
    SnowflakeLoadSolidDefinition,
    SnowflakeSolidDefinition,
)

snowflake_load = SnowflakeLoadSolidDefinition(
    'load some parquet data', src='file:///tmp/mydata/*.parquet', table='mydata'
)

snowflake_query = SnowflakeSolidDefinition('query some data', ['SELECT * FROM mydata'])

pipeline = PipelineDefinition(
    name='snowflake example',
    solids=[snowflake_load, snowflake_query],
    mode_defs=[ModeDefinition(resource_defs={'snowflake': snowflake_resource})],
    dependencies={snowflake_query: {'start': DependencyDefinition('snowflake_load')}},
)

result = execute_pipeline(
    pipeline,
    {
        'resources': {
            'snowflake': {
                'config': {
                    'account': 'foo',
                    'user': 'bar',
                    'password': 'baz',
                    'database': 'TESTDB',
                    'schema': 'TESTSCHEMA',
                    'warehouse': 'TINY_WAREHOUSE',
                }
            }
        }
    },
)
```
