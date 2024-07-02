from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__
from .resources import PrometheusResource, prometheus_resource

DagsterLibraryRegistry.register("dagster-prometheus", __version__)

__all__ = ["prometheus_resource", "PrometheusResource"]
