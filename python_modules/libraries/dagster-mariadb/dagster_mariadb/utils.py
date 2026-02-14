from typing import Union, Callable, Any, Optional
from typing_extensions import TypeAlias
import pymysql
from sqlalchemy.engine import Connection
from urllib.parse import urlparse
import time
from dagster import get_dagster_logger
from urllib.parse import quote_plus as urlquote, unquote_plus as urlunquote

# Type alias for connection types
MariaDBConnectionUnion: TypeAlias = Union[
    Connection,  # SQLAlchemy connection
    pymysql.connections.Connection,  # PyMySQL connection
]


def retry_mariadb_connection_fn(
    fn: Callable,
    retry_limit: int = 3,
    retry_wait: float = 0.2,
    kwargs: Optional[dict] = None,
) -> Any:
    """Retry a function that creates a connection.
    
    Args:
        fn: Function to call (e.g., engine.connect or pymysql.connect)
        retry_limit: Maximum number of retry attempts
        retry_wait: Seconds to wait between retries
        kwargs: Keyword arguments to pass to fn
        
    Returns:
        Result of fn call
        
    Raises:
        Exception: If all retries fail
    """
    logger = get_dagster_logger()
    kwargs = kwargs or {}
    
    for attempt in range(retry_limit):
        try:
            return fn(**kwargs) if kwargs else fn()
        except Exception as e:
            if attempt == retry_limit - 1:
                logger.error(f"Failed to connect after {retry_limit} attempts")
                raise
            logger.warning(
                f"Connection attempt {attempt + 1}/{retry_limit} failed: {e}. "
                f"Retrying in {retry_wait}s..."
            )
            time.sleep(retry_wait)


def get_pymysql_connection_from_string(conn_string: str) -> pymysql.connections.Connection:
    """Get a raw PyMySQL connection from connection string.
    
    Handles URL-encoded special characters in username, password, and database name.
    
    Args:
        conn_string: Connection string in format:
            mariadb+pymysql://user:password@host:port/database
            Special characters in user/password/database should be URL-encoded
    
    Returns:
        PyMySQL connection object
        
    Example:
        >>> # Password with special characters
        >>> conn_string = "mariadb+pymysql://root:p%40ssw%23rd@localhost:3306/mydb"
        >>> conn = get_pymysql_connection_from_string(conn_string)
        >>> with conn.cursor() as cur:
        ...     cur.execute("SELECT 1")
    """
    parsed = urlparse(conn_string)
    
    # URL decode username and password to handle special characters
    username = urlunquote(parsed.username) if parsed.username else None
    password = urlunquote(parsed.password) if parsed.password else None
    database = urlunquote(parsed.path[1:]) if parsed.path and len(parsed.path) > 1 else None
    
    # Build connection parameters, only including non-None values
    conn_params = {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
    }
    
    if username is not None:
        conn_params["user"] = username
    
    if password is not None:
        conn_params["password"] = password
    
    if database is not None:
        conn_params["database"] = database
    
    conn = pymysql.connect(**conn_params)
    return conn


def get_connection_params_from_string(conn_string: str) -> dict:
    """Extract connection parameters from connection string.
    
    Handles URL-encoded special characters.
    
    Args:
        conn_string: Connection string with potentially URL-encoded values
        
    Returns:
        Dictionary of connection parameters with decoded values
    """
    parsed = urlparse(conn_string)
    
    return {
        "user": urlunquote(parsed.username) if parsed.username else None,
        "password": urlunquote(parsed.password) if parsed.password else None,
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "database": urlunquote(parsed.path[1:]) if parsed.path and len(parsed.path) > 1 else None,
    }


def is_pymysql_connection(conn: MariaDBConnectionUnion) -> bool:
    """Check if connection is a PyMySQL connection.
    
    Args:
        conn: Connection object to check
        
    Returns:
        True if PyMySQL connection, False if SQLAlchemy connection
    """
    return isinstance(conn, pymysql.connections.Connection)


def is_sqlalchemy_connection(conn: MariaDBConnectionUnion) -> bool:
    """Check if connection is a SQLAlchemy connection.
    
    Args:
        conn: Connection object to check
        
    Returns:
        True if SQLAlchemy connection, False if PyMySQL connection
    """
    return isinstance(conn, Connection)

def encode_connection_string_component(component: str) -> str:
    """URL encode a connection string component (username, password, database).
    
    Args:
        component: String to encode
        
    Returns:
        URL-encoded string safe for connection strings
        
    Example:
        >>> encode_connection_string_component("p@ssw#rd!")
        'p%40ssw%23rd%21'
    """
    return urlquote(component)


def decode_connection_string_component(component: str) -> str:
    """URL decode a connection string component.
    
    Args:
        component: URL-encoded string
        
    Returns:
        Decoded string
        
    Example:
        >>> decode_connection_string_component("p%40ssw%23rd%21")
        'p@ssw#rd!'
    """
    return urlunquote(component)