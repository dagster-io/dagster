from dagster import check
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.context.transform import AbstractComputeExecutionContext


class DagstermillInPipelineExecutionContext(AbstractComputeExecutionContext):
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
        return self._pipeline_context.scoped_resources_builder.build()

    @property
    def run_config(self):
        return self._pipeline_context.run_config

    @property
    def log(self):
        return self._pipeline_context.log

    @property
    def solid_def(self):
        return self.pipeline_def.solid_defs[0]

    @property
    def solid(self):
        return self.pipeline_def.solids[0]

    @property
    def solid_config(self):
        solid_config = self.environment_config.solids.get(self.solid.name)
        return solid_config.config if solid_config else None
