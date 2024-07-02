from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__
from .resources import SSHResource, ssh_resource

DagsterLibraryRegistry.register("dagster-ssh", __version__)

__all__ = ["ssh_resource", "SSHResource"]
