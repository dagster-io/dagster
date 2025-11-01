from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Optional
import pymysql
from dagster import ConfigurableResource
from dagster._utils.backoff import backoff
from pydantic import Field
from sqlalchemy import create_engine, Engine
from sqlalchemy.exc import SQLAlchemyError


class MariaDBResource(ConfigurableResource):
    """Resource for interacting with a MariaDB database using SQLAlchemy."""

    host: str = Field(
        description="The host name or IP address of the MariaDB server.",
        default="localhost",
    )

    port: int = Field(
        description="The TCP/IP port of the MariaDB server.",
        default=3306,
    )

    user: str = Field(
        description="The user name used to authenticate with the MariaDB server.",
    )

    password: Optional[str] = Field(
        description="The password to authenticate the user with the MariaDB server.",
        default=None,
    )

    database: Optional[str] = Field(
        description="The database name to use when connecting with the MariaDB server.",
        default=None,
    )

    additional_parameters: dict[str, Any] = Field(
        description=(
            "Additional parameters to pass to SQLAlchemy create_engine()."
            " For a full list of options, see"
            " https://docs.sqlalchemy.org/en/14/core/engines.html#mysql"
        ),
        default={},
    )

    @classmethod
    def _is_dagster_maintained(cls):
        return True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._engine: Optional[Engine] = None

    def _get_connection_string(self) -> str:
        """Build the MariaDB connection string."""
        driver = "mariadb+pymysql"

        components = [f"{driver}://{self.user}"]
        
        if self.password:
            components.append(f":{self.password}")
        
        components.append(f"@{self.host}:{self.port}")
        
        if self.database:
            components.append(f"/{self.database}")
        
        connection_string = "".join(components)
        
        if self.additional_parameters:
            param_pairs = []
            for key, value in self.additional_parameters.items():
                param_pairs.append(f"{key}={value}")
            if param_pairs:
                connection_string += "?" + "&".join(param_pairs)
        
        return connection_string

    def get_engine(self) -> Engine:
        """Get a SQLAlchemy engine for MariaDB (cached to avoid recreating engines)."""
        if self._engine is None:
            connection_string = self._get_connection_string()
            # default engine parameters optimized for MariaDB
            engine_kwargs = {
                "pool_pre_ping": True,
                "pool_recycle": 3600,
                "echo": False,
                **self.additional_parameters,
            }
            self._engine = create_engine(connection_string, **engine_kwargs)
        return self._engine

    @contextmanager
    def get_connection(self) -> Generator[Any, None, None]:
        """Get a database connection with automatic cleanup."""
        engine = self.get_engine()
        
        connection = backoff(
            fn=engine.connect,
            retry_on=(SQLAlchemyError,),
            max_retries=10,
        )

        try:
            yield connection
        finally:
            connection.close()


