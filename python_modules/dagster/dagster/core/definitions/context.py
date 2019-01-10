from collections import namedtuple

from dagster import check

from dagster.core.types import Field, Dict, String
from dagster.core.execution_context import ExecutionContext
from dagster.core.system_config.objects import DEFAULT_CONTEXT_NAME

from dagster.utils.logging import level_from_string, define_colored_console_logger

from .resource import ResourceDefinition


class PipelineContextDefinition(object):
    '''Pipelines declare the different context types they support, in the form
    of PipelineContextDefinitions. For example a pipeline could declare a context
    definition for different operating environments: unittest, integration tests,
    production and so forth. The use provides context function that returns an
    ExecutionContext that is passed to every solid. One can hang resources
    (such as db connections) off of that context. Thus the pipeline author
    has complete control over how the author of each individual solid within
    the pipeline interacts with its operating environment.

    The PipelineContextDefinition is passed to the PipelineDefinition in
    a dictionary key'ed by its name so the name is not present in this object.

    Attributes:
        config_field (Field): The configuration for the pipeline context.

context_fn (callable):
            Signature is (pipeline: PipelineDefintion, config_value: Any) => ExecutionContext

            A callable that either returns *or* yields an ExecutionContext.

        description (str): A description of what this context represents
    '''

    @staticmethod
    def passthrough_context_definition(context_params):
        '''Create a context definition from a pre-existing context. This can be useful
        in testing contexts where you may want to create a context manually and then
        pass it into a one-off PipelineDefinition

        Args:
            context (ExecutionContext): The context that will provided to the pipeline.
        Returns:
            PipelineContextDefinition: The passthrough context definition.
        '''

        check.inst_param(context_params, 'context', ExecutionContext)
        context_definition = PipelineContextDefinition(context_fn=lambda *_args: context_params)
        return {DEFAULT_CONTEXT_NAME: context_definition}

    def __init__(self, context_fn=None, config_field=None, resources=None, description=None):
        '''
        Args:
            context_fn (callable):
                Signature of context_fn:
                (pipeline: PipelineDefintion, config_value: Any) => ExecutionContext

                Returns *or* yields an ExecutionContext.

                If it yields a context, the code after the yield executes after pipeline
                completion, just like a python context manager.

                Environment-specific resources should be placed in the "resources" argument
                to an execution context. This argument can be *anything* and it is made
                avaiable to every solid in the pipeline. A typical pattern is to have this
                resources object be a namedtuple, where each property is an object that
                manages a particular resource, e.g. aws, a local filesystem manager, etc.

            config_field (Field):
                Define the configuration for the context

            description (str): Description of the context definition.
        '''
        self.config_field = check.opt_inst_param(config_field, 'config_field', Field)
        self.context_fn = check.opt_callable_param(
            context_fn, 'context_fn', lambda *args, **kwargs: ExecutionContext()
        )
        self.resources = check.opt_dict_param(
            resources, 'resources', key_type=str, value_type=ResourceDefinition
        )
        self.description = description
        self.resources_type = namedtuple('Resources', list(resources.keys())) if resources else None


def default_pipeline_context_definitions():
    def _default_context_fn(info):
        log_level = level_from_string(info.config['log_level'])
        context = ExecutionContext(
            loggers=[define_colored_console_logger('dagster', level=log_level)]
        )
        return context

    default_context_def = PipelineContextDefinition(
        config_field=Field(
            Dict({'log_level': Field(dagster_type=String, is_optional=True, default_value='INFO')})
        ),
        context_fn=_default_context_fn,
    )
    return {DEFAULT_CONTEXT_NAME: default_context_def}
