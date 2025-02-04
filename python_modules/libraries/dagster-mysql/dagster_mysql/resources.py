from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Optional, Union

import mysql.connector as mysql
from dagster import ConfigurableResource
from dagster._utils.backoff import backoff
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection
from pydantic import Field


class MySQLResource(ConfigurableResource):
    """Resource for interacting with a MySQL database. Wraps an underlying mysql.connector connection.

    Examples:
        .. code-block:: python

            from dagster import Definitions, asset, EnvVar
            from dagster_mysql import MySQLResource

            @asset
            def my_table(mysql: MySQLResource):
                with mysql.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT * FROM table;")

            defs = Definitions(
                assets=[my_table],
                resources={
                    "mysql": MySQLResource(
                        host="localhost",
                        port=3306,
                        user="root",
                        password=EnvVar("MYSQL_PASSWORD")
                    )
                }
            )
    """

    host: Optional[str] = Field(
        description=(
            "The host name or IP address of the MySQL server. Defaults to localhost if not provided."
        ),
        default=None,
    )

    port: Optional[int] = Field(
        description=(
            "The TCP/IP port of the MySQL server. Must be an integer. Defaults to 3306 if not provided."
        ),
        default=None,
    )

    user: str = Field(
        description=("The user name used to authenticate with the MySQL server."),
    )

    password: Optional[str] = Field(
        description=(
            "The password to authenticate the user with the MySQL server. Defaults to empty string if not provided."
        ),
        default=None,
    )

    database: Optional[str] = Field(
        description=(
            "The database name to use when connecting with the MySQL server. Defaults to None."
        ),
        default=None,
    )

    additional_parameters: dict[str, Any] = Field(
        description=(
            "Additional parameters to pass to mysql.connector.connect()."
            " For a full list of options, see"
            " https://dev.mysql.com/doc/connector-python/en/connector-python-connectargs.html"
        ),
        default={},
    )

    @classmethod
    def _is_dagster_maintained(cls):
        return True

    def _drop_none_values(self, dictionary) -> dict:
        return {key: value for (key, value) in dictionary.items() if (value is not None)}

    @contextmanager
    def get_connection(
        self,
    ) -> Generator[Union[PooledMySQLConnection, MySQLConnectionAbstract], None, None]:
        connection = backoff(
            fn=mysql.connect,
            retry_on=(mysql.errors.DatabaseError,),
            kwargs=self._drop_none_values(
                {
                    "host": self.host,
                    "port": self.port,
                    "user": self.user,
                    "password": self.password,
                    "database": self.database,
                    **self.additional_parameters,
                }
            ),
            max_retries=10,
        )

        try:
            yield connection
        finally:
            connection.close()
