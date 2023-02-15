from dagster._core.libraries import DagsterLibraryRegistry

from .resources import github_resource
from .version import __version__

DagsterLibraryRegistry.register("dagster-github", __version__)

__all__ = ["github_resource"]
