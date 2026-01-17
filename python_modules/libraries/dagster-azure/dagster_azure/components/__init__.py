"""Dagster Azure Components - YAML-configurable resource components for Azure services."""

from dagster_azure.components.adls2 import ADLS2ResourceComponent
from dagster_azure.components.blob import AzureBlobStorageResourceComponent
from dagster_azure.components.io_managers import ADLS2PickleIOManagerComponent

__all__ = [
    "AzureBlobStorageResourceComponent",
    "ADLS2ResourceComponent",
    "ADLS2PickleIOManagerComponent",
]
