from collections.abc import Mapping
from contextlib import contextmanager
from typing import Any

from clickhouse_driver import Client
from dagster import ConfigurableResource
from dagster.components.lib.sql_component.sql_client import SQLClient
from pydantic import Field


def client_kwargs_from_resource_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """Build clickhouse-driver Client kwargs from an I/O manager or resource config dict."""
    return {
        "host": config["host"],
        "port": config.get("port", 9000),
        "user": config.get("user", "default"),
        "password": config.get("password", ""),
        "database": config.get("database"),
        "secure": config.get("secure", False),
        "settings": config.get("settings") or {},
    }


class ClickhouseResource(ConfigurableResource, SQLClient):
    """Resource for interacting with a ClickHouse database via ``clickhouse-driver`` (native protocol).

    Examples:
        .. code-block:: python

            from dagster import Definitions, asset
            from dagster_clickhouse import ClickhouseResource

            @asset
            def my_table(clickhouse: ClickhouseResource):
                with clickhouse.get_connection() as client:
                    client.execute("SELECT * FROM my_database.my_table LIMIT 1")

            Definitions(
                assets=[my_table],
                resources={"clickhouse": ClickhouseResource(host="localhost")},
            )

    """

    host: str = Field(description="ClickHouse server host.")
    port: int = Field(
        default=9000,
        description="Native protocol port (default 9000).",
    )
    user: str = Field(default="default", description="User name.")
    password: str = Field(default="", description="Password.")
    database: str | None = Field(
        default=None,
        description="Default database on the connection (ClickHouse server database name).",
    )
    secure: bool = Field(
        default=False,
        description="Use TLS for the native protocol connection.",
    )
    settings: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional ClickHouse server settings passed to the driver client.",
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def connect_and_execute(self, sql: str) -> None:
        """Connect to ClickHouse and execute the given SQL statement."""
        with self.get_connection() as client:
            client.execute(sql)

    @contextmanager
    def get_connection(self):
        kwargs = client_kwargs_from_resource_config(
            {
                "host": self.host,
                "port": self.port,
                "user": self.user,
                "password": self.password,
                "database": self.database,
                "secure": self.secure,
                "settings": self.settings,
            }
        )
        client = Client(**kwargs)
        try:
            yield client
        finally:
            client.disconnect()
