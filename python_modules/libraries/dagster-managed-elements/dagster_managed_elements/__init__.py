from dagster._core.libraries import DagsterLibraryRegistry

from .types import *  # noqa: F403
from .version import __version__

DagsterLibraryRegistry.register("dagster-managed-elements", __version__)
