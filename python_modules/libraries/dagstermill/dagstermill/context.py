from dagster import check
from dagster.core.execution.context.compute import AbstractComputeExecutionContext
from dagster.core.execution.context.system import SystemPipelineExecutionContext


class DagstermillExecutionContext(AbstractComputeExecutionContext):
    '''Dagstermill-specific execution context.

    Do not initialize directly: use :func:`dagstermill.get_context`.
    '''

    def __init__(self, pipeline_context, resource_keys_to_init, solid_config=None):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        self._pipeline_context = pipeline_context
        if solid_config:
            self._solid_config = solid_config
        else:
            self._solid_config = None

        self._resource_keys_to_init = check.set_param(
            resource_keys_to_init, 'resource_keys_to_init', of_type=str
        )

    def has_tag(self, key):
        '''Check if a logging tag is defined on the context.

        Args:
            key (str): The key to check.

        Returns:
            bool
        '''
        return self._pipeline_context.has_tag(key)

    def get_tag(self, key):
        '''Get a logging tag defined on the context.

        Args:
            key (str): The key to get.

        Returns:
            str
        '''
        return self._pipeline_context.get_tag(key)

    @property
    def run_id(self):
        '''str: The run_id for the context.'''
        return self._pipeline_context.run_id

    @property
    def environment_dict(self):
        '''dict: The environment_dict for the context.'''
        return self._pipeline_context.environment_dict

    @property
    def environment_config(self):
        ''':class:`dagster.EnvironmentConfig`: The environment_config for the context'''
        return self._pipeline_context.environment_config

    @property
    def logging_tags(self):
        '''dict: The logging tags for the context.'''
        return self._pipeline_context.logging_tags

    @property
    def pipeline_def(self):
        ''':class:`dagster.PipelineDefinition`: The pipeline definition for the context.

        This will be a dagstermill-specific shim.
        '''
        return self._pipeline_context.pipeline_def

    @property
    def resources(self):
        '''collections.namedtuple: A dynamically-created type whose properties allow access to
        resources.'''
        return self._pipeline_context.scoped_resources_builder.build(
            required_resource_keys=self._resource_keys_to_init,
        )

    @property
    def pipeline_run(self):
        ''':class:`dagster.PipelineRun`: The pipeline run for the context.'''
        return self._pipeline_context.pipeline_run

    @property
    def log(self):
        ''':class:`dagster.LogManager`: The log manager for the context.

        Call, e.g., ``log.info()`` to log messages through the Dagster machinery.
        '''
        return self._pipeline_context.log

    @property
    def solid_def(self):
        ''':class:`dagster.SolidDefinition`: The solid definition for the context.

        In interactive contexts, this may be a dagstermill-specific shim, depending whether a
        solid definition was passed to ``dagstermill.get_context``.
        '''
        return self.pipeline_def.all_solid_defs[0]

    @property
    def solid(self):
        ''':class:`dagster.Solid`: The solid for the context.

        In interactive contexts, this may be a dagstermill-specific shim, depending whether a
        solid definition was passed to ``dagstermill.get_context``.
        '''
        return self.pipeline_def.solids[0]

    @property
    def solid_config(self):
        '''collections.namedtuple: A dynamically-created type whose properties allow access to
        solid-specific config.'''
        if self._solid_config:
            return self._solid_config

        solid_config = self.environment_config.solids.get(self.solid.name)
        return solid_config.config if solid_config else None
