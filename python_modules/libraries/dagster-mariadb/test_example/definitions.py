from dagster import Definitions
from dagster_mariadb import MariaDBResource, MariaDBPandasIOManager, MariaDBPartitionedPandasIOManager
from .assets import (
    raw_airports,
    raw_airlines,
    raw_routes,
    airports_with_airline_count,
    route_statistics
)
from .advanced_assets import (
    storage_engine_info,
    test_innodb_table,
    test_aria_table,
    test_optimize_write_heavy,
    test_galera_cluster_status,
    test_analytics_warehouse,
    compare_storage_engines,
    test_multi_engine_performance,
    test_columnstore_table,
    advanced_features_summary,
)
from .partition_test_assets import (
    daily_sales,
    monthly_revenue,
    weekly_metrics,
    regional_inventory,
    multi_dim_transactions,
    daily_sales_summary,
    partition_metadata_report,
    query_specific_partition,
    partition_maintenance,
    partition_performance_test,
    partition_test_summary,
)

# Create the MariaDB resource
mariadb_resource = MariaDBResource(
    host="localhost",
    port=3306,
    user="root",
    password="rootpw123",
    database="flightdb2"
)

# Create standard IO manager for non-partitioned assets
mariadb_io_manager = MariaDBPandasIOManager(
    mariadb=mariadb_resource,
    schema_name="flightdb2",
    mode="replace"
)

# Create partitioned IO managers
# Version 2: Native MariaDB partitioning (when supported)
partitioned_io_manager = MariaDBPartitionedPandasIOManager(
    mariadb=mariadb_resource,
    schema_name="flightdb2",
    mode="replace",
    use_native_partitioning=True,  # Enable native partitioning
    storage_engine="InnoDB",
    default_partition_column="partition_date"
)

# Application-level partitioning for multi-dimensional
partitioned_io_manager_app_level = MariaDBPartitionedPandasIOManager(
    mariadb=mariadb_resource,
    schema_name="flightdb2",
    mode="replace",
    use_native_partitioning=False,  # Disable native for multi-dim
    default_partition_column="partition_date"
)

defs = Definitions(
    assets=[
        # Original assets
        raw_airports,
        raw_airlines,
        raw_routes,
        airports_with_airline_count,
        route_statistics,
        # Advanced features
        storage_engine_info,
        test_innodb_table,
        test_aria_table,
        test_optimize_write_heavy,
        test_galera_cluster_status,
        test_analytics_warehouse,
        compare_storage_engines,
        test_multi_engine_performance,
        test_columnstore_table,
        advanced_features_summary,
        # Partition tests
        daily_sales,
        monthly_revenue,
        weekly_metrics,
        regional_inventory,
        multi_dim_transactions,
        daily_sales_summary,
        partition_metadata_report,
        query_specific_partition,
        partition_maintenance,
        partition_performance_test,
        partition_test_summary,
    ],
    resources={
        "mariadb": mariadb_resource,
        "mariadb_io_manager": mariadb_io_manager,  # Added back for original assets
        "partitioned_io_manager": partitioned_io_manager,
        "partitioned_io_manager_app_level": partitioned_io_manager_app_level,
    }
)