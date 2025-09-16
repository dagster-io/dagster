from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Optional

import psycopg2
from dagster import ConfigurableResource
from dagster._utils.backoff import backoff
from pydantic import Field


class PostgresResource(ConfigurableResource):
    """Resource for interacting with a postgres database. Wraps an underlying psycopg2 connection.

    Examples:
        .. code-block:: python

            from dagster import Definitions, asset, EnvVar
            from dagster_postgres import PostgresResource

            @asset
            def my_table(postgres: PostgresResource):
                with postgres.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT * FROM table;")

            defs = Definitions(
                assets=[my_table],
                resources={
                    "postgres": PostgresResource(
                        host="localhost",
                        port=5432,
                        user="postgres",
                        password=EnvVar("POSTGRES_PASSWORD")
                    )
                }
            )


    """

    dsn: Optional[str] = Field(
        description=(
            "A libpq connection string."
            " Can be provided together with keyword-arguments in a mix-and-match manner."
            " Defaults to None if not provided - in which case only the keyword arguments"
            " will be used to establish the connection."
        ),
        default=None,
    )

    host: Optional[str] = Field(
        description=("Database host address. Defaults to UNIX socket if not provided"),
        default=None,
    )

    port: Optional[int] = Field(
        description=("Connection port number. defaults to 5432 if not provided."),
        default=None,
    )

    user: Optional[str] = Field(
        description=(
            "User name used to authenticate."
            " Defaults to None if not provided - in which case the 'user' field in"
            " the dsn will be used"
        ),
        default=None,
    )

    password: Optional[str] = Field(
        description=(
            "Password used to authenticate."
            " Defaults to None if not provided - in which case the 'password' field in"
            " the dsn will be used"
        ),
        default=None,
    )

    database: Optional[str] = Field(
        description=("The database name. Defaults to the user name if not provided"),
        default=None,
    )

    additional_parameters: dict[str, Any] = Field(
        description=(
            "Additional parameters to pass to psycopg2.connect."
            " For a full list of options, see"
            " https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-PARAMKEYWORDS"
        ),
        default={},
    )

    @classmethod
    def _is_dagster_maintained(cls):
        return True

    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        connection = backoff(
            fn=psycopg2.connect,
            retry_on=(psycopg2.OperationalError,),
            kwargs={
                "dsn": self.dsn,
                "host": self.host,
                "port": self.port,
                "user": self.user,
                "password": self.password,
                "database": self.database,
                **self.additional_parameters,
            },
            max_retries=10,
        )

        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
