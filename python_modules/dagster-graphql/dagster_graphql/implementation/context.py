from dagster import check, ExecutionTargetHandle
from .pipeline_run_storage import PipelineRunStorage
from .pipeline_execution_manager import PipelineExecutionManager


class DagsterGraphQLContext(object):
    def __init__(
        self, handle, pipeline_runs, execution_manager, raise_on_error=False, version=None
    ):
        self._handle = check.inst_param(handle, 'handle', ExecutionTargetHandle)
        self.pipeline_runs = check.inst_param(pipeline_runs, 'pipeline_runs', PipelineRunStorage)
        self.execution_manager = check.inst_param(
            execution_manager, 'pipeline_execution_manager', PipelineExecutionManager
        )
        self.raise_on_error = check.bool_param(raise_on_error, 'raise_on_error')
        self.version = version
        self.repository_definition = self.get_handle().build_repository_definition()

    def get_handle(self):
        return self._handle

    def get_repository(self):
        return self.repository_definition

    def get_pipeline(self, pipeline_name):
        orig_handle = self.get_handle()
        if orig_handle.is_resolved_to_pipeline:
            pipeline_def = orig_handle.build_pipeline_definition()
            check.invariant(
                pipeline_def.name == pipeline_name,
                '''Dagster GraphQL Context resolved pipeline with name {handle_pipeline_name},
                couldn't resolve {pipeline_name}'''.format(
                    handle_pipeline_name=pipeline_def.name, pipeline_name=pipeline_name
                ),
            )
            return pipeline_def
        return self.get_handle().with_pipeline_name(pipeline_name).build_pipeline_definition()
