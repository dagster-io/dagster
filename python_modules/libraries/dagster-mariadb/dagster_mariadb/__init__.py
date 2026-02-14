from dagster._core.libraries import DagsterLibraryRegistry

from dagster_mariadb.resource import MariaDBResource
from dagster_mariadb.io_manager import MariaDBPandasIOManager
from dagster_mariadb.partitioned_io_manager import MariaDBPartitionedIOManager
from dagster_mariadb.version import __version__
from dagster_mariadb.partitioned_io_manager_v2 import MariaDBPartitionedPandasIOManager
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
from dagster_mariadb.utils import (
    MariaDBConnectionUnion,
    get_pymysql_connection_from_string,
    get_connection_params_from_string,
    is_pymysql_connection,
    is_sqlalchemy_connection,
    encode_connection_string_component,
    decode_connection_string_component,
)
# Import partitioning features
from dagster_mariadb.partitions import (
    PartitionType,
    PartitionStrategy,
    create_partitioned_table,
    add_partition,
    drop_partition,
    truncate_partition,
    reorganize_partitions,
    get_partition_info,
    optimize_partition,
    check_partition,
    repair_partition,
)

DagsterLibraryRegistry.register("dagster-mariadb", __version__)

__all__ = [
    "MariaDBResource",
    "MariaDBPandasIOManager",
    "MariaDBPartitionedIOManager",
    "MariaDBPartitionedPandasIOManager",
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
    # Partitioning features
    "PartitionType",
    "PartitionStrategy",
    "create_partitioned_table",
    "add_partition",
    "drop_partition",
    "truncate_partition",
    "reorganize_partitions",
    "get_partition_info",
    "optimize_partition",
    "check_partition",
    "repair_partition",
    "MariaDBConnectionUnion",
    "get_pymysql_connection_from_string",
    "get_connection_params_from_string",
    "is_pymysql_connection",
    "is_sqlalchemy_connection",
    "encode_connection_string_component",
    "decode_connection_string_component",
]