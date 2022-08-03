from dagster import op, job
from dagster_snowflake import snowflake_resource


@op(required_resource_keys={'snowflake'})
def get_one(context):
    context.resources.snowflake.execute_query('SELECT 1')


@job(resource_defs={'snowflake': snowflake_resource})
def my_snowflake_job():
    get_one()


my_snowflake_job.execute_in_process(
    run_config={
        'resources': {
            'snowflake': {
                'config': {
                    'account': "abc1234.us-east-1",
                    'user': {'env': 'SYSTEM_SNOWFLAKE_USER'},
                    'password': {'env': 'SYSTEM_SNOWFLAKE_PASSWORD'},
                    'database': "PRODUCTION",
                    'schema': "ANALYTICS",
                }
            }
        }
    }
)
