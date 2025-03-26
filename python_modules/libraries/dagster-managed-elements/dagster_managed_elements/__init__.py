from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_managed_elements.types import *  # noqa: F403  # pyright: ignore (reportWildcardImportFromLibrary)
from dagster_managed_elements.version import __version__

DagsterLibraryRegistry.register("dagster-managed-elements", __version__)
