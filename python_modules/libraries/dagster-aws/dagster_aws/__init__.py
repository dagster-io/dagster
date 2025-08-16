from dagster_aws.version import __version__
from dagster_shared.libraries import DagsterLibraryRegistry

DagsterLibraryRegistry.register("dagster-aws", __version__)
