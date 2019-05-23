from dagster import check
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.context.transform import AbstractTransformExecutionContext


class DagstermillInNotebookExecutionContext(AbstractTransformExecutionContext):
    def __init__(self, pipeline_context):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        self._pipeline_context = pipeline_context

    def has_tag(self, key):
        return self._pipeline_context.has_tag(key)

    def get_tag(self, key):
        return self._pipeline_context.get_tag(key)

    @property
    def run_id(self):
        return self._pipeline_context.run_id

    @property
    def environment_config(self):
        return self._pipeline_context.environment_config

    @property
    def pipeline_def(self):
        return self._pipeline_context.pipeline_def

    @property
    def resources(self):
        return self._pipeline_context.resources

    @property
    def log(self):
        return self._pipeline_context.log

    @property
    def context(self):
        return self._pipeline_context.context

    @property
    def config(self):
        check.not_implemented('Cannot access solid config in dagstermill exploratory context')

    @property
    def solid_def(self):
        check.not_implemented('Cannot access solid_def in dagstermill exploratory context')

    @property
    def solid(self):
        check.not_implemented('Cannot access solid in dagstermill exploratory context')
