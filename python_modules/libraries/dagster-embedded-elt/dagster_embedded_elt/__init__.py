from dagster._core.libraries import DagsterLibraryRegistry

from dagster_embedded_elt.version import __version__

DagsterLibraryRegistry.register("dagster-embedded-elt", __version__)
