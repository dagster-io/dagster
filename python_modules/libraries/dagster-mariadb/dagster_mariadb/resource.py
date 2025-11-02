# resource.py
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Dict, Generator as TypingGenerator, List, Optional, Tuple

from dagster import ConfigurableResource
from dagster._utils.backoff import backoff
from pydantic import Field
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.exc import SQLAlchemyError
from dagster_mariadb.utils import (
    retry_mariadb_connection_fn,
    get_pymysql_connection_from_string,
    MariaDBConnectionUnion,
    is_pymysql_connection,
    is_sqlalchemy_connection,
)
from urllib.parse import quote_plus as urlquote

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
        """Build the MariaDB connection string with proper URL encoding for special characters."""
        driver = "mariadb+pymysql"
        components = [f"{driver}://"]
        
        # URL encode username if it contains special characters
        encoded_user = urlquote(self.user)
        components.append(encoded_user)
        
        if self.password:
            # URL encode password to handle special characters
            encoded_password = urlquote(self.password)
            components.append(f":{encoded_password}")
        
        host = self.host or "localhost"
        port = self.port or 3306
        components.append(f"@{host}:{port}")
        
        if self.database:
            # URL encode database name if it contains special characters
            encoded_database = urlquote(self.database)
            components.append(f"/{encoded_database}")
        
        connection_string = "".join(components)
        
        # Add additional parameters if present
        if self.additional_parameters:
            param_pairs = []
            for key, value in self.additional_parameters.items():
                # URL encode parameter values
                encoded_value = urlquote(str(value))
                param_pairs.append(f"{key}={encoded_value}")
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
    def get_pymysql_connection_params(self) -> dict:
        """Get connection parameters for PyMySQL.
        
        Returns:
            Dictionary of connection parameters
        """
        return self._drop_none_values({
            "host": self.host or "localhost",
            "port": self.port or 3306,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            **self.additional_parameters,
        })

    @contextmanager
    def get_connection_flexible(
        self,
        use_pymysql: bool = False
    ) -> Generator[MariaDBConnectionUnion, None, None]:
        """Get either a SQLAlchemy or PyMySQL connection based on preference.
        
        Args:
            use_pymysql: If True, returns PyMySQL connection. 
                        If False, returns SQLAlchemy connection.
        
        Yields:
            Either a SQLAlchemy Connection or PyMySQL Connection
            
        Example:
            >>> # Get PyMySQL connection
            >>> with mariadb.get_connection_flexible(use_pymysql=True) as conn:
            ...     with conn.cursor() as cur:
            ...         cur.execute("SELECT 1")
            
            >>> # Get SQLAlchemy connection  
            >>> with mariadb.get_connection_flexible(use_pymysql=False) as conn:
            ...     result = conn.execute(text("SELECT 1"))
        """
        if use_pymysql:
            with self.get_raw_connection() as conn:
                yield conn
        else:
            with self.get_connection() as conn:
                yield conn

    def execute_query_raw(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_all: bool = True
    ):
        """Execute a query using raw PyMySQL connection.
        
        Useful for simple queries where you don't need SQLAlchemy overhead.
        
        Args:
            query: SQL query to execute (use %s for parameters)
            params: Tuple of query parameters
            fetch_all: If True, returns all results. If False, returns cursor.
            
        Returns:
            Query results or cursor
            
        Example:
            >>> # Simple select
            >>> results = mariadb.execute_query_raw(
            ...     "SELECT * FROM users WHERE id = %s",
            ...     params=(1,)
            ... )
            
            >>> # Insert with commit
            >>> mariadb.execute_query_raw(
            ...     "INSERT INTO users (name) VALUES (%s)",
            ...     params=("John",),
            ...     fetch_all=False
            ... )
        """
        with self.get_raw_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                
                if fetch_all:
                    results = cursor.fetchall()
                    conn.commit()
                    return results
                else:
                    conn.commit()
                    return cursor.rowcount

    def execute_many_raw(
        self,
        query: str,
        params_list: list[tuple]
    ) -> int:
        """Execute a query multiple times with different parameters (bulk insert).
        
        Uses PyMySQL's executemany for better performance on bulk operations.
        
        Args:
            query: SQL query with parameter placeholders
            params_list: List of tuples containing parameters for each execution
            
        Returns:
            Total number of affected rows
            
        Example:
            >>> users = [
            ...     ("Alice", 25),
            ...     ("Bob", 30),
            ...     ("Charlie", 35)
            ... ]
            >>> rows = mariadb.execute_many_raw(
            ...     "INSERT INTO users (name, age) VALUES (%s, %s)",
            ...     users
            ... )
            >>> print(f"Inserted {rows} rows")
        """
        with self.get_raw_connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount

    def get_connection_info(self) -> dict:
        """Get connection information (without password).
        
        Returns:
            Dictionary with connection details
        """
        return {
            "host": self.host or "localhost",
            "port": self.port or 3306,
            "user": self.user,
            "database": self.database,
            "has_password": bool(self.password),
        }

    def test_connection(self, use_pymysql: bool = False) -> tuple[bool, Optional[str]]:
        """Test the connection to MariaDB.
        
        Args:
            use_pymysql: Test with PyMySQL connection instead of SQLAlchemy
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
            
        Example:
            >>> success, error = mariadb.test_connection()
            >>> if success:
            ...     print("Connection successful!")
            >>> else:
            ...     print(f"Connection failed: {error}")
        """
        try:
            if use_pymysql:
                with self.get_raw_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
            else:
                with self.get_connection() as conn:
                    from sqlalchemy import text
                    conn.execute(text("SELECT 1"))
            return (True, None)
        except Exception as e:
            return (False, str(e))

    def dispose_engine(self) -> None:
        """Dispose the cached SQLAlchemy engine and its connection pool.
        
        Call this when you want to release all connections.
        """
        if hasattr(self, '_engine') and self._engine is not None:
            try:
                self._engine.dispose()
            finally:
                self._engine = None

