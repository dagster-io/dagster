from dagster import check
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.context.transform import AbstractTransformExecutionContext


class DagstermillInNotebookExecutionContext(AbstractTransformExecutionContext):
    def __init__(self, pipeline_context, out_of_pipeline=False):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        self._pipeline_context = pipeline_context
        self.out_of_pipeline = out_of_pipeline

    def has_tag(self, key):
        return self._pipeline_context.has_tag(key)

    def get_tag(self, key):
        return self._pipeline_context.get_tag(key)

    @property
    def run_id(self):
        return self._pipeline_context.run_id

    @property
    def environment_dict(self):
        return self._pipeline_context.environment_dict

    @property
    def environment_config(self):
        return self._pipeline_context.environment_config

    @property
    def logging_tags(self):
        return self._pipeline_context.logging_tags

    @property
    def pipeline_def(self):
        return self._pipeline_context.pipeline_def

    @property
    def resources(self):
        if self.out_of_pipeline:
            check.failed('Cannot access resources in dagstermill exploratory context')
        return self._pipeline_context.resources

    @property
    def log(self):
        return self._pipeline_context.log

    @property
    def solid_def(self):
        if self.out_of_pipeline:
            check.failed('Cannot access solid_def in dagstermill exploratory context')
        return self._pipeline_context.solid_def

    @property
    def solid(self):
        if self.out_of_pipeline:
            check.failed('Cannot access solid in dagstermill exploratory context')
        return self._pipeline_context.solid
