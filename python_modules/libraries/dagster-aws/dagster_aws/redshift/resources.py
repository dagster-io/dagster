import abc
from contextlib import contextmanager
from logging import Logger
from typing import Any, Optional, cast

import psycopg2
import psycopg2.extensions
from dagster import (
    ConfigurableResource,
    _check as check,
    get_dagster_logger,
    resource,
)
from dagster._annotations import deprecated
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from pydantic import Field


class RedshiftError(Exception):
    pass


class BaseRedshiftClient(abc.ABC):
    @abc.abstractmethod
    def execute_query(self, query, fetch_results=False, cursor_factory=None, error_callback=None):
        pass

    @abc.abstractmethod
    def execute_queries(
        self, queries, fetch_results=False, cursor_factory=None, error_callback=None
    ):
        pass


class RedshiftClient(BaseRedshiftClient):
    def __init__(self, conn_args: dict[str, Any], autocommit: Optional[bool], log: Logger):
        # Extract parameters from resource config
        self.conn_args = conn_args

        self.autocommit = autocommit
        self.log = log

    def execute_query(self, query, fetch_results=False, cursor_factory=None, error_callback=None):
        """Synchronously execute a single query against Redshift. Will return a list of rows, where
        each row is a tuple of values, e.g. SELECT 1 will return [(1,)].

        Args:
            query (str): The query to execute.
            fetch_results (Optional[bool]): Whether to return the results of executing the query.
                Defaults to False, in which case the query will be executed without retrieving the
                results.
            cursor_factory (Optional[:py:class:`psycopg2.extensions.cursor`]): An alternative
                cursor_factory; defaults to None. Will be used when constructing the cursor.
            error_callback (Optional[Callable[[Exception, Cursor, DagsterLogManager], None]]): A
                callback function, invoked when an exception is encountered during query execution;
                this is intended to support executing additional queries to provide diagnostic
                information, e.g. by querying ``stl_load_errors`` using ``pg_last_copy_id()``. If no
                function is provided, exceptions during query execution will be raised directly.

        Returns:
            Optional[List[Tuple[Any, ...]]]: Results of the query, as a list of tuples, when
                fetch_results is set. Otherwise return None.
        """
        check.str_param(query, "query")
        check.bool_param(fetch_results, "fetch_results")
        check.opt_class_param(
            cursor_factory, "cursor_factory", superclass=psycopg2.extensions.cursor
        )
        check.opt_callable_param(error_callback, "error_callback")

        with self._get_conn() as conn:
            with self._get_cursor(conn, cursor_factory=cursor_factory) as cursor:
                try:
                    self.log.info(f"Executing query '{query}'")
                    cursor.execute(query)

                    if fetch_results and cursor.rowcount > 0:
                        return cursor.fetchall()
                    else:
                        self.log.info("Empty result from query")

                except Exception as e:
                    # If autocommit is disabled or not set (it is disabled by default), Redshift
                    # will be in the middle of a transaction at exception time, and because of
                    # the failure the current transaction will not accept any further queries.
                    #
                    # This conn.commit() call closes the open transaction before handing off
                    # control to the error callback, so that the user can issue additional
                    # queries. Notably, for e.g. pg_last_copy_id() to work, it requires you to
                    # use the same conn/cursor, so you have to do this conn.commit() to ensure
                    # things are in a usable state in the error callback.
                    if not self.autocommit:
                        conn.commit()

                    if error_callback is not None:
                        error_callback(e, cursor, self.log)
                    else:
                        raise

    def execute_queries(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, queries, fetch_results=False, cursor_factory=None, error_callback=None
    ):
        """Synchronously execute a list of queries against Redshift. Will return a list of list of
        rows, where each row is a tuple of values, e.g. ['SELECT 1', 'SELECT 1'] will return
        [[(1,)], [(1,)]].

        Args:
            queries (List[str]): The queries to execute.
            fetch_results (Optional[bool]): Whether to return the results of executing the query.
                Defaults to False, in which case the query will be executed without retrieving the
                results.
            cursor_factory (Optional[:py:class:`psycopg2.extensions.cursor`]): An alternative
            cursor_factory; defaults to None. Will be used when constructing the cursor.
            error_callback (Optional[Callable[[Exception, Cursor, DagsterLogManager], None]]): A
                callback function, invoked when an exception is encountered during query execution;
                this is intended to support executing additional queries to provide diagnostic
                information, e.g. by querying ``stl_load_errors`` using ``pg_last_copy_id()``. If no
                function is provided, exceptions during query execution will be raised directly.

        Returns:
            Optional[List[List[Tuple[Any, ...]]]]: Results of the query, as a list of list of
                tuples, when fetch_results is set. Otherwise return None.
        """
        check.list_param(queries, "queries", of_type=str)
        check.bool_param(fetch_results, "fetch_results")
        check.opt_class_param(
            cursor_factory, "cursor_factory", superclass=psycopg2.extensions.cursor
        )
        check.opt_callable_param(error_callback, "error_callback")

        results = []
        with self._get_conn() as conn:
            with self._get_cursor(conn, cursor_factory=cursor_factory) as cursor:
                for query in queries:
                    try:
                        self.log.info(f"Executing query '{query}'")
                        cursor.execute(query)

                        if fetch_results and cursor.rowcount > 0:
                            results.append(cursor.fetchall())
                        else:
                            results.append([])
                            self.log.info("Empty result from query")

                    except Exception as e:
                        # If autocommit is disabled or not set (it is disabled by default), Redshift
                        # will be in the middle of a transaction at exception time, and because of
                        # the failure the current transaction will not accept any further queries.
                        #
                        # This conn.commit() call closes the open transaction before handing off
                        # control to the error callback, so that the user can issue additional
                        # queries. Notably, for e.g. pg_last_copy_id() to work, it requires you to
                        # use the same conn/cursor, so you have to do this conn.commit() to ensure
                        # things are in a usable state in the error callback.
                        if not self.autocommit:
                            conn.commit()

                        if error_callback is not None:
                            error_callback(e, cursor, self.log)
                        else:
                            raise

        if fetch_results:
            return results

    @contextmanager
    def _get_conn(self):
        conn = None
        try:
            conn = psycopg2.connect(**self.conn_args)
            yield conn
        finally:
            if conn:
                conn.close()

    @contextmanager
    def _get_cursor(self, conn, cursor_factory=None):
        check.opt_class_param(
            cursor_factory, "cursor_factory", superclass=psycopg2.extensions.cursor
        )

        # Could be none, in which case we should respect the connection default. Otherwise
        # explicitly set to true/false.
        if self.autocommit is not None:
            conn.autocommit = self.autocommit

        with conn:
            with conn.cursor(cursor_factory=cursor_factory) as cursor:
                yield cursor

            # If autocommit is set, we'll commit after each and every query execution. Otherwise, we
            # want to do a final commit after we're wrapped up executing the full set of one or more
            # queries.
            if not self.autocommit:
                conn.commit()


