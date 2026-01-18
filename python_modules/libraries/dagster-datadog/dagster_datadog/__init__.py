from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_datadog.resources import DatadogResource, datadog_resource
from dagster_datadog.version import __version__

DagsterLibraryRegistry.register("dagster-datadog", __version__)

__all__ = ["DatadogResource", "datadog_resource"]
