from dagster._core.libraries import DagsterLibraryRegistry

from .asset_factory import define_dagstermill_asset as define_dagstermill_asset
from .context import DagstermillExecutionContext as DagstermillExecutionContext
from .errors import DagstermillError as DagstermillError
from .factory import define_dagstermill_op as define_dagstermill_op
from .io_managers import (
    ConfigurableLocalOutputNotebookIOManager as ConfigurableLocalOutputNotebookIOManager,
    local_output_notebook_io_manager as local_output_notebook_io_manager,
)
from .manager import MANAGER_FOR_NOTEBOOK_INSTANCE as _MANAGER_FOR_NOTEBOOK_INSTANCE
from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagstermill", __version__)

get_context = _MANAGER_FOR_NOTEBOOK_INSTANCE.get_context

yield_result = _MANAGER_FOR_NOTEBOOK_INSTANCE.yield_result

yield_event = _MANAGER_FOR_NOTEBOOK_INSTANCE.yield_event

_reconstitute_job_context = _MANAGER_FOR_NOTEBOOK_INSTANCE.reconstitute_job_context

_teardown = _MANAGER_FOR_NOTEBOOK_INSTANCE.teardown_resources

_load_input_parameter = _MANAGER_FOR_NOTEBOOK_INSTANCE.load_input_parameter
