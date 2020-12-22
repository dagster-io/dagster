from dagster.core.utils import check_dagster_package_version

from .context import DagstermillExecutionContext
from .errors import DagstermillError
from .manager import MANAGER_FOR_NOTEBOOK_INSTANCE as _MANAGER_FOR_NOTEBOOK_INSTANCE
from .solids import define_dagstermill_solid
from .version import __version__

check_dagster_package_version("dagstermill", __version__)

get_context = _MANAGER_FOR_NOTEBOOK_INSTANCE.get_context

yield_result = _MANAGER_FOR_NOTEBOOK_INSTANCE.yield_result

yield_event = _MANAGER_FOR_NOTEBOOK_INSTANCE.yield_event

_reconstitute_pipeline_context = _MANAGER_FOR_NOTEBOOK_INSTANCE.reconstitute_pipeline_context

_teardown = _MANAGER_FOR_NOTEBOOK_INSTANCE.teardown_resources

_load_parameter = _MANAGER_FOR_NOTEBOOK_INSTANCE.load_parameter
