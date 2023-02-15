from dagster._core.libraries import DagsterLibraryRegistry

from .resources import SSHResource, ssh_resource
from .version import __version__

DagsterLibraryRegistry.register("dagster-ssh", __version__)

__all__ = ["ssh_resource", "SSHResource"]
