import warnings
from collections.abc import Generator, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from io import StringIO
from typing import Any, cast

import snowflake.connector
from dagster import (
    AssetExecutionContext,
    AssetKey,
    DagsterInvariantViolationError,
    OpExecutionContext,
    get_dagster_logger,
)
from dagster._annotations import beta, public
from dagster._check import CheckError
from dagster._core.errors import DagsterInvalidPropertyError
from dagster._core.storage.event_log.sql_event_log import SqlDbConnection
from dagster_snowflake import SnowflakeConnection, SnowflakeResource
from snowflake.connector.cursor import SnowflakeCursor

from dagster_cloud.dagster_insights.insights_utils import get_current_context_and_asset_key
from dagster_cloud.dagster_insights.snowflake.snowflake_utils import meter_snowflake_query


def get_current_context_and_asset_key_or_warn() -> tuple[
    OpExecutionContext | AssetExecutionContext | None, AssetKey | None
]:
    try:
        return get_current_context_and_asset_key()
    except (DagsterInvalidPropertyError, DagsterInvariantViolationError, CheckError):
        warnings.warn(
            "Accessed InsightsSnowflakeResource outside of an Op or Asset context."
            " This query may not be properly attributed."
        )
        return None, None


class InsightsSnowflakeCursor(SnowflakeCursor):
    def __init__(self, *args, **kwargs) -> None:
        self._asset_key = None
        super().__init__(*args, **kwargs)

    def set_asset_key(self, asset_key: AssetKey | None):
        self._asset_key = asset_key

    def execute(self, command: str, *args, **kwargs):
        context, inferred_asset_key = get_current_context_and_asset_key_or_warn()
        if not context:
            return super().execute(command, *args, **kwargs)

        associated_asset_key = self._asset_key or inferred_asset_key

        return super().execute(
            meter_snowflake_query(context, command, associated_asset_key=associated_asset_key),
            *args,
            **kwargs,
        )


class WrappedSnowflakeConnection(snowflake.connector.SnowflakeConnection):
    def __init__(self, *args, asset_key: AssetKey | None = None, **kwargs) -> None:
        self._asset_key = asset_key
        super().__init__(*args, **kwargs)

    def execute_string(  # ty: ignore[invalid-method-override], fix me!
        self,
        sql_text: str,
        remove_comments: bool = False,
        return_cursors: bool = True,
        cursor_class: type[SnowflakeCursor] = InsightsSnowflakeCursor,
        **kwargs,
    ) -> Iterable[SnowflakeCursor]:
        return super().execute_string(
            sql_text,
            remove_comments,
            return_cursors,
            cursor_class,  # type: ignore  # (bad stubs)
            **kwargs,
        )

    def execute_stream(  # ty: ignore[invalid-method-override], fix me!
        self,
        stream: StringIO,
        remove_comments: bool = False,
        cursor_class: type[SnowflakeCursor] = InsightsSnowflakeCursor,
        **kwargs,
    ) -> Generator[SnowflakeCursor, None, None]:
        return super().execute_stream(stream, remove_comments, cursor_class, **kwargs)  # type: ignore  # (bad stubs)

    def cursor(self, cursor_class=None) -> SnowflakeCursor:
        if cursor_class is None:
            cursor = cast("InsightsSnowflakeCursor", super().cursor(InsightsSnowflakeCursor))
            cursor.set_asset_key(self._asset_key)
        else:
            cursor = super().cursor(cursor_class)

        return cursor


