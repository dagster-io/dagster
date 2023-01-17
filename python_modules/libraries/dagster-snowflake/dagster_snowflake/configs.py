from dagster import Bool, Field, IntSource, StringSource


def define_snowflake_config():
    """Snowflake configuration.

    See the Snowflake documentation for reference:
        https://docs.snowflake.net/manuals/user-guide/python-connector-api.html
    """
    account = Field(
        StringSource,
        description="Your Snowflake account name. For more details, see  https://bit.ly/2FBL320.",
        is_required=False,
    )

    user = Field(StringSource, description="User login name.", is_required=True)

    password = Field(StringSource, description="User password.", is_required=False)

    database = Field(
        StringSource,
        description=(
            "Name of the default database to use. After login, you can use USE DATABASE "
            " to change the database."
        ),
        is_required=False,
    )

    schema = Field(
        StringSource,
        description=(
            "Name of the default schema to use. After login, you can use USE SCHEMA to "
            "change the schema."
        ),
        is_required=False,
    )

    role = Field(
        StringSource,
        description=(
            "Name of the default role to use. After login, you can use USE ROLE to change "
            " the role."
        ),
        is_required=False,
    )

    warehouse = Field(
        StringSource,
        description=(
            "Name of the default warehouse to use. After login, you can use USE WAREHOUSE "
            "to change the role."
        ),
        is_required=False,
    )

    private_key = Field(
        StringSource,
        description=(
            "Raw private key to use. See"
            " https://docs.snowflake.com/en/user-guide/key-pair-auth.html for details. Alternately,"
            " set private_key_path and private_key_password."
        ),
        is_required=False,
    )

    private_key_password = Field(
        StringSource,
        description=(
            "Raw private key password to use. See"
            " https://docs.snowflake.com/en/user-guide/key-pair-auth.html for details. Required for"
            " both private_key and private_key_path."
        ),
        is_required=False,
    )

    private_key_path = Field(
        StringSource,
        description=(
            "Raw private key path to use. See"
            " https://docs.snowflake.com/en/user-guide/key-pair-auth.html for details. Alternately,"
            " set the raw private key as private_key."
        ),
        is_required=False,
    )

    autocommit = Field(
        Bool,
        description=(
            "None by default, which honors the Snowflake parameter AUTOCOMMIT. Set to True "
            "or False to enable or disable autocommit mode in the session, respectively."
        ),
        is_required=False,
    )

    client_prefetch_threads = Field(
        IntSource,
        description=(
            "Number of threads used to download the results sets (4 by default). "
            "Increasing the value improves fetch performance but requires more memory."
        ),
        is_required=False,
    )

    client_session_keep_alive = Field(
        StringSource,
        description=(
            "False by default. Set this to True to keep the session active indefinitely, "
            "even if there is no activity from the user. Make certain to call the close method to "
            "terminate the thread properly or the process may hang."
        ),
        is_required=False,
    )

    login_timeout = Field(
        IntSource,
        description=(
            "Timeout in seconds for login. By default, 60 seconds. The login request gives "
            'up after the timeout length if the HTTP response is "success".'
        ),
        is_required=False,
    )

    network_timeout = Field(
        IntSource,
        description=(
            "Timeout in seconds for all other operations. By default, none/infinite. A general"
            " request gives up after the timeout length if the HTTP response is not 'success'."
        ),
        is_required=False,
    )

    ocsp_response_cache_filename = Field(
        StringSource,
        description=(
            "URI for the OCSP response cache file.  By default, the OCSP response cache "
            "file is created in the cache directory."
        ),
        is_required=False,
    )

    validate_default_parameters = Field(
        Bool,
        description=(
            "False by default. Raise an exception if either one of specified database, "
            "schema or warehouse doesn't exists if True."
        ),
        is_required=False,
    )

    paramstyle = Field(
        # TODO should validate only against permissible values for this
        StringSource,
        description=(
            "pyformat by default for client side binding. Specify qmark or numeric to "
            "change bind variable formats for server side binding."
        ),
        is_required=False,
    )

    timezone = Field(
        StringSource,
        description=(
            "None by default, which honors the Snowflake parameter TIMEZONE. Set to a "
            "valid time zone (e.g. America/Los_Angeles) to set the session time zone."
        ),
        is_required=False,
    )

    connector = Field(
        StringSource,
        description=(
            "Indicate alternative database connection engine. Permissible option is "
            "'sqlalchemy' otherwise defaults to use the Snowflake Connector for Python."
        ),
        is_required=False,
    )

    cache_column_metadata = Field(
        StringSource,
        description=(
            "Optional parameter when connector is set to sqlalchemy. Snowflake SQLAlchemy takes a"
            " flag cache_column_metadata=True such that all of column metadata for all tables are"
            ' "cached"'
        ),
        is_required=False,
    )

    numpy = Field(
        StringSource,
        description=(
            "Optional parameter when connector is set to sqlalchemy. To enable fetching "
            "NumPy data types, add numpy=True to the connection parameters."
        ),
        is_required=False,
    )

    authenticator = Field(
        StringSource,
        description="Optional parameter to specify the authentication mechanism to use.",
        is_required=False,
    )

    return {
        "account": account,
        "user": user,
        "password": password,
        "database": database,
        "schema": schema,
        "role": role,
        "warehouse": warehouse,
        "autocommit": autocommit,
        "private_key": private_key,
        "private_key_password": private_key_password,
        "private_key_path": private_key_path,
        "client_prefetch_threads": client_prefetch_threads,
        "client_session_keep_alive": client_session_keep_alive,
        "login_timeout": login_timeout,
        "network_timeout": network_timeout,
        "ocsp_response_cache_filename": ocsp_response_cache_filename,
        "validate_default_parameters": validate_default_parameters,
        "paramstyle": paramstyle,
        "timezone": timezone,
        "connector": connector,
        "cache_column_metadata": cache_column_metadata,
        "numpy": numpy,
        "authenticator": authenticator,
    }
