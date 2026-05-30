import dagster_cloud
import dagster_cloud_cli
from dagster._core.libraries import DagsterLibraryRegistry


def test_library_registry():
    library_registry = DagsterLibraryRegistry.get()
    assert library_registry["dagster-cloud"] == dagster_cloud.__version__
    assert library_registry["dagster-cloud-cli"] == dagster_cloud_cli.__version__