@beta
class InsightsSnowflakeResource(SnowflakeResource):
    """A wrapper around :py:class:`SnowflakeResource` which automatically tags
    Snowflake queries with comments which can be used to attribute Snowflake
    query costs to Dagster jobs and assets.

    If connector configuration is not set, InsightsSnowflakeResource.get_connection() will return a
    `snowflake.connector.Connection <https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-api#object-connection>`__
    object. If connector="sqlalchemy" configuration is set, then InsightsSnowflakeResource.get_connection() will
    return a `SQLAlchemy Connection <https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Connection>`__
    or a `SQLAlchemy raw connection <https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Engine.raw_connection>`__.

    A simple example of loading data into Snowflake and subsequently querying that data is shown below:

    Examples:
        .. code-block:: python

            from dagster import job, op
            from dagster_insights import InsightsSnowflakeResource

            @op
            def get_one(snowflake_resource: InsightsSnowflakeResource):
                with snowflake_resource.get_connection() as conn:
                    # conn is a snowflake.connector.Connection object
                    conn.cursor().execute("SELECT 1")

            @job
            def my_snowflake_job():
                get_one()

            my_snowflake_job.execute_in_process(
                resources={
                    'snowflake_resource': InsightsSnowflakeResource(
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

    def get_object_to_set_on_execution_context(self) -> Any:
        # Directly create a SnowflakeConnection here for backcompat since the SnowflakeConnection
        # has methods this resource does not have
        return SnowflakeConnection(
            config=self._resolved_config_dict,
            log=get_dagster_logger(),
            snowflake_connection_resource=self,
        )

    @public
    @contextmanager
    def get_connection(
        self, raw_conn: bool = True
    ) -> Iterator[SqlDbConnection | WrappedSnowflakeConnection]:
        if self.connector == "sqlalchemy":
            from snowflake.sqlalchemy import URL
            from sqlalchemy import create_engine, event

            engine = create_engine(
                URL(**self._sqlalchemy_connection_args),
                connect_args=self._sqlalchemy_engine_args,
            )

            # Attach a listener to the connection which will add a comment to any SQL query
            # executed through the connection. This comment will be used to identify the query
            # when later attributing cost.
            @event.listens_for(engine, "before_cursor_execute", retval=True)
            def comment_sql(conn, cursor, statement, parameters, context, executemany):
                context, asset_key = get_current_context_and_asset_key_or_warn()
                if not context:
                    return statement, parameters

                statement = meter_snowflake_query(
                    context, statement, associated_asset_key=asset_key
                )
                return statement, parameters

            conn = engine.raw_connection() if raw_conn else engine.connect()

            yield conn
            conn.close()
            engine.dispose()
        else:
            conn = WrappedSnowflakeConnection(**self._connection_args)

            yield conn
            if not self.autocommit:
                conn.commit()
            conn.close()

    @public
    @contextmanager
    def get_connection_for_asset(
        self, asset_key: AssetKey, raw_conn: bool = True
    ) -> Iterator[SqlDbConnection | WrappedSnowflakeConnection]:
        if self.connector == "sqlalchemy":
            from snowflake.sqlalchemy import URL
            from sqlalchemy import create_engine, event

            engine = create_engine(
                URL(**self._sqlalchemy_connection_args),
                connect_args=self._sqlalchemy_engine_args,
            )

            # Attach a listener to the connection which will add a comment to any SQL query
            # executed through the connection. This comment will be used to identify the query
            # when later attributing cost.
            @event.listens_for(engine, "before_cursor_execute", retval=True)
            def comment_sql(conn, cursor, statement, parameters, context, executemany):
                context, _ = get_current_context_and_asset_key_or_warn()
                if not context:
                    return statement, parameters

                statement = meter_snowflake_query(
                    context, statement, associated_asset_key=asset_key
                )
                return statement, parameters

            conn = engine.raw_connection() if raw_conn else engine.connect()

            yield conn
            conn.close()
            engine.dispose()
        else:
            conn = WrappedSnowflakeConnection(asset_key=asset_key, **self._connection_args)

            yield conn
            if not self.autocommit:
                conn.commit()
            conn.close()


class InsightsSnowflakeConnection(SnowflakeConnection):
    def execute_query(
        self,
        sql: str,
        parameters: Sequence[Any] | Mapping[Any, Any] | None = None,
        fetch_results: bool = False,
        use_pandas_result: bool = False,
    ):
        context, asset_key = get_current_context_and_asset_key_or_warn()
        if not context:
            return super().execute_query(sql, parameters, fetch_results, use_pandas_result)

        return super().execute_query(
            meter_snowflake_query(context, sql, associated_asset_key=asset_key),
            parameters,
            fetch_results,
            use_pandas_result,
        )

    def execute_queries(
        self,
        sql_queries: Sequence[str],
        parameters: Sequence[Any] | Mapping[Any, Any] | None = None,
        fetch_results: bool = False,
        use_pandas_result: bool = False,
    ) -> Sequence[Any] | None:
        context, asset_key = get_current_context_and_asset_key_or_warn()

        if not context:
            return super().execute_queries(
                sql_queries, parameters, fetch_results, use_pandas_result
            )

        return super().execute_queries(
            [
                meter_snowflake_query(context, sql, associated_asset_key=asset_key)
                for sql in sql_queries
            ],
            parameters,
            fetch_results,
            use_pandas_result,
        )
