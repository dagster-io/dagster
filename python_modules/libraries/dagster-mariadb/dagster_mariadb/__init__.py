from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_mariadb.resource import MariaDBResource
from dagster_mariadb.io_manager import MariaDBPandasIOManager, mariadb_pandas_io_manager
from dagster_mariadb.version import __version__

DagsterLibraryRegistry.register("dagster-mariadb", __version__)

__all__ = [
    "MariaDBResource",
    "MariaDBPandasIOManager", 
    "mariadb_pandas_io_manager",
]
