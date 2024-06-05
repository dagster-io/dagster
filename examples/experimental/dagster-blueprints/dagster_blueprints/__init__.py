from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-blueprints", __version__)
