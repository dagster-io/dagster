from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_cloud_cli.version import __version__

DagsterLibraryRegistry.register("dagster-cloud-cli", __version__)
