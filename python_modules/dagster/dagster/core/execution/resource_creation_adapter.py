from dagster import check

from dagster.core.definitions import ModeDefinition, PipelineContextDefinition
from dagster.core.system_config.objects import EnvironmentConfig

from .user_context import ExecutionContext


class ResourceCreationAdapter:
    '''
    This class exists temporarily to handle the transition period where we have three ways
    of creating resources:
    1) Override in a context function
    2) Specifiying a set of resources on a context definition
    3) Specifiying a set of resources on a mode definition

    When we are done with this refactor only 3 will be necessary. The elimination of this
    class will be a good marker of when this is "done" -- schrockn (05-08-2019)
    '''

    def __init__(self, execution_context, environment_config, context_definition, mode_definition):
        self.execution_context = check.inst_param(
            execution_context, 'execution_context', ExecutionContext
        )

        self.environment_config = check.inst_param(
            environment_config, 'environment_config', EnvironmentConfig
        )

        check.invariant(context_definition or mode_definition)
        check.invariant(not (context_definition and mode_definition))

        self.context_definition = check.opt_inst_param(
            context_definition, 'context_definition', PipelineContextDefinition
        )

        self.mode_definition = check.opt_inst_param(
            mode_definition, 'mode_definition', ModeDefinition
        )

    @property
    def is_resource_override(self):
        return bool(self.execution_context.resources)

    def get_override_resources(self):
        check.invariant(self.is_resource_override)
        return self.execution_context.resources

    def get_resource_config(self, resource_name):
        if self.context_definition:
            check.invariant(self.environment_config.resources is None)
            return self.environment_config.context.resources.get(resource_name, {}).get('config')
        else:
            check.invariant(self.environment_config.context is None)
            return self.environment_config.resources.get(resource_name, {}).get('config')

    @property
    def resource_defs(self):
        return (
            self.context_definition.resource_defs
            if self.context_definition
            else self.mode_definition.resource_defs
        )
