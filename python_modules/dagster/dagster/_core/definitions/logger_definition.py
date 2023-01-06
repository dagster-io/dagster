import logging
from typing import TYPE_CHECKING, Any, Callable, Optional, Union, cast, overload

import dagster._check as check
from dagster._annotations import public
from dagster._core.errors import DagsterInvalidInvocationError

from ..decorator_utils import get_function_params
from .config import is_callable_valid_config_arg
from .configurable import AnonymousConfigurableDefinition
from .definition_config_schema import (
    CoercableToConfigSchema,
    convert_user_facing_definition_config_schema,
)

if TYPE_CHECKING:
    from dagster._core.definitions import JobDefinition, PipelineDefinition
    from dagster._core.execution.context.logger import InitLoggerContext, UnboundInitLoggerContext

    InitLoggerFunction = Callable[[InitLoggerContext], logging.Logger]


class LoggerDefinition(AnonymousConfigurableDefinition):
    """Core class for defining loggers.

    Loggers are job-scoped logging handlers, which will be automatically invoked whenever
    dagster messages are logged from within a job.

    Args:
        logger_fn (Callable[[InitLoggerContext], logging.Logger]): User-provided function to
            instantiate the logger. This logger will be automatically invoked whenever the methods
            on ``context.log`` are called from within job/pipeline compute logic.
        config_schema (Optional[ConfigSchema]): The schema for the config. Configuration data available in
            `init_context.logger_config`. If not set, Dagster will accept any config provided.
        description (Optional[str]): A human-readable description of this logger.
    """

    def __init__(
        self,
        logger_fn: "InitLoggerFunction",
        config_schema: Any = None,
        description: Optional[str] = None,
    ):
        self._logger_fn = check.callable_param(logger_fn, "logger_fn")
        self._config_schema = convert_user_facing_definition_config_schema(config_schema)
        self._description = check.opt_str_param(description, "description")

    def __call__(self, *args, **kwargs):
        from dagster._core.execution.context.logger import UnboundInitLoggerContext

        from .logger_invocation import logger_invocation_result

        if len(args) == 0 and len(kwargs) == 0:
            raise DagsterInvalidInvocationError(
                "Logger initialization function has context argument, but no context argument was "
                "provided when invoking."
            )
        if len(args) + len(kwargs) > 1:
            raise DagsterInvalidInvocationError(
                "Initialization of logger received multiple arguments. Only a first "
                "positional context parameter should be provided when invoking."
            )

        context_param_name = get_function_params(self.logger_fn)[0].name

        if args:
            context = check.opt_inst_param(
                args[0],
                context_param_name,
                UnboundInitLoggerContext,
                default=UnboundInitLoggerContext(logger_config=None, pipeline_def=None),
            )
            return logger_invocation_result(self, context)
        else:
            if context_param_name not in kwargs:
                raise DagsterInvalidInvocationError(
                    f"Logger initialization expected argument '{context_param_name}'."
                )
            context = check.opt_inst_param(
                kwargs[context_param_name],
                context_param_name,
                UnboundInitLoggerContext,
                default=UnboundInitLoggerContext(logger_config=None, pipeline_def=None),
            )

            return logger_invocation_result(self, context)

    @public  # type: ignore
    @property
    def logger_fn(self) -> "InitLoggerFunction":
        return self._logger_fn

    @public  # type: ignore
    @property
    def config_schema(self) -> Any:
        return self._config_schema

    @public  # type: ignore
    @property
    def description(self) -> Optional[str]:
        return self._description

    def copy_for_configured(
        self,
        description: Optional[str],
        config_schema: Any,
    ) -> "LoggerDefinition":
        return LoggerDefinition(
            config_schema=config_schema,
            description=description or self.description,
            logger_fn=self.logger_fn,
        )


@overload
def logger(
    config_schema: CoercableToConfigSchema, description: Optional[str] = ...
) -> Callable[["InitLoggerFunction"], "LoggerDefinition"]:
    ...


@overload
def logger(
    config_schema: "InitLoggerFunction", description: Optional[str] = ...
) -> "LoggerDefinition":
    ...


def logger(
    config_schema: Union[CoercableToConfigSchema, "InitLoggerFunction"] = None,
    description: Optional[str] = None,
) -> Union["LoggerDefinition", Callable[["InitLoggerFunction"], "LoggerDefinition"]]:
    """Define a logger.

    The decorated function should accept an :py:class:`InitLoggerContext` and return an instance of
    :py:class:`python:logging.Logger`. This function will become the ``logger_fn`` of an underlying
    :py:class:`LoggerDefinition`.

    Args:
        config_schema (Optional[ConfigSchema]): The schema for the config. Configuration data available in
            `init_context.logger_config`. If not set, Dagster will accept any config provided.
        description (Optional[str]): A human-readable description of the logger.
    """
    # This case is for when decorator is used bare, without arguments.
    # E.g. @logger versus @logger()
    if callable(config_schema) and not is_callable_valid_config_arg(config_schema):
        return LoggerDefinition(logger_fn=cast("InitLoggerFunction", config_schema))

    def _wrap(logger_fn: "InitLoggerFunction") -> "LoggerDefinition":
        return LoggerDefinition(
            logger_fn=logger_fn,
            config_schema=config_schema,
            description=description,
        )

    return _wrap


def build_init_logger_context(
    logger_config: Any = None,
    pipeline_def: Optional["PipelineDefinition"] = None,
    job_def: Optional["JobDefinition"] = None,
) -> "UnboundInitLoggerContext":
    """Builds logger initialization context from provided parameters.

    This function can be used to provide the context argument to the invocation of a logger
    definition.

    Note that you may only specify one of pipeline_def and job_def.

    Args:
        logger_config (Any): The config to provide during initialization of logger.
        pipeline_def (Optional[PipelineDefinition]): The pipeline definition that the logger will be
            used with.
        job_def (Optional[JobDefinition]): The job definition that the logger will be used with.

    Examples:
        .. code-block:: python

            context = build_init_logger_context()
            logger_to_init(context)
    """
    from dagster._core.definitions import JobDefinition, PipelineDefinition
    from dagster._core.execution.context.logger import UnboundInitLoggerContext

    check.opt_inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    check.opt_inst_param(job_def, "job_def", JobDefinition)

    check.invariant(
        not (pipeline_def and job_def),
        (
            "In build_init_logger_context, you may only specify one of the pipeline_def and job_def"
            " parameters, not both."
        ),
    )

    return UnboundInitLoggerContext(
        logger_config=logger_config, pipeline_def=pipeline_def or job_def
    )
