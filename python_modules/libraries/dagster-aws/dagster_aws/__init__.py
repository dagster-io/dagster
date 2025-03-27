from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_aws.version import __version__

DagsterLibraryRegistry.register("dagster-aws", __version__)
