from dagster import check

from dagster.core.types import Field, Dict
from dagster.core.types.field_utils import check_user_facing_opt_field_param
from dagster.core.execution.user_context import ExecutionContext
from dagster.core.system_config.objects import DEFAULT_CONTEXT_NAME

from dagster.utils.logging import LogLevelEnum, level_from_string

from .resource import ResourceDefinition


class PipelineContextDefinition(object):
    '''Defines a context type supported by a pipeline.

    Pipelines declare the different context types they support, in the form
    of PipelineContextDefinitions. For example a pipeline could declare a context
    definition for different operating environments: unittest, integration tests,
    production and so forth. The user provides a context function that returns an
    ``ExecutionContext`` that is passed to every solid. One can hang resources
    (such as db connections) off of that context. Thus the pipeline author
    has complete control over how the author of each individual solid within
    the pipeline interacts with its operating environment.

    The ``PipelineContextDefinition`` is passed to the ``PipelineDefinition`` in
    a dictionary keyed by its name so the name is not present in this object.

    Args:
        context_fn (Callable):
            Signature of context_fn:
            (pipeline: PipelineDefintion, config_value: Any) => ExecutionContext

            Returns *or* yields an ExecutionContext.

            If it yields a context, the code after the yield executes after pipeline
            completion, just like a python context manager.

        config_field (Field):
            Define the configuration for the context

        description (str)

    Attributes:
        config_field (Field): The configuration for the pipeline context.

        context_fn (callable):
            Signature is (**pipeline**: `PipelineDefintion`, **config_value**: `Any`) :
            `ExecutionContext`.

            A callable that either returns *or* yields an ``ExecutionContext``.

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
        if config_field is None and context_fn is None:
            config_field = _default_config_field()
            context_fn = _default_context_fn

        self.config_field = check_user_facing_opt_field_param(
            config_field, 'config_field', 'of a PipelineContextDefinition'
        )
        self.context_fn = check.opt_callable_param(
            context_fn, 'context_fn', lambda *args, **kwargs: ExecutionContext()
        )
        self.resource_defs = check.opt_dict_param(
            resources, 'resources', key_type=str, value_type=ResourceDefinition
        )
        self.description = description


def _default_context_fn(init_context):
    log_level = level_from_string(init_context.context_config['log_level'])
    return ExecutionContext.console_logging(log_level)


def _default_config_field():
    return Field(Dict({'log_level': Field(LogLevelEnum, is_optional=True, default_value='INFO')}))


def default_pipeline_context_definitions():
    return {
        DEFAULT_CONTEXT_NAME: PipelineContextDefinition(
            config_field=_default_config_field(), context_fn=_default_context_fn
        )
    }
