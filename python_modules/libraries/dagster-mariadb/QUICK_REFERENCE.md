# Quick Reference: MariaDB Advanced Features in Dagster

## Storage Engines

```python
from dagster_mariadb import StorageEngine, create_table_with_storage_engine, MariaDBResource

# Choose storage engine based on workload:

# 1. InnoDB (Default) - ACID, transactional
create_table_with_storage_engine(
    table_name="orders", schema_name="shop",
    columns={"id": "INT PRIMARY KEY", "amount": "DECIMAL(10,2)"},
    connection=conn, storage_engine=StorageEngine.InnoDB,
)

# 2. MyRocks - High write throughput, compression
create_table_with_storage_engine(
    table_name="logs", schema_name="system",
    columns={"id": "BIGINT PRIMARY KEY", "message": "TEXT"},
    connection=conn, storage_engine=StorageEngine.MyRocks,
)

# 3. ColumnStore - Analytics, OLAP workloads
create_table_with_storage_engine(
    table_name="sales_facts", schema_name="warehouse",
    columns={"date": "DATE", "revenue": "DECIMAL(10,2)"},
    connection=conn, storage_engine=StorageEngine.ColumnStore,
)

# 4. Aria - Temporary tables, cache
create_table_with_storage_engine(
    table_name="cache", schema_name="temp",
    columns={"key": "VARCHAR(255) PRIMARY KEY", "value": "TEXT"},
    connection=conn, storage_engine=StorageEngine.Aria,
)
```

## Parallel Query Execution

```python
from dagster_mariadb import enable_parallel_query_execution

with mariadb.get_connection() as conn:
    enable_parallel_query_execution(conn, enabled=True)
    # Now queries will use parallel execution
```

## Galera Cluster

```python
from dagster_mariadb import check_galera_cluster_status

with mariadb.get_connection() as conn:
    cluster_status = check_galera_cluster_status(conn)
    if cluster_status:
        print(f"Cluster size: {cluster_status['cluster_size']}")
        print(f"State: {cluster_status['local_state']}")
```

## Workload Optimization

```python
from dagster_mariadb import optimize_for_write_heavy_load

# Optimize existing table for write-heavy workload
with mariadb.get_connection() as conn:
    optimize_for_write_heavy_load(
        table_name="metrics", schema_name="monitoring",
        connection=conn, use_myrocks=True,
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

@asset
def setup_production(mariadb: MariaDBResource):
    with mariadb.get_connection() as conn:
        # Enable parallel queries
        enable_parallel_query_execution(conn, enabled=True)
        
        # Check cluster
        cluster = check_galera_cluster_status(conn)
        print(f"Cluster: {cluster}")
        
        # Setup tables with appropriate engines
        # Analytics: ColumnStore
        create_table_with_storage_engine(
            table_name="analytics", schema_name="warehouse",
            columns={"id": "INT", "value": "DOUBLE"},
            connection=conn, storage_engine=StorageEngine.ColumnStore,
        )
        
        # High writes: MyRocks  
        optimize_for_write_heavy_load(
            table_name="events", schema_name="logs",
            connection=conn, use_myrocks=True,
        )

mariadb = MariaDBResource(
    host="localhost", user="root",
    password=EnvVar("MARIADB_PASSWORD"),
    database="production",
)

defs = Definitions(
    assets=[setup_production],
    resources={"mariadb": mariadb},
)
```

## Decision Matrix

| Workload Type | Storage Engine | Why |
|--------------|----------------|-----|
| Financial transactions | InnoDB | ACID compliance |
| IoT sensor data | MyRocks | High write throughput |
| Analytics dashboard | ColumnStore | Fast aggregations |
| Web session cache | Aria | Low overhead |
| Multi-server queries | Spider | Distributed federation |
| Time-series metrics | MyRocks | Write + compression |

## Further Reading

See [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) for detailed documentation.

