from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_prometheus.resources import PrometheusResource, prometheus_resource
from dagster_prometheus.version import __version__

DagsterLibraryRegistry.register("dagster-prometheus", __version__)

__all__ = ["PrometheusResource", "prometheus_resource"]
