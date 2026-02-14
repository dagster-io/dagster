# advanced_features.py

"""
MariaDB Advanced Features

This module provides utilities for leveraging MariaDB-specific features including:
- Storage engines (InnoDB, Aria, MyRocks, Spider)
- Parallel query execution
- Galera Cluster support
- ColumnStore for columnar storage
"""

from collections.abc import Sequence
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError


# Storage Engine Enum
class StorageEngine:
    """MariaDB storage engines optimized for different workloads."""
    
    InnoDB = "InnoDB"      # ACID-compliant, row-level locking (default)
    Aria = "Aria"          # Crash-safe, improved MyISAM
    MyRocks = "MyRocks"    # RocksDB-based, write-optimized
    Spider = "Spider"      # Federated table engine for distributed queries
    ColumnStore = "ColumnStore"  # Columnar storage for analytics


def create_table_with_storage_engine(
    table_name: str,
    schema_name: Optional[str],
    columns: dict[str, str],
    connection: Connection,
    storage_engine: str = StorageEngine.InnoDB,
) -> None:
    """Create a table with a specific storage engine.
    
    Args:
        table_name: Name of the table
        schema_name: Schema name (optional)
        columns: Dictionary of column_name -> column_definition
        storage_engine: Storage engine to use
        connection: Database connection
        
    Examples:
        >>> create_table_with_storage_engine(
        ...     "logs",
        ...     "analytics",
        ...     {"id": "INT AUTO_INCREMENT PRIMARY KEY", "message": "TEXT"},
        ...     StorageEngine.Aria,
        ...     connection,
        ... )
    """
    qualified_name = f"{schema_name}.{table_name}" if schema_name else table_name
    column_defs = ", ".join([f"{name} {defn}" for name, defn in columns.items()])
    
    query = f"""
        CREATE TABLE IF NOT EXISTS {qualified_name} (
            {column_defs}
        ) ENGINE={storage_engine}
    """
    
    try:
        connection.execute(text(query))
        connection.commit()
    except SQLAlchemyError as e:
        connection.rollback()
        raise e


def enable_parallel_query_execution(
    connection: Connection,
    enabled: bool = True,
) -> None:
    """Enable or disable parallel query execution in MariaDB.
    
    Note: This requires appropriate MariaDB configuration on the server.
    
    Args:
        connection: Database connection
        enabled: Whether to enable parallel execution
    """
    try:
        query = f"SET SESSION sql_log_bin=0; SET GLOBAL innodb_parallel_read_threads={64 if enabled else 1}; SET SESSION max_parallel_tables={10 if enabled else 1}"
        # Note: These are session-specific settings
        connection.execute(text(query))
        connection.commit()
    except SQLAlchemyError:
        # Not all MariaDB servers support parallel execution
        pass


def create_columnstore_table(
    table_name: str,
    schema_name: Optional[str],
    columns: dict[str, str],
    connection: Connection,
) -> None:
    """Create a ColumnStore table for analytical workloads.
    
    ColumnStore is optimized for:
    - Analytical queries
    - Large-scale data warehousing
    - Columnar data access patterns
    
    Args:
        table_name: Name of the table
        schema_name: Schema name (optional)
        columns: Dictionary of column_name -> column_definition
        connection: Database connection
    """
    create_table_with_storage_engine(
        table_name=table_name,
        schema_name=schema_name,
        columns=columns,
        storage_engine=StorageEngine.ColumnStore,
        connection=connection,
    )


def check_galera_cluster_status(connection: Connection) -> Optional[dict[str, Any]]:
    """Check Galera Cluster status if running in a cluster.
    
    Returns None if not running in Galera Cluster mode.
    
    Args:
        connection: Database connection
        
    Returns:
        Dictionary with cluster status or None
    """
    try:
        result = connection.execute(
            text("SHOW STATUS LIKE 'wsrep%'")
        )
        rows = result.fetchall()
        
        if not rows:
            return None
            
        cluster_status = {row[0]: row[1] for row in rows}
        return {
            "connected": cluster_status.get("wsrep_connected", "OFF"),
            "ready": cluster_status.get("wsrep_ready", "OFF"),
            "cluster_size": cluster_status.get("wsrep_cluster_size", "0"),
            "local_state": cluster_status.get("wsrep_local_state_comment", "Unknown"),
        }
    except SQLAlchemyError:
        return None


def optimize_for_write_heavy_load(
    table_name: str,
    schema_name: Optional[str],
    connection: Connection,
    use_myrocks: bool = True,
) -> None:
    """Optimize a table for write-heavy workloads.
    
    For write-heavy workloads, use MyRocks which offers:
    - Better write performance
    - Better compression
    - Lower storage requirements
    
    Args:
        table_name: Name of the table
        schema_name: Schema name (optional)
        connection: Database connection
        use_myrocks: Whether to use MyRocks engine
    """
    storage_engine = StorageEngine.MyRocks if use_myrocks else StorageEngine.InnoDB
    qualified_name = f"{schema_name}.{table_name}" if schema_name else table_name
    
    try:
        # Alter table to use appropriate storage engine
        connection.execute(text(f"ALTER TABLE {qualified_name} ENGINE={storage_engine}"))
        connection.commit()
    except SQLAlchemyError as e:
        connection.rollback()
        raise e


def create_distributed_table_via_spider(
    table_name: str,
    schema_name: Optional[str],
    remote_table_name: str,
    remote_host: str,
    remote_database: str,
    connection: Connection,
) -> None:
    """Create a Spider table that federates queries to remote servers.
    
    Spider enables querying across multiple MariaDB servers as if they were one.
    
    Args:
        table_name: Local table name (federated)
        schema_name: Schema name (optional)
        remote_table_name: Table name on remote server
        remote_host: Host of remote server
        remote_database: Database on remote server
        connection: Database connection
    """
    qualified_name = f"{schema_name}.{table_name}" if schema_name else table_name
    
    # Note: This is a simplified example
    # Real Spider setup requires additional configuration
    query = f"""
        CREATE TABLE {qualified_name} (
            -- Define columns matching remote table
            id INT,
            data VARCHAR(255),
            PRIMARY KEY (id)
        ) ENGINE=Spider
        COMMENT 'wrapper "mysql", table "{remote_table_name}"'
    """
    
    try:
        connection.execute(text(query))
        connection.commit()
    except SQLAlchemyError as e:
        connection.rollback()
        raise e


def get_storage_engine_info(connection: Connection) -> dict[str, Sequence[str]]:
    """Get information about available and enabled storage engines.
    
    Args:
        connection: Database connection
        
    Returns:
        Dictionary with 'available' and 'supported' engine lists
    """
    try:
        result = connection.execute(text("SHOW ENGINES"))
        rows = result.fetchall()
        
        available = []
        supported = []
        
        for engine_name, support, comment, transactions, xa, savepoints in rows:
            if support in ["YES", "DEFAULT"]:
                available.append(engine_name)
            if support == "DEFAULT" or (support == "YES" and "MariaDB" in str(comment)):
                supported.append(engine_name)
        
        return {
            "available": available,
            "supported": supported,
        }
    except SQLAlchemyError:
        return {"available": [], "supported": []}


# Helper functions for common patterns

def setup_analytics_warehouse(
    connection: Connection,
    database_name: str,
) -> None:
    """Setup a data warehouse optimized for analytics using ColumnStore.
    
    Args:
        connection: Database connection
        database_name: Name of the database to create
    """
    try:
        connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {database_name}"))
        connection.commit()
        
        # Note: ColumnStore requires specific setup steps not shown here
        # This is a simplified example
    except SQLAlchemyError as e:
        connection.rollback()
        raise e

