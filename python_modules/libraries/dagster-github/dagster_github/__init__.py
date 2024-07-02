from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__
from .resources import GithubResource, github_resource

DagsterLibraryRegistry.register("dagster-github", __version__)

__all__ = ["github_resource", "GithubResource"]
