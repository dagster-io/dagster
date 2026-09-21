from dagster._core.libraries import DagsterLibraryRegistry

from dagster_cloud.instance import DagsterCloudAgentInstance as DagsterCloudAgentInstance
from dagster_cloud.storage.compute_logs import CloudComputeLogManager as CloudComputeLogManager
from dagster_cloud.version import __version__

DagsterLibraryRegistry.register("dagster-cloud", __version__)
