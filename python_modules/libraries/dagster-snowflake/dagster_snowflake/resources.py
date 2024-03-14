import base64
import sys
import warnings
from contextlib import closing, contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Union

import dagster._check as check
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from dagster import (
    ConfigurableResource,
    IAttachDifferentObjectToOpContext,
    get_dagster_logger,
    resource,
)
from dagster._annotations import public
from dagster._config.pythonic_config.pydantic_compat_layer import compat_model_validator
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._core.storage.event_log.sql_event_log import SqlDbConnection
from dagster._utils.cached_method import cached_method
from pydantic import Field, validator

try:
    import snowflake.connector
except ImportError:
    msg = (
        "Could not import snowflake.connector. This could mean you have an incompatible version "
        "of azure-storage-blob installed. dagster-snowflake requires azure-storage-blob<12.0.0; "
        "this conflicts with dagster-azure which requires azure-storage-blob~=12.0.0 and is "
        "incompatible with dagster-snowflake. Please uninstall dagster-azure and reinstall "
        "dagster-snowflake to fix this error."
    )
    warnings.warn(msg)
    raise


class SnowflakeResource(ConfigurableResource, IAttachDifferentObjectToOpContext):
    """A resource for connecting to the Snowflake data warehouse.

    If connector configuration is not set, SnowflakeResource.get_connection() will return a
    `snowflake.connector.Connection <https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-api#object-connection>`__
    object. If connector="sqlalchemy" configuration is set, then SnowflakeResource.get_connection() will
    return a `SQLAlchemy Connection <https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Connection>`__
    or a `SQLAlchemy raw connection <https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Engine.raw_connection>`__.

    A simple example of loading data into Snowflake and subsequently querying that data is shown below:

    Examples:
        .. code-block:: python

            from dagster import job, op
            from dagster_snowflake import SnowflakeResource

            @op
            def get_one(snowflake_resource: SnowflakeResource):
                with snowflake_resource.get_connection() as conn:
                    # conn is a snowflake.connector.Connection object
                    conn.cursor().execute("SELECT 1")

            @job
            def my_snowflake_job():
                get_one()

            my_snowflake_job.execute_in_process(
                resources={
                    'snowflake_resource': SnowflakeResource(
                        account=EnvVar("SNOWFLAKE_ACCOUNT"),
                        user=EnvVar("SNOWFLAKE_USER"),
                        password=EnvVar("SNOWFLAKE_PASSWORD")
                        database="MY_DATABASE",
                        schema="MY_SCHEMA",
                        warehouse="MY_WAREHOUSE"
                    )
                }
            )
    """

    account: Optional[str] = Field(
        default=None,
        description=(
            "Your Snowflake account name. For more details, see the `Snowflake documentation."
            " <https://docs.snowflake.com/developer-guide/python-connector/python-connector-api>`__"
        ),
    )

    user: str = Field(description="User login name.")

    password: Optional[str] = Field(default=None, description="User password.")

    database: Optional[str] = Field(
        default=None,
        description=(
            "Name of the default database to use. After login, you can use ``USE DATABASE`` "
            " to change the database."
        ),
    )

    schema_: Optional[str] = Field(
        default=None,
        description=(
            "Name of the default schema to use. After login, you can use ``USE SCHEMA`` to "
            "change the schema."
        ),
        alias="schema",
    )  # schema is a reserved word for pydantic

    role: Optional[str] = Field(
        default=None,
        description=(
            "Name of the default role to use. After login, you can use ``USE ROLE`` to change "
            " the role."
        ),
    )

    warehouse: Optional[str] = Field(
        default=None,
        description=(
            "Name of the default warehouse to use. After login, you can use ``USE WAREHOUSE`` "
            "to change the role."
        ),
    )

    private_key: Optional[str] = Field(
        default=None,
        description=(
            "Raw private key to use. See the `Snowflake documentation"
            " <https://docs.snowflake.com/en/user-guide/key-pair-auth.html>`__ for details."
            " Alternately, set private_key_path and private_key_password. To avoid issues with"
            " newlines in the keys, you can base64 encode the key. You can retrieve the base64"
            " encoded key with this shell command: ``cat rsa_key.p8 | base64``"
        ),
    )

    private_key_password: Optional[str] = Field(
        default=None,
        description=(
            "Raw private key password to use. See the `Snowflake documentation"
            " <https://docs.snowflake.com/en/user-guide/key-pair-auth.html>`__ for details."
            " Required for both ``private_key`` and ``private_key_path`` if the private key is"
            " encrypted. For unencrypted keys, this config can be omitted or set to None."
        ),
    )

    private_key_path: Optional[str] = Field(
        default=None,
        description=(
            "Raw private key path to use. See the `Snowflake documentation"
            " <https://docs.snowflake.com/en/user-guide/key-pair-auth.html>`__ for details."
            " Alternately, set the raw private key as ``private_key``."
        ),
    )

    autocommit: Optional[bool] = Field(
        default=None,
        description=(
            "None by default, which honors the Snowflake parameter AUTOCOMMIT. Set to True "
            "or False to enable or disable autocommit mode in the session, respectively."
        ),
    )

    client_prefetch_threads: Optional[int] = Field(
        default=None,
        description=(
            "Number of threads used to download the results sets (4 by default). "
            "Increasing the value improves fetch performance but requires more memory."
        ),
    )

    client_session_keep_alive: Optional[bool] = Field(
        default=None,
        description=(
            "False by default. Set this to True to keep the session active indefinitely, "
            "even if there is no activity from the user. Make certain to call the close method to "
            "terminate the thread properly or the process may hang."
        ),
    )

    login_timeout: Optional[int] = Field(
        default=None,
        description=(
            "Timeout in seconds for login. By default, 60 seconds. The login request gives "
            'up after the timeout length if the HTTP response is "success".'
        ),
    )

    network_timeout: Optional[int] = Field(
        default=None,
        description=(
            "Timeout in seconds for all other operations. By default, none/infinite. A general"
            " request gives up after the timeout length if the HTTP response is not 'success'."
        ),
    )

    ocsp_response_cache_filename: Optional[str] = Field(
        default=None,
        description=(
            "URI for the OCSP response cache file.  By default, the OCSP response cache "
            "file is created in the cache directory."
        ),
    )

    validate_default_parameters: Optional[bool] = Field(
        default=None,
        description=(
            "If True, raise an exception if the warehouse, database, or schema doesn't exist."
            " Defaults to False."
        ),
    )

    paramstyle: Optional[str] = Field(
        default=None,
        description=(
            "pyformat by default for client side binding. Specify qmark or numeric to "
            "change bind variable formats for server side binding."
        ),
    )

    timezone: Optional[str] = Field(
        default=None,
        description=(
            "None by default, which honors the Snowflake parameter TIMEZONE. Set to a "
            "valid time zone (e.g. America/Los_Angeles) to set the session time zone."
        ),
    )

    connector: Optional[str] = Field(
        default=None,
        description=(
            "Indicate alternative database connection engine. Permissible option is "
            "'sqlalchemy' otherwise defaults to use the Snowflake Connector for Python."
        ),
        is_required=False,
    )

    cache_column_metadata: Optional[str] = Field(
        default=None,
        description=(
            "Optional parameter when connector is set to sqlalchemy. Snowflake SQLAlchemy takes a"
            " flag ``cache_column_metadata=True`` such that all of column metadata for all tables"
            ' are "cached"'
        ),
    )

    numpy: Optional[bool] = Field(
        default=None,
        description=(
            "Optional parameter when connector is set to sqlalchemy. To enable fetching "
            "NumPy data types, add numpy=True to the connection parameters."
        ),
    )

    authenticator: Optional[str] = Field(
        default=None,
        description="Optional parameter to specify the authentication mechanism to use.",
    )

    @validator("paramstyle")
    def validate_paramstyle(cls, v: Optional[str]) -> Optional[str]:
        valid_config = ["pyformat", "qmark", "numeric"]
        if v is not None and v not in valid_config:
            raise ValueError(
                "Snowflake Resource: 'paramstyle' configuration value must be one of:"
                f" {','.join(valid_config)}."
            )
        return v

    @validator("connector")
    def validate_connector(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "sqlalchemy":
            raise ValueError(
                "Snowflake Resource: 'connector' configuration value must be None or sqlalchemy."
            )
        return v

    @compat_model_validator(mode="before")
    def validate_authentication(cls, values):
        auths_set = 0
        auths_set += 1 if values.get("password") is not None else 0
        auths_set += 1 if values.get("private_key") is not None else 0
        auths_set += 1 if values.get("private_key_path") is not None else 0

        # if authenticator is set, there can be 0 or 1 additional auth method;
        # otherwise, ensure at least 1 method is provided
        check.invariant(
            auths_set > 0 or values.get("authenticator") is not None,
            "Missing config: Password, private key, or authenticator authentication required"
            " for Snowflake resource.",
        )

        # ensure that only 1 non-authenticator method is provided
        check.invariant(
            auths_set <= 1,
            "Incorrect config: Cannot provide both password and private key authentication to"
            " Snowflake Resource.",
        )

        return values

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @property
    @cached_method
    def _connection_args(self) -> Mapping[str, Any]:
        conn_args = {
            k: self._resolved_config_dict.get(k)
            for k in (
                "account",
                "user",
                "password",
                "database",
                "schema",
                "role",
                "warehouse",
                "autocommit",
                "client_prefetch_threads",
                "client_session_keep_alive",
                "login_timeout",
                "network_timeout",
                "ocsp_response_cache_filename",
                "validate_default_parameters",
                "paramstyle",
                "timezone",
                "authenticator",
            )
            if self._resolved_config_dict.get(k) is not None
        }
        if (
            self._resolved_config_dict.get("private_key", None) is not None
            or self._resolved_config_dict.get("private_key_path", None) is not None
        ):
            conn_args["private_key"] = self._snowflake_private_key(self._resolved_config_dict)

        return conn_args

    @property
    @cached_method
    def _sqlalchemy_connection_args(self) -> Mapping[str, Any]:
        conn_args: Dict[str, Any] = {
            k: self._resolved_config_dict.get(k)
            for k in (
                "account",
                "user",
                "password",
                "database",
                "schema",
                "role",
                "warehouse",
                "cache_column_metadata",
                "numpy",
            )
            if self._resolved_config_dict.get(k) is not None
        }

        return conn_args

    @property
    @cached_method
    def _sqlalchemy_engine_args(self) -> Mapping[str, Any]:
        config = self._resolved_config_dict
        sqlalchemy_engine_args = {}
        if (
            config.get("private_key", None) is not None
            or config.get("private_key_path", None) is not None
        ):
            # sqlalchemy passes private key args separately, so store them in a new dict
            sqlalchemy_engine_args["private_key"] = self._snowflake_private_key(config)
        if config.get("authenticator", None) is not None:
            sqlalchemy_engine_args["authenticator"] = config["authenticator"]

        return sqlalchemy_engine_args

    def _snowflake_private_key(self, config) -> bytes:
        # If the user has defined a path to a private key, we will use that.
        if config.get("private_key_path", None) is not None:
            # read the file from the path.
            with open(config.get("private_key_path"), "rb") as key:
                private_key = key.read()
        else:
            private_key = config.get("private_key", None)

        kwargs = {}
        if config.get("private_key_password", None) is not None:
            kwargs["password"] = config["private_key_password"].encode()
        else:
            kwargs["password"] = None

        try:
            p_key = serialization.load_pem_private_key(
                private_key, backend=default_backend(), **kwargs
            )
        except TypeError:
            try:
                private_key = base64.b64decode(private_key)
                p_key = serialization.load_pem_private_key(
                    private_key, backend=default_backend(), **kwargs
                )
            except ValueError:
                raise ValueError(
                    "Unable to load private key. You may need to base64 encode your private key."
                    " You can retrieve the base64 encoded key with this shell command: cat"
                    " rsa_key.p8 | base64"
                )

        pkb = p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        return pkb

    @public
    @contextmanager
    def get_connection(
        self, raw_conn: bool = True
    ) -> Iterator[Union[SqlDbConnection, snowflake.connector.SnowflakeConnection]]:
        """Gets a connection to Snowflake as a context manager.

        If connector configuration is not set, SnowflakeResource.get_connection() will return a
        `snowflake.connector.Connection <https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-api#object-connection>`__
        If connector="sqlalchemy" configuration is set, then SnowflakeResource.get_connection() will
        return a `SQLAlchemy Connection <https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Connection>`__
        or a `SQLAlchemy raw connection <https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Engine.raw_connection>`__
        if raw_conn=True.


        Args:
            raw_conn (bool): If using the sqlalchemy connector, you can set raw_conn to True to create a raw
                connection. Defaults to True.

        Examples:
            .. code-block:: python

                @op
                def get_query_status(snowflake: SnowflakeResource, query_id):
                    with snowflake.get_connection() as conn:
                        # conn is a Snowflake Connection object or a SQLAlchemy Connection if
                        # sqlalchemy is specified as the connector in the Snowflake Resource config

                        return conn.get_query_status(query_id)

        """
        if self.connector == "sqlalchemy":
            from snowflake.sqlalchemy import URL
            from sqlalchemy import create_engine

            engine = create_engine(
                URL(**self._sqlalchemy_connection_args), connect_args=self._sqlalchemy_engine_args
            )
            conn = engine.raw_connection() if raw_conn else engine.connect()

            yield conn
            conn.close()
            engine.dispose()
        else:
            conn = snowflake.connector.connect(**self._connection_args)

            yield conn
            if not self.autocommit:
                conn.commit()
            conn.close()

    def get_object_to_set_on_execution_context(self) -> Any:
        # Directly create a SnowflakeConnection here for backcompat since the SnowflakeConnection
        # has methods this resource does not have
        return SnowflakeConnection(
            config=self._resolved_config_dict,
            log=get_dagster_logger(),
            snowflake_connection_resource=self,
        )


class SnowflakeConnection:
    """A connection to Snowflake that can execute queries. In general this class should not be
    directly instantiated, but rather used as a resource in an op or asset via the
    :py:func:`snowflake_resource`.

    Note that the SnowflakeConnection is only used by the snowflake_resource. The Pythonic SnowflakeResource does
    not use this SnowflakeConnection class.
    """

    def __init__(
        self, config: Mapping[str, str], log, snowflake_connection_resource: SnowflakeResource
    ):
        self.snowflake_connection_resource = snowflake_connection_resource
        self.log = log

    @public
    @contextmanager
    def get_connection(
        self, raw_conn: bool = True
    ) -> Iterator[Union[SqlDbConnection, snowflake.connector.SnowflakeConnection]]:
        """Gets a connection to Snowflake as a context manager.

        If using the execute_query, execute_queries, or load_table_from_local_parquet methods,
        you do not need to create a connection using this context manager.

        Args:
            raw_conn (bool): If using the sqlalchemy connector, you can set raw_conn to True to create a raw
                connection. Defaults to True.

        Examples:
            .. code-block:: python

                @op(
                    required_resource_keys={"snowflake"}
                )
                def get_query_status(query_id):
                    with context.resources.snowflake.get_connection() as conn:
                        # conn is a Snowflake Connection object or a SQLAlchemy Connection if
                        # sqlalchemy is specified as the connector in the Snowflake Resource config

                        return conn.get_query_status(query_id)

        """
        with self.snowflake_connection_resource.get_connection(raw_conn=raw_conn) as conn:
            yield conn

    @public
    def execute_query(
        self,
        sql: str,
        parameters: Optional[Union[Sequence[Any], Mapping[Any, Any]]] = None,
        fetch_results: bool = False,
        use_pandas_result: bool = False,
    ):
        """Execute a query in Snowflake.

        Args:
            sql (str): the query to be executed
            parameters (Optional[Union[Sequence[Any], Mapping[Any, Any]]]): Parameters to be passed to the query. See the
                `Snowflake documentation <https://docs.snowflake.com/en/user-guide/python-connector-example.html#binding-data>`__
                for more information.
            fetch_results (bool): If True, will return the result of the query. Defaults to False. If True
                and use_pandas_result is also True, results will be returned as a Pandas DataFrame.
            use_pandas_result (bool): If True, will return the result of the query as a Pandas DataFrame.
                Defaults to False. If fetch_results is False and use_pandas_result is True, an error will be
                raised.

        Returns:
            The result of the query if fetch_results or use_pandas_result is True, otherwise returns None

        Examples:
            .. code-block:: python

                @op
                def drop_database(snowflake: SnowflakeResource):
                    snowflake.execute_query(
                        "DROP DATABASE IF EXISTS MY_DATABASE"
                    )
        """
        check.str_param(sql, "sql")
        check.opt_inst_param(parameters, "parameters", (list, dict))
        check.bool_param(fetch_results, "fetch_results")
        if not fetch_results and use_pandas_result:
            check.failed("If use_pandas_result is True, fetch_results must also be True.")

        with self.get_connection() as conn:
            with closing(conn.cursor()) as cursor:
                if sys.version_info[0] < 3:
                    sql = sql.encode("utf-8")

                self.log.info("Executing query: " + sql)
                parameters = dict(parameters) if isinstance(parameters, Mapping) else parameters
                cursor.execute(sql, parameters)
                if use_pandas_result:
                    return cursor.fetch_pandas_all()
                if fetch_results:
                    return cursor.fetchall()

    @public
    def execute_queries(
        self,
        sql_queries: Sequence[str],
        parameters: Optional[Union[Sequence[Any], Mapping[Any, Any]]] = None,
        fetch_results: bool = False,
        use_pandas_result: bool = False,
    ) -> Optional[Sequence[Any]]:
        """Execute multiple queries in Snowflake.

        Args:
            sql_queries (str): List of queries to be executed in series
            parameters (Optional[Union[Sequence[Any], Mapping[Any, Any]]]): Parameters to be passed to every query. See the
                `Snowflake documentation <https://docs.snowflake.com/en/user-guide/python-connector-example.html#binding-data>`__
                for more information.
            fetch_results (bool): If True, will return the results of the queries as a list. Defaults to False. If True
                and use_pandas_result is also True, results will be returned as Pandas DataFrames.
            use_pandas_result (bool): If True, will return the results of the queries as a list of a Pandas DataFrames.
                Defaults to False. If fetch_results is False and use_pandas_result is True, an error will be
                raised.

        Returns:
            The results of the queries as a list if fetch_results or use_pandas_result is True,
            otherwise returns None

        Examples:
            .. code-block:: python

                @op
                def create_fresh_database(snowflake: SnowflakeResource):
                    queries = ["DROP DATABASE IF EXISTS MY_DATABASE", "CREATE DATABASE MY_DATABASE"]
                    snowflake.execute_queries(
                        sql_queries=queries
                    )

        """
        check.sequence_param(sql_queries, "sql_queries", of_type=str)
        check.opt_inst_param(parameters, "parameters", (list, dict))
        check.bool_param(fetch_results, "fetch_results")
        if not fetch_results and use_pandas_result:
            check.failed("If use_pandas_result is True, fetch_results must also be True.")

        results: List[Any] = []
        with self.get_connection() as conn:
            with closing(conn.cursor()) as cursor:
                for raw_sql in sql_queries:
                    sql = raw_sql.encode("utf-8") if sys.version_info[0] < 3 else raw_sql
                    self.log.info("Executing query: " + sql)
                    parameters = dict(parameters) if isinstance(parameters, Mapping) else parameters
                    cursor.execute(sql, parameters)
                    if use_pandas_result:
                        results = results.append(cursor.fetch_pandas_all())  # type: ignore
                    elif fetch_results:
                        results.append(cursor.fetchall())

        return results if len(results) > 0 else None

    @public
    def load_table_from_local_parquet(self, src: str, table: str):
        """Stores the content of a parquet file to a Snowflake table.

        Args:
            src (str): the name of the file to store in Snowflake
            table (str): the name of the table to store the data. If the table does not exist, it will
                be created. Otherwise the contents of the table will be replaced with the data in src

        Examples:
            .. code-block:: python

                import pandas as pd
                import pyarrow as pa
                import pyarrow.parquet as pq

                @op
                def write_parquet_file(snowflake: SnowflakeResource):
                    df = pd.DataFrame({"one": [1, 2, 3], "ten": [11, 12, 13]})
                    table = pa.Table.from_pandas(df)
                    pq.write_table(table, "example.parquet')
                    snowflake.load_table_from_local_parquet(
                        src="example.parquet",
                        table="MY_TABLE"
                    )

        """
        check.str_param(src, "src")
        check.str_param(table, "table")

        sql_queries = [
            f"CREATE OR REPLACE TABLE {table} ( data VARIANT DEFAULT NULL);",
            "CREATE OR REPLACE FILE FORMAT parquet_format TYPE = 'parquet';",
            f"PUT {src} @%{table};",
            f"COPY INTO {table} FROM @%{table} FILE_FORMAT = (FORMAT_NAME = 'parquet_format');",
        ]

        self.execute_queries(sql_queries)


@dagster_maintained_resource
@resource(
    config_schema=SnowflakeResource.to_config_schema(),
    description="This resource is for connecting to the Snowflake data warehouse",
)
def snowflake_resource(context) -> SnowflakeConnection:
    """A resource for connecting to the Snowflake data warehouse. The returned resource object is an
    instance of :py:class:`SnowflakeConnection`.

    A simple example of loading data into Snowflake and subsequently querying that data is shown below:

    Examples:
        .. code-block:: python

            from dagster import job, op
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
                                'account': {'env': 'SNOWFLAKE_ACCOUNT'},
                                'user': {'env': 'SNOWFLAKE_USER'},
                                'password': {'env': 'SNOWFLAKE_PASSWORD'},
                                'database': {'env': 'SNOWFLAKE_DATABASE'},
                                'schema': {'env': 'SNOWFLAKE_SCHEMA'},
                                'warehouse': {'env': 'SNOWFLAKE_WAREHOUSE'},
                            }
                        }
                    }
                }
            )
    """
    snowflake_resource = SnowflakeResource.from_resource_context(context)
    return SnowflakeConnection(
        config=context, log=context.log, snowflake_connection_resource=snowflake_resource
    )


def fetch_last_updated_timestamps(
    *,
    snowflake_connection: Union[SqlDbConnection, snowflake.connector.SnowflakeConnection],
    schema: str,
    tables: Sequence[str],
    database: Optional[str] = None,
) -> Mapping[str, datetime]:
    """Fetch the last updated times of a list of tables in Snowflake.

    If the underlying query to fetch the last updated time returns no results, a ValueError will be raised.

    Args:
        snowflake_connection (Union[SqlDbConnection, SnowflakeConnection]): A connection to Snowflake.
            Accepts either a SnowflakeConnection or a sqlalchemy connection object,
            which are the two types of connections emittable from the snowflake resource.
        schema (str): The schema of the tables to fetch the last updated time for.
        tables (Sequence[str]): A list of table names to fetch the last updated time for.
        database (Optional[str]): The database of the table. Only required if the connection
            has not been set with a database.

    Returns:
        Mapping[str, datetime]: A dictionary of table names to their last updated time in UTC.
    """
    check.invariant(len(tables) > 0, "Must provide at least one table name to query upon.")
    tables_str = ", ".join([f"'{table_name}'" for table_name in tables])
    fully_qualified_table_name = (
        f"{database}.information_schema.tables" if database else "information_schema.tables"
    )

    query = f"""
    SELECT table_name, CONVERT_TIMEZONE('UTC', last_altered) AS last_altered 
    FROM {fully_qualified_table_name}
    WHERE table_schema = '{schema}' AND table_name IN ({tables_str});
    """
    result = snowflake_connection.cursor().execute(query)
    if not result:
        raise ValueError("No results returned from Snowflake update time query.")

    last_updated_times = {}
    for table_name, last_altered in result:
        check.invariant(
            isinstance(last_altered, datetime),
            "Expected last_altered to be a datetime, but it was not.",
        )
        last_updated_times[table_name] = last_altered

    for table_name in tables:
        if table_name not in last_updated_times:
            raise ValueError(f"Table {table_name} does not exist in Snowflake.")

    return last_updated_times
