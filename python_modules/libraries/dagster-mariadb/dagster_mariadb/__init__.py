from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_mariadb.resource import MariaDBResource
from dagster_mariadb.io_manager import MariaDBPandasIOManager, mariadb_pandas_io_manager
from dagster_mariadb.version import __version__

# Import advanced MariaDB features
from dagster_mariadb.advanced_features import (
    StorageEngine,
    create_table_with_storage_engine,
    enable_parallel_query_execution,
    create_columnstore_table,
    check_galera_cluster_status,
    optimize_for_write_heavy_load,
    create_distributed_table_via_spider,
    get_storage_engine_info,
    setup_analytics_warehouse,
)

DagsterLibraryRegistry.register("dagster-mariadb", __version__)

__all__ = [
    "MariaDBResource",
    "MariaDBPandasIOManager",
    "mariadb_pandas_io_manager",
    # Advanced features
    "StorageEngine",
    "create_table_with_storage_engine",
    "enable_parallel_query_execution",
    "create_columnstore_table",
    "check_galera_cluster_status",
    "optimize_for_write_heavy_load",
    "create_distributed_table_via_spider",
    "get_storage_engine_info",
    "setup_analytics_warehouse",
]

