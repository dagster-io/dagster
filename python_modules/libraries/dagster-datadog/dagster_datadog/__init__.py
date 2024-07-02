from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__
from .resources import DatadogResource, datadog_resource

DagsterLibraryRegistry.register("dagster-datadog", __version__)

__all__ = ["datadog_resource", "DatadogResource"]
