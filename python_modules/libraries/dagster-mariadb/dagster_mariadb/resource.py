from contextlib import contextmanager
from typing import Any, Dict, Generator as TypingGenerator, List, Optional, Tuple

from dagster import ConfigurableResource
from dagster._utils.backoff import backoff
from pydantic import Field
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.exc import SQLAlchemyError


class MariaDBResource(ConfigurableResource):
    """Resource for interacting with a MariaDB database using SQLAlchemy.

    This resource caches a single SQLAlchemy Engine for the lifetime of the
    resource instance. It provides convenience helpers for
    executing and streaming queries with improved error messages and
    parameter coercion.
    """

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

    additional_parameters: Dict[str, Any] = Field(
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
        # Cached SQLAlchemy engine. Engines are thread-safe and intended to be
        # long-lived; creating one per connection is expensive and may leak
        # resources.
        self._engine: Optional[Engine] = None

    def _get_connection_info(self) -> str:
        """Return a connection info string suitable for log messages (password omitted)."""
        parts = [f"{self.user}@" if self.user else ""]
        parts.append(f"{self.host}:{self.port}")
        if self.database:
            parts.append(f"/{self.database}")
        if self.additional_parameters:
            params = "&".join(f"{k}={v}" for k, v in self.additional_parameters.items())
            parts.append(f"?{params}")
        return "".join(parts)

    def _get_connection_string(self) -> str:
        """Build the MariaDB connection string."""
        driver = "pymysql"

        components = [f"{driver}://{self.user}"]

        if self.password:
            components.append(f":{self.password}")

        components.append(f"@{self.host}:{self.port}")

        if self.database:
            components.append(f"/{self.database}")

        connection_string = "".join(components)

        if self.additional_parameters:
            param_pairs: List[str] = []
            for key, value in self.additional_parameters.items():
                param_pairs.append(f"{key}={value}")
            if param_pairs:
                connection_string += "?" + "&".join(param_pairs)

        return connection_string

    def get_engine(self) -> Engine:
        """Get a SQLAlchemy engine for MariaDB (cached to avoid recreating engines)."""
        if self._engine is None:
            connection_string = self._get_connection_string()
            engine_kwargs = {
                "pool_pre_ping": True,
                "pool_recycle": 3600,
                "echo": False,
                **self.additional_parameters,
            }
            try:
                self._engine = create_engine(connection_string, **engine_kwargs)
            except SQLAlchemyError as e:
                raise RuntimeError(
                    f"Failed to create SQLAlchemy engine for MariaDB ({self._get_connection_info()}): {e}"
                ) from e
            except Exception as e:
                raise RuntimeError(
                    f"Unexpected error creating engine for MariaDB ({self._get_connection_info()}): {e}"
                ) from e
        return self._engine

    def dispose_engine(self) -> None:
        """Dispose the cached SQLAlchemy engine and its connection pool."""
        if self._engine is not None:
            try:
                self._engine.dispose()
            finally:
                self._engine = None

    def _coerce_params(self, params: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Coerce parameter values to SQLAlchemy-friendly Python native types."""
        if params is None:
            return None

        def _coerce_value(v: Any) -> Any:
            # Primitive native types are fine as-is
            if isinstance(v, (str, int, float, bool, type(None))):
                return v
            # Bytes -> str
            if isinstance(v, (bytes, bytearray)):
                try:
                    return v.decode("utf-8")
                except Exception:
                    return str(v)
            # numpy / pandas like objects -> Python native where possible
            try:
                if hasattr(v, "tolist"):
                    return v.tolist()
            except Exception:
                pass
            # Fallback to string representation
            return str(v)

        return {str(k): _coerce_value(v) for k, v in params.items()}

    @contextmanager
    def get_connection(self) -> TypingGenerator[Any, None, None]:
        """Get a database connection with automatic cleanup and backoff.

        Yields:
            A SQLAlchemy Connection object.
        """
        engine = self.get_engine()

        try:
            connection = backoff(
                fn=engine.connect,
                retry_on=(SQLAlchemyError,),
                max_retries=10,
            )
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Failed to obtain connection to MariaDB ({self._get_connection_info()}): {e}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error obtaining connection to MariaDB ({self._get_connection_info()}): {e}"
            ) from e

        try:
            yield connection
        finally:
            try:
                connection.close()
            except Exception:
                # best-effort close, don't mask earlier exceptions
                pass

    def stream_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        chunk_size: int = 1000,
    ) -> TypingGenerator[List[Tuple[Any, ...]], None, None]:
        """Stream query results in chunks.

        Args:
            query: SQL query to execute.
            params: Optional query parameters.
            chunk_size: Number of rows per yielded chunk. Must be >=1.

        Yields:
            Lists of rows (each row as a tuple).
        """
        if chunk_size < 1:
            raise ValueError("chunk_size must be >= 1")

        coerced_params = self._coerce_params(params)

        with self.get_connection() as conn:
            try:
                result = conn.execution_options(stream_results=True).execute(text(query), coerced_params or {})
            except SQLAlchemyError as e:
                raise RuntimeError(
                    f"Error executing query on MariaDB ({self._get_connection_info()}): {e}"
                ) from e

            buffer: List[Tuple[Any, ...]] = []
            try:
                for row in result:
                    # convert Row to tuple for portability
                    buffer.append(tuple(row))
                    if len(buffer) >= chunk_size:
                        yield buffer
                        buffer = []
                if buffer:
                    yield buffer
            finally:
                try:
                    result.close()
                except Exception:
                    pass

    def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Any, ...]]:
        """Execute a query and return all results as a list of tuples."""
        coerced_params = self._coerce_params(params)
        with self.get_connection() as conn:
            try:
                result = conn.execute(text(query), coerced_params or {})
                rows = [tuple(r) for r in result.fetchall()]
                try:
                    result.close()
                except Exception:
                    pass
                return rows
            except SQLAlchemyError as e:
                raise RuntimeError(
                    f"Error executing query on MariaDB ({self._get_connection_info()}): {e}"
                ) from e

