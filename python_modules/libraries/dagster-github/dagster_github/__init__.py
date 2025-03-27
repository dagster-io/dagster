from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_github.resources import GithubResource, github_resource
from dagster_github.version import __version__

DagsterLibraryRegistry.register("dagster-github", __version__)

__all__ = ["GithubResource", "github_resource"]
