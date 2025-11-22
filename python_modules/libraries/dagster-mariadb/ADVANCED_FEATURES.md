# MariaDB Advanced Features Guide

This guide demonstrates how to leverage MariaDB's advanced features in your Dagster pipelines.

## Table of Contents

1. [Storage Engines](#storage-engines)
2. [Parallel Query Execution](#parallel-query-execution)
3. [Galera Cluster Support](#galera-cluster-support)
4. [ColumnStore for Analytics](#columnstore-for-analytics)
5. [Workload-Specific Optimization](#workload-specific-optimization)

## Storage Engines

MariaDB supports multiple storage engines, each optimized for different workloads:

### Available Storage Engines

```python
from dagster_mariadb import StorageEngine

# Storage engine options:
StorageEngine.InnoDB      # ACID-compliant, transactional workloads (default)
StorageEngine.Aria        # Crash-safe MyISAM replacement
StorageEngine.MyRocks     # Write-optimized, RocksDB-based
StorageEngine.Spider      # Federated/distributed queries
StorageEngine.ColumnStore # Columnar storage for analytics
```

### Choose the Right Storage Engine

| Use Case | Recommended Engine | Why |
|----------|-------------------|-----|
| Transactional data | InnoDB | ACID compliance, row-level locking |
| High write load | MyRocks | Better write performance, compression |
| Temporary logs | Aria | Crash-safe, low overhead |
| Analytics/OLAP | ColumnStore | Columnar storage, fast aggregations |
| Distributed queries | Spider | Federate across multiple servers |
| Web caching | Aria | Fast reads, simple queries |

### Example: Create Table with Specific Engine

```python
from dagster import asset
from dagster_mariadb import MariaDBResource, StorageEngine, create_table_with_storage_engine

@asset
def setup_analytics_table(mariadb: MariaDBResource):
    """Create a ColumnStore table for analytics."""
    with mariadb.get_connection() as conn:
        create_table_with_storage_engine(
            table_name="sales_facts",
            schema_name="warehouse",
            columns={
                "id": "INT AUTO_INCREMENT PRIMARY KEY",
                "date": "DATE",
                "product_id": "INT",
                "quantity": "INT",
                "revenue": "DECIMAL(10, 2)",
            },
            connection=conn,
            storage_engine=StorageEngine.ColumnStore,
        )
```

## Parallel Query Execution

MariaDB supports parallel query execution for better performance on large datasets.

### Enable Parallel Execution

```python
from dagster import asset
from dagster_mariadb import MariaDBResource, enable_parallel_query_execution

@asset
def optimize_parallel_queries(mariadb: MariaDBResource):
    """Enable parallel query execution."""
    with mariadb.get_connection() as conn:
        enable_parallel_query_execution(conn, enabled=True)
```

**When to use:**
- Large table scans
- Complex aggregations
- Data warehouse queries
- Multiple CPU cores available

## Galera Cluster Support

Galera provides synchronous multi-master replication for high availability.

### Check Cluster Status

```python
from dagster import asset
from dagster_mariadb import MariaDBResource, check_galera_cluster_status

@asset
def monitor_cluster(mariadb: MariaDBResource):
    """Monitor Galera Cluster status."""
    with mariadb.get_connection() as conn:
        status = check_galera_cluster_status(conn)
        
        if status:
            print(f"Cluster size: {status['cluster_size']}")
            print(f"State: {status['local_state']}")
            print(f"Connected: {status['connected']}")
        else:
            print("Not in Galera Cluster mode")
        
        return status
```

**Benefits:**
- Zero-downtime maintenance
- Automatic failover
- Synchronous replication
- Multi-master writes

## ColumnStore for Analytics

ColumnStore is optimized for analytical workloads and data warehousing.

### ColumnStore Benefits

- **Columnar storage**: Better compression
- **Vectorized operations**: Faster aggregations
- **Distributed architecture**: Scales horizontally
- **Column-based indexing**: Optimized for analytics

### Example: Analytics Data Warehouse

```python
from dagster import asset
from dagster_mariadb import (
    MariaDBResource, 
    StorageEngine,
    create_table_with_storage_engine,
)

@asset
def setup_data_warehouse(mariadb: MariaDBResource):
    """Setup ColumnStore tables for analytics."""
    with mariadb.get_connection() as conn:
        # Fact table
        create_table_with_storage_engine(
            table_name="sales_facts",
            schema_name="analytics",
            columns={
                "id": "INT",
                "date_id": "INT",
                "product_id": "INT",
                "customer_id": "INT",
                "quantity": "INT",
                "amount": "DECIMAL(10, 2)",
            },
            connection=conn,
            storage_engine=StorageEngine.ColumnStore,
        )
        
        # Dimension tables
        create_table_with_storage_engine(
            table_name="products",
            schema_name="analytics",
            columns={
                "id": "INT PRIMARY KEY",
                "name": "VARCHAR(255)",
                "category": "VARCHAR(100)",
            },
            connection=conn,
            storage_engine=StorageEngine.InnoDB,  # Smaller, use InnoDB
        )
```

## Workload-Specific Optimization

### Write-Heavy Workloads

For high-volume writes (e.g., IoT, logs, metrics):

```python
from dagster import asset
from dagster_mariadb import MariaDBResource, optimize_for_write_heavy_load

@asset
def setup_metrics_table(mariadb: MariaDBResource):
    """Setup table optimized for write-heavy load."""
    with mariadb.get_connection() as conn:
        # Use MyRocks for better write performance
        optimize_for_write_heavy_load(
            table_name="sensor_metrics",
            schema_name="iot",
            connection=conn,
            use_myrocks=True,
        )
```

**MyRocks advantages:**
- Better write throughput
- Improved compression
- Faster insert performance
- Lower storage requirements

### Read-Heavy Workloads

For analytics and reporting:

```python
from dagster import asset
from dagster_mariadb import MariaDBResource, StorageEngine, create_table_with_storage_engine

@asset
def setup_read_optimized(mariadb: MariaDBResource):
    """Setup ColumnStore for read-heavy analytics."""
    with mariadb.get_connection() as conn:
        create_table_with_storage_engine(
            table_name="reporting_data",
            schema_name="reports",
            columns={
                "id": "INT",
                "dimension": "VARCHAR(100)",
                "metric1": "DOUBLE",
                "metric2": "DOUBLE",
            },
            connection=conn,
            storage_engine=StorageEngine.ColumnStore,
        )
```

### Mixed Workloads

For transactional workloads with occasional analytics:

```python
from dagster import asset
from dagster_mariadb import MariaDBResource, StorageEngine, create_table_with_storage_engine

@asset
def setup_mixed_workload(mariadb: MariaDBResource):
    """Use InnoDB for transactions, ColumnStore for analytics."""
    with mariadb.get_connection() as conn:
        # Transactional data
        create_table_with_storage_engine(
            table_name="orders",
            schema_name="ecommerce",
            columns={
                "id": "INT AUTO_INCREMENT PRIMARY KEY",
                "customer_id": "INT",
                "total": "DECIMAL(10, 2)",
                "created_at": "TIMESTAMP",
            },
            connection=conn,
            storage_engine=StorageEngine.InnoDB,
        )
        
        # Analytics data (aggregated)
        create_table_with_storage_engine(
            table_name="daily_sales",
            schema_name="analytics",
            columns={
                "date": "DATE",
                "total_orders": "INT",
                "total_revenue": "DECIMAL(10, 2)",
            },
            connection=conn,
            storage_engine=StorageEngine.ColumnStore,
        )
```

## Complete Example

```python
from dagster import Definitions, asset, EnvVar
from dagster_mariadb import (
    MariaDBResource,
    StorageEngine,
    create_table_with_storage_engine,
    check_galera_cluster_status,
    optimize_for_write_heavy_load,
    enable_parallel_query_execution,
)

mariadb_resource = MariaDBResource(
    host="localhost",
    port=3306,
    user="root",
    password=EnvVar("MARIADB_PASSWORD"),
    database="production_db",
)

@asset
def setup_production_database(mariadb: MariaDBResource):
    """Setup production database with optimized storage engines."""
    with mariadb.get_connection() as conn:
        # Enable parallel queries
        enable_parallel_query_execution(conn, enabled=True)
        
        # Check cluster status
        cluster = check_galera_cluster_status(conn)
        if cluster:
            print(f"Running in cluster with {cluster['cluster_size']} nodes")
        
        # Setup transactional tables
        create_table_with_storage_engine(
            table_name="transactions",
            schema_name="finance",
            columns={"id": "INT PRIMARY KEY", "amount": "DECIMAL(10,2)"},
            connection=conn,
            storage_engine=StorageEngine.InnoDB,
        )
        
        # Setup analytics tables
        create_table_with_storage_engine(
            table_name="analytics_facts",
            schema_name="warehouse",
            columns={"id": "INT", "metric": "DOUBLE"},
            connection=conn,
            storage_engine=StorageEngine.ColumnStore,
        )
        
        # Optimize high-write tables
        optimize_for_write_heavy_load(
            table_name="event_logs",
            schema_name="logs",
            connection=conn,
            use_myrocks=True,
        )

defs = Definitions(
    assets=[setup_production_database],
    resources={"mariadb": mariadb_resource},
)
```

## Best Practices

1. **Storage Engines:**
   - Use InnoDB for transactional/OLTP workloads
   - Use ColumnStore for analytical/OLAP workloads
   - Use MyRocks for high-write scenarios
   - Use Aria for temporary/cache tables

2. **Parallel Execution:**
   - Enable only on multi-core systems
   - Best for read-heavy, complex queries
   - Monitor CPU usage

3. **Clustering:**
   - Use Galera for high availability
   - Ensure network latency is low
   - Monitor cluster health regularly

4. **Performance:**
   - Match storage engine to workload
   - Use partitioning for large tables
   - Optimize after bulk loads
   - Monitor query performance

## Further Reading

- [MariaDB Storage Engines](https://mariadb.com/kb/en/storage-engines/)
- [ColumnStore Documentation](https://mariadb.com/kb/en/about-columnstore/)
- [Galera Cluster](https://mariadb.com/kb/en/about-galera-cluster/)
- [MyRocks Engine](https://mariadb.com/kb/en/myrocks/)

