"""
MariaDB Advanced Features Example

Demonstrates how to leverage MariaDB-specific features including:
- Storage engines (InnoDB, MyRocks, ColumnStore, Aria)
- Parallel query execution
- Galera Cluster support
- ColumnStore for analytics
"""

from dagster import Definitions, asset, EnvVar
from dagster_mariadb import (
    MariaDBResource,
    MariaDBPandasIOManager,
    StorageEngine,
    create_table_with_storage_engine,
    enable_parallel_query_execution,
    check_galera_cluster_status,
    get_storage_engine_info,
    optimize_for_write_heavy_load,
)


mariadb_resource = MariaDBResource(
    host="localhost",
    port=3306,
    user="root",
    password=EnvVar("MARIADB_PASSWORD"),
    database="advanced_features_db",
)

mariadb_io_manager = MariaDBPandasIOManager(
    engine_resource_key="mariadb",
    schema="analytics",
    mode="replace",
)


@asset
def check_mariadb_capabilities(mariadb: MariaDBResource):
    """Check MariaDB capabilities and storage engines."""
    with mariadb.get_connection() as conn:
        # Check available storage engines
        engines = get_storage_engine_info(conn)
        print(f"Available engines: {engines['available']}")
        print(f"Supported engines: {engines['supported']}")
        
        # Check if running in Galera Cluster
        cluster_status = check_galera_cluster_status(conn)
        if cluster_status:
            print(f"Galera Cluster size: {cluster_status['cluster_size']}")
            print(f"Cluster state: {cluster_status['local_state']}")
        else:
            print("Not running in Galera Cluster mode")
        
        return engines


@asset
def setup_write_optimized_tables(mariadb: MariaDBResource):
    """Setup tables optimized for write-heavy workloads using MyRocks."""
    with mariadb.get_connection() as conn:
        # Create a table optimized for high write throughput
        create_table_with_storage_engine(
            table_name="event_logs",
            schema_name="analytics",
            columns={
                "id": "INT AUTO_INCREMENT PRIMARY KEY",
                "event_time": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "event_type": "VARCHAR(50)",
                "event_data": "TEXT",
            },
            connection=conn,
            storage_engine=StorageEngine.MyRocks,  # Better write performance
        )


@asset
def setup_analytics_table(mariadb: MariaDBResource):
    """Setup columnar storage table for analytical workloads."""
    with mariadb.get_connection() as conn:
        # Create ColumnStore table for analytics
        create_table_with_storage_engine(
            table_name="sales_analytics",
            schema_name="analytics",
            columns={
                "id": "INT",
                "date": "DATE",
                "product_id": "INT",
                "quantity": "INT",
                "revenue": "DECIMAL(10, 2)",
                "region": "VARCHAR(50)",
            },
            connection=conn,
            storage_engine=StorageEngine.ColumnStore,  # Columnar storage
        )


@asset
def enable_parallel_queries(mariadb: MariaDBResource):
    """Enable parallel query execution for better performance."""
    with mariadb.get_connection() as conn:
        enable_parallel_query_execution(conn, enabled=True)
        print("Parallel query execution enabled")


@asset
def optimize_existing_table(mariadb: MariaDBResource):
    """Optimize an existing table for specific workload patterns."""
    with mariadb.get_connection() as conn:
        # Optimize for write-heavy workload
        optimize_for_write_heavy_load(
            table_name="frequent_writes",
            schema_name="analytics",
            connection=conn,
            use_myrocks=True,
        )


# Example: Using different storage engines for different use cases
@asset
def demonstrate_storage_engine_selection(mariadb: MariaDBResource):
    """Demonstrate appropriate storage engine selection."""
    with mariadb.get_connection() as conn:
        
        # 1. InnoDB for transactional workloads (default)
        create_table_with_storage_engine(
            table_name="transactions",
            schema_name="finance",
            columns={
                "id": "INT AUTO_INCREMENT PRIMARY KEY",
                "account_id": "INT",
                "amount": "DECIMAL(10, 2)",
                "timestamp": "TIMESTAMP",
            },
            connection=conn,
            storage_engine=StorageEngine.InnoDB,  # ACID compliant
        )
        
        # 2. Aria for temporary/log tables
        create_table_with_storage_engine(
            table_name="temp_logs",
            schema_name="system",
            columns={
                "id": "BIGINT AUTO_INCREMENT PRIMARY KEY",
                "log_message": "TEXT",
                "created_at": "TIMESTAMP",
            },
            connection=conn,
            storage_engine=StorageEngine.Aria,  # Crash-safe MyISAM
        )
        
        # 3. MyRocks for time-series data with high write load
        create_table_with_storage_engine(
            table_name="metrics",
            schema_name="monitoring",
            columns={
                "id": "BIGINT AUTO_INCREMENT PRIMARY KEY",
                "metric_name": "VARCHAR(100)",
                "value": "DOUBLE",
                "timestamp": "TIMESTAMP",
            },
            connection=conn,
            storage_engine=StorageEngine.MyRocks,  # Write-optimized
        )


defs = Definitions(
    assets=[
        check_mariadb_capabilities,
        setup_write_optimized_tables,
        setup_analytics_table,
        enable_parallel_queries,
        optimize_existing_table,
        demonstrate_storage_engine_selection,
    ],
    resources={
        "mariadb": mariadb_resource,
    },
)

