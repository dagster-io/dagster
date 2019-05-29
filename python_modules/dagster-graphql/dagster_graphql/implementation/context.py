from dagster import check, ExecutionTargetHandle
from .pipeline_run_storage import PipelineRunStorage
from .pipeline_execution_manager import PipelineExecutionManager


class DagsterGraphQLContext(object):
    def __init__(
        self, handle, pipeline_runs, execution_manager, raise_on_error=False, version=None
    ):
        self._handle = check.inst_param(handle, 'handle', ExecutionTargetHandle)
        self.repository_definition = handle.build_repository_definition()
        self.pipeline_runs = check.inst_param(pipeline_runs, 'pipeline_runs', PipelineRunStorage)
        self.execution_manager = check.inst_param(
            execution_manager, 'pipeline_execution_manager', PipelineExecutionManager
        )
        self.raise_on_error = check.bool_param(raise_on_error, 'raise_on_error')
        self.version = version

    def get_handle(self):
        return self._handle
