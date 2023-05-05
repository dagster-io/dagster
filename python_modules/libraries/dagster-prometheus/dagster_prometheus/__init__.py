from dagster._core.libraries import DagsterLibraryRegistry

from .resources import prometheus_resource
from .version import __version__

DagsterLibraryRegistry.register("dagster-prometheus", __version__)

__all__ = ["prometheus_resource"]