@deprecated(breaking_version="2.0", additional_warn_text="Use RedshiftClientResource instead.")
class RedshiftResource(RedshiftClient):
    """This class was used by the function-style Redshift resource."""


class FakeRedshiftClient(BaseRedshiftClient):
    QUERY_RESULT = [(1,)]

    def __init__(self, log: Logger):
        # Extract parameters from resource config

        self.log = log

    def execute_query(self, query, fetch_results=False, cursor_factory=None, error_callback=None):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Fake for execute_query; returns [self.QUERY_RESULT].

        Args:
            query (str): The query to execute.
            fetch_results (Optional[bool]): Whether to return the results of executing the query.
                Defaults to False, in which case the query will be executed without retrieving the
                results.
            cursor_factory (Optional[:py:class:`psycopg2.extensions.cursor`]): An alternative
                cursor_factory; defaults to None. Will be used when constructing the cursor.
            error_callback (Optional[Callable[[Exception, Cursor, DagsterLogManager], None]]): A
                callback function, invoked when an exception is encountered during query execution;
                this is intended to support executing additional queries to provide diagnostic
                information, e.g. by querying ``stl_load_errors`` using ``pg_last_copy_id()``. If no
                function is provided, exceptions during query execution will be raised directly.

        Returns:
            Optional[List[Tuple[Any, ...]]]: Results of the query, as a list of tuples, when
                fetch_results is set. Otherwise return None.
        """
        check.str_param(query, "query")
        check.bool_param(fetch_results, "fetch_results")
        check.opt_class_param(
            cursor_factory, "cursor_factory", superclass=psycopg2.extensions.cursor
        )
        check.opt_callable_param(error_callback, "error_callback")

        self.log.info(f"Executing query '{query}'")
        if fetch_results:
            return self.QUERY_RESULT

    def execute_queries(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, queries, fetch_results=False, cursor_factory=None, error_callback=None
    ):
        """Fake for execute_queries; returns [self.QUERY_RESULT] * 3.

        Args:
            queries (List[str]): The queries to execute.
            fetch_results (Optional[bool]): Whether to return the results of executing the query.
                Defaults to False, in which case the query will be executed without retrieving the
                results.
            cursor_factory (Optional[:py:class:`psycopg2.extensions.cursor`]): An alternative
                cursor_factory; defaults to None. Will be used when constructing the cursor.
            error_callback (Optional[Callable[[Exception, Cursor, DagsterLogManager], None]]): A
                callback function, invoked when an exception is encountered during query execution;
                this is intended to support executing additional queries to provide diagnostic
                information, e.g. by querying ``stl_load_errors`` using ``pg_last_copy_id()``. If no
                function is provided, exceptions during query execution will be raised directly.

        Returns:
            Optional[List[List[Tuple[Any, ...]]]]: Results of the query, as a list of list of
                tuples, when fetch_results is set. Otherwise return None.
        """
        check.list_param(queries, "queries", of_type=str)
        check.bool_param(fetch_results, "fetch_results")
        check.opt_class_param(
            cursor_factory, "cursor_factory", superclass=psycopg2.extensions.cursor
        )
        check.opt_callable_param(error_callback, "error_callback")

        for query in queries:
            self.log.info(f"Executing query '{query}'")
        if fetch_results:
            return [self.QUERY_RESULT] * 3


@deprecated(breaking_version="2.0", additional_warn_text="Use FakeRedshiftClientResource instead.")
class FakeRedshiftResource(FakeRedshiftClient):
    """This class was used by the function-style fake Redshift resource."""


class RedshiftClientResource(ConfigurableResource):
    """This resource enables connecting to a Redshift cluster and issuing queries against that
    cluster.

    Example:
        .. code-block:: python

            from dagster import Definitions, asset, EnvVar
            from dagster_aws.redshift import RedshiftClientResource

            @asset
            def example_redshift_asset(context, redshift: RedshiftClientResource):
                redshift.get_client().execute_query('SELECT 1', fetch_results=True)

            redshift_configured = RedshiftClientResource(
                host='my-redshift-cluster.us-east-1.redshift.amazonaws.com',
                port=5439,
                user='dagster',
                password=EnvVar("DAGSTER_REDSHIFT_PASSWORD"),
                database='dev',
            )

            defs = Definitions(
                assets=[example_redshift_asset],
                resources={'redshift': redshift_configured},
            )

    """

    host: str = Field(description="Redshift host")
    port: int = Field(default=5439, description="Redshift port")
    user: Optional[str] = Field(default=None, description="Username for Redshift connection")
    password: Optional[str] = Field(default=None, description="Password for Redshift connection")
    database: Optional[str] = Field(
        default=None,
        description=(
            "Name of the default database to use. After login, you can use USE DATABASE to change"
            " the database."
        ),
    )
    autocommit: Optional[bool] = Field(default=None, description="Whether to autocommit queries")
    connect_timeout: int = Field(
        default=5, description="Timeout for connection to Redshift cluster. Defaults to 5 seconds."
    )
    sslmode: str = Field(
        default="require",
        description=(
            "SSL mode to use. See the Redshift documentation for reference:"
            " https://docs.aws.amazon.com/redshift/latest/mgmt/connecting-ssl-support.html"
        ),
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def get_client(self) -> RedshiftClient:
        conn_args = {
            k: getattr(self, k, None)
            for k in (
                "host",
                "port",
                "user",
                "password",
                "database",
                "connect_timeout",
                "sslmode",
            )
            if getattr(self, k, None) is not None
        }

        return RedshiftClient(conn_args, self.autocommit, get_dagster_logger())


class FakeRedshiftClientResource(RedshiftClientResource):
    def get_client(self) -> FakeRedshiftClient:  # pyright: ignore[reportIncompatibleMethodOverride]
        return FakeRedshiftClient(get_dagster_logger())


@dagster_maintained_resource
@resource(
    config_schema=RedshiftClientResource.to_config_schema(),
    description="Resource for connecting to the Redshift data warehouse",
)
def redshift_resource(context) -> RedshiftClient:
    """This resource enables connecting to a Redshift cluster and issuing queries against that
    cluster.

    Example:
        .. code-block:: python

            from dagster import build_op_context, op
            from dagster_aws.redshift import redshift_resource

            @op(required_resource_keys={'redshift'})
            def example_redshift_op(context):
                return context.resources.redshift.execute_query('SELECT 1', fetch_results=True)

            redshift_configured = redshift_resource.configured({
                'host': 'my-redshift-cluster.us-east-1.redshift.amazonaws.com',
                'port': 5439,
                'user': 'dagster',
                'password': 'dagster',
                'database': 'dev',
            })
            context = build_op_context(resources={'redshift': redshift_configured})
            assert example_redshift_op(context) == [(1,)]

    """
    return RedshiftClientResource.from_resource_context(context).get_client()


@dagster_maintained_resource
@resource(
    config_schema=FakeRedshiftClientResource.to_config_schema(),
    description=(
        "Fake resource for connecting to the Redshift data warehouse. Usage is identical "
        "to the real redshift_resource. Will always return [(1,)] for the single query case and "
        "[[(1,)], [(1,)], [(1,)]] for the multi query case."
    ),
)
def fake_redshift_resource(context) -> FakeRedshiftClient:
    return cast(
        FakeRedshiftClient,
        FakeRedshiftClientResource.from_resource_context(context).get_client(),
    )
