from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__

DagsterLibraryRegistry.register("dagster-embedded-elt", __version__)
