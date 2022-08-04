from dagster import op, job, resource


@resource
def database_client():
    ...


# start_database_example


@op(required_resource_keys={'database'})
def get_one(context):
    context.resources.database.execute_query('SELECT 1')


@job(resource_defs={'database': database_client})
def get_one_from_db():
    get_one()


get_one_from_db.execute_in_process(
    run_config={
        'resources': {
            'database': {
                'config': {
                    'username': {'env': 'SYSTEM_USER'},
                    'password': {'env': 'SYSTEM_PASSWORD'},
                    'hostname': 'abccompany',
                    'db_name': 'PRODUCTION',
                    'port': '5432',
                }
            }
        }
    }
)

# end_database_example
