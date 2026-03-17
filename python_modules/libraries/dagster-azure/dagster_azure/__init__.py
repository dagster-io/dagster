from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_azure.components.adls2 import ADLS2ResourceComponent as ADLS2ResourceComponent
from dagster_azure.components.blob import (
    AzureBlobStorageResourceComponent as AzureBlobStorageResourceComponent,
)
from dagster_azure.version import __version__

DagsterLibraryRegistry.register("dagster-azure", __version__)
