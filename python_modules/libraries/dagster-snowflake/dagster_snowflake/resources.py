import sys
import warnings
from contextlib import closing, contextmanager
from typing import Mapping

import dagster._check as check
from dagster import resource
from dagster._annotations import public

from .configs import define_snowflake_config

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


class SnowflakeConnection:
    """A connection to Snowflake that can execute queries. In general this class should not be
    directly instantiated, but rather used as a resource in an op or asset via the :py:func:`snowflake_resource`.
    """

    def __init__(self, config: Mapping[str, str], log):  # pylint: disable=too-many-locals
        # Extract parameters from resource config. Note that we can't pass None values to
        # snowflake.connector.connect() because they will override the default values set within the
        # connector; remove them from the conn_args dict.
        self.connector = config.get("connector", None)

        if self.connector == "sqlalchemy":
            self.conn_args = {
                k: config.get(k)
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
                if config.get(k) is not None
            }

        else:
            self.conn_args = {
                k: config.get(k)
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
                if config.get(k) is not None
            }

        self.autocommit = self.conn_args.get("autocommit", False)
        self.log = log

    @public
    @contextmanager
    def get_connection(self, raw_conn=True):
        """Gets a connection to Snowflake as a context manager.

        If using the execute_query, execute_queries, or load_table_from_local_parquet methods,
        you do not need to create a
        connection using this context manager.

        Args:
            raw_conn: If using the sqlalchemy connector, set raw_conn to True to create a raw
                connection. Defaults to True.

        """
        if self.connector == "sqlalchemy":
            from snowflake.sqlalchemy import URL  # pylint: disable=no-name-in-module,import-error
            from sqlalchemy import create_engine

            engine = create_engine(URL(**self.conn_args))
            conn = engine.raw_connection() if raw_conn else engine.connect()

            yield conn
            conn.close()
            engine.dispose()
        else:
            conn = snowflake.connector.connect(**self.conn_args)

            yield conn
            if not self.autocommit:
                conn.commit()
            conn.close()

    @public
    def execute_query(self, sql, parameters=None, fetch_results=False, use_pandas_result=False):
        """Execute a query in Snowflake.

        Args:
            sql: the query to be executed
            parameters: parameters to be passed to the query
            fetch_results: If True, will return the result of the query. Defaults to False
            use_pandas_result: If True, will return the result of the query as a Pandas DataFrame.
                Defaults to False

        Returns:
            The result of the query if fetch_results or use_pandas_result is True, otherwise returns None

        Examples:
            .. code-block:: python

                @op(required_resource_keys={"snowflake"})
                def drop_database(context):
                    context.resources.snowflake.execute_query(
                        "DROP DATABASE IF EXISTS MY_DATABASE"
                    )
        """

        check.str_param(sql, "sql")
        check.opt_dict_param(parameters, "parameters")
        check.bool_param(fetch_results, "fetch_results")

        with self.get_connection() as conn:
            with closing(conn.cursor()) as cursor:
                if sys.version_info[0] < 3:
                    sql = sql.encode("utf-8")

                self.log.info("Executing query: " + sql)
                cursor.execute(sql, parameters)  # pylint: disable=E1101
                if fetch_results:
                    return cursor.fetchall()  # pylint: disable=E1101
                if use_pandas_result:
                    return cursor.fetch_pandas_all()

    @public
    def execute_queries(
        self, sql_queries, parameters=None, fetch_results=False, use_pandas_result=False
    ):
        """Execute multiple queries in Snowflake.

        Args:
            sql_queries: List of queries to be executed in series
            parameters: parameters to be passed to every query
            fetch_results: If True, will return the results of the queries as a list. Defaults to False
            use_pandas_result: If True, will return the results of the queries as a list of a Pandas DataFrames.
                Defaults to False

        Returns:
            The results of the queries as a list if fetch_results or use_pandas_result is True,
            otherwise returns None

        Examples:
            .. code-block:: python

                @op(required_resource_keys={"snowflake"})
                def drop_database(context):
                    queries = ["DROP DATABASE IF EXISTS MY_DATABASE", "CREATE DATABASE MY_DATABASE"]
                    context.resources.snowflake.execute_queries(
                        sql=queries
                    )

        """
        check.list_param(sql_queries, "sql_queries", of_type=str)
        check.opt_dict_param(parameters, "parameters")
        check.bool_param(fetch_results, "fetch_results")

        if use_pandas_result:
            import pandas as pd

            results = pd.DataFrame()
        else:
            results = []
        with self.get_connection() as conn:
            with closing(conn.cursor()) as cursor:
                for sql in sql_queries:
                    if sys.version_info[0] < 3:
                        sql = sql.encode("utf-8")
                    self.log.info("Executing query: " + sql)
                    cursor.execute(sql, parameters)  # pylint: disable=E1101
                    if fetch_results:
                        if use_pandas_result:
                            results = results.append(cursor.fetch_pandas_all())
                        else:
                            results.append(cursor.fetchall())  # pylint: disable=E1101

        return results if fetch_results else None

    @public
    def load_table_from_local_parquet(self, src: str, table: str):
        """Stores the content of a parquet file to a Snowflake table

        Args:
            src (str): the name of the file to store in Snowflake
            table (str): the name of the table to store the data. If the table does not exist, it will
                be created. Otherwise the contents of the table will be replaced with the data in src
        """
        check.str_param(src, "src")
        check.str_param(table, "table")

        sql_queries = [
            "CREATE OR REPLACE TABLE {table} ( data VARIANT DEFAULT NULL);".format(table=table),
            "CREATE OR REPLACE FILE FORMAT parquet_format TYPE = 'parquet';",
            "PUT {src} @%{table};".format(src=src, table=table),
            "COPY INTO {table} FROM @%{table} FILE_FORMAT = (FORMAT_NAME = 'parquet_format');".format(
                table=table
            ),
        ]

        self.execute_queries(sql_queries)


@resource(
    config_schema=define_snowflake_config(),
    description="This resource is for connecting to the Snowflake data warehouse",
)
def snowflake_resource(context):
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
    return SnowflakeConnection(context.resource_config, context.log)


def _filter_password(args):
    """Remove password from connection args for logging"""
    return {k: v for k, v in args.items() if k != "password"}
