from dagster_cloud_cli.version import __version__
from dagster_shared.libraries import DagsterLibraryRegistry

DagsterLibraryRegistry.register("dagster-cloud-cli", __version__)
