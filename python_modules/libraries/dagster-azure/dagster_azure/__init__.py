from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_azure.components.adls2 import ADLS2ResourceComponent
from dagster_azure.components.blob import AzureBlobStorageResourceComponent
from dagster_azure.components.io_managers import ADLS2PickleIOManagerComponent
from dagster_azure.version import __version__

DagsterLibraryRegistry.register("dagster-azure", __version__)

__all__ = [
    "ADLS2PickleIOManagerComponent",
    "ADLS2ResourceComponent",
    "AzureBlobStorageResourceComponent",
    "__version__",
]
