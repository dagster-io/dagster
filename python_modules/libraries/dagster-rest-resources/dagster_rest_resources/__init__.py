from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_rest_resources.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-rest-resources", __version__)
