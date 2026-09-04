from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_prefect.pipes_task import PipesPrefectTaskClient as PipesPrefectTaskClient
from dagster_prefect.resource import PrefectResource as PrefectResource
from dagster_prefect.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-prefect", __version__)
