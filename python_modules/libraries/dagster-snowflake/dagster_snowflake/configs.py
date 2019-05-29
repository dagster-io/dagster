from dagster import Bool, Dict, Field, Int, Path, String


def define_snowflake_config():
    '''Snowflake configuration.

    See the Snowflake documentation for reference:
        https://docs.snowflake.net/manuals/user-guide/python-connector-api.html
    '''

    account = Field(
        String,
        description='Your Snowflake account name. For more details, see  https://bit.ly/2FBL320.',
        is_optional=True,
    )

    user = Field(String, description='User login name.', is_optional=False)

    password = Field(String, description='User password.', is_optional=False)

    database = Field(
        String,
        description='''Name of the default database to use. After login, you can use USE DATABASE
         to change the database.''',
        is_optional=True,
    )

    schema = Field(
        String,
        description='''Name of the default schema to use. After login, you can use USE SCHEMA to
         change the schema.''',
        is_optional=True,
    )

    role = Field(
        String,
        description='''Name of the default role to use. After login, you can use USE ROLE to change
         the role.''',
        is_optional=True,
    )

    warehouse = Field(
        String,
        description='''Name of the default warehouse to use. After login, you can use USE WAREHOUSE
         to change the role.''',
        is_optional=True,
    )

    autocommit = Field(
        Bool,
        description='''None by default, which honors the Snowflake parameter AUTOCOMMIT. Set to True
         or False to enable or disable autocommit mode in the session, respectively.''',
        is_optional=True,
    )

    client_prefetch_threads = Field(
        Int,
        description='''Number of threads used to download the results sets (4 by default).
         Increasing the value improves fetch performance but requires more memory.''',
        is_optional=True,
    )

    client_session_keep_alive = Field(
        String,
        description='''False by default. Set this to True to keep the session active indefinitely,
         even if there is no activity from the user. Make certain to call the close method to
         terminate the thread properly or the process may hang.''',
        is_optional=True,
    )

    login_timeout = Field(
        Int,
        description='''Timeout in seconds for login. By default, 60 seconds. The login request gives
         up after the timeout length if the HTTP response is "success".''',
        is_optional=True,
    )

    network_timeout = Field(
        Int,
        description='''Timeout in seconds for all other operations. By default, none/infinite. A
         general request gives up after the timeout length if the HTTP response is not "success"''',
        is_optional=True,
    )

    ocsp_response_cache_filename = Field(
        Path,
        description='''URI for the OCSP response cache file.
         By default, the OCSP response cache file is created in the cache directory.''',
        is_optional=True,
    )

    validate_default_parameters = Field(
        Bool,
        description='''False by default. Raise an exception if either one of specified database,
         schema or warehouse doesn't exists if True.''',
        is_optional=True,
    )

    paramstyle = Field(
        # TODO should validate only against permissible values for this
        String,
        description='''pyformat by default for client side binding. Specify qmark or numeric to
        change bind variable formats for server side binding.''',
        is_optional=True,
    )

    timezone = Field(
        String,
        description='''None by default, which honors the Snowflake parameter TIMEZONE. Set to a
         valid time zone (e.g. America/Los_Angeles) to set the session time zone.''',
        is_optional=True,
    )

    return Field(
        Dict(
            fields={
                'account': account,
                'user': user,
                'password': password,
                'database': database,
                'schema': schema,
                'role': role,
                'warehouse': warehouse,
                'autocommit': autocommit,
                'client_prefetch_threads': client_prefetch_threads,
                'client_session_keep_alive': client_session_keep_alive,
                'login_timeout': login_timeout,
                'network_timeout': network_timeout,
                'ocsp_response_cache_filename': ocsp_response_cache_filename,
                'validate_default_parameters': validate_default_parameters,
                'paramstyle': paramstyle,
                'timezone': timezone,
            }
        ),
        description='Snowflake configuration',
    )
