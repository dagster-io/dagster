import logging
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

from dagster import check
from dagster.core.definitions.config import is_callable_valid_config_arg
from dagster.core.definitions.configurable import AnonymousConfigurableDefinition
from dagster.core.errors import DagsterInvalidConfigError

from .definition_config_schema import convert_user_facing_definition_config_schema

if TYPE_CHECKING:
    from dagster.core.execution.context.logger import InitLoggerContext
    from dagster.core.definitions import PipelineDefinition

    InitLoggerFunction = Callable[[InitLoggerContext], logging.Logger]


class LoggerDefinition(AnonymousConfigurableDefinition):
    """Core class for defining loggers.

    Loggers are pipeline-scoped logging handlers, which will be automatically invoked whenever
    solids in a pipeline log messages.

    Args:
        logger_fn (Callable[[InitLoggerContext], logging.Logger]): User-provided function to
            instantiate the logger. This logger will be automatically invoked whenever the methods
            on ``context.log`` are called from within solid compute logic.
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

    # This allows us to pass LoggerDefinition off as a function, so that we can use it as a bare
    # decorator
    def __call__(self, *args, **kwargs):
        return self

    @property
    def logger_fn(self) -> "InitLoggerFunction":
        return self._logger_fn

    @property
    def config_schema(self) -> Any:
        return self._config_schema

    @property
    def description(self) -> Optional[str]:
        return self._description

    def copy_for_configured(
        self, description: Optional[str], config_schema: Any, _
    ) -> "LoggerDefinition":
        return LoggerDefinition(
            config_schema=config_schema,
            description=description or self.description,
            logger_fn=self.logger_fn,
        )


def logger(
    config_schema: Any = None, description: Optional[str] = None
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
        return LoggerDefinition(logger_fn=config_schema)

    def _wrap(logger_fn: "InitLoggerFunction") -> "LoggerDefinition":
        return LoggerDefinition(
            logger_fn=logger_fn,
            config_schema=config_schema,
            description=description,
        )

    return _wrap


def build_init_logger_context(
    logger_def: Optional["LoggerDefinition"] = None,
    logger_config: Any = None,
    pipeline_def: Optional["PipelineDefinition"] = None,
) -> "InitLoggerContext":
    from dagster.config.validate import validate_config
    from dagster.core.execution.context.logger import InitLoggerContext
    from dagster.core.definitions import PipelineDefinition

    check.inst_param(logger_def, "logger_def", LoggerDefinition)
    check.opt_inst_param(pipeline_def, "pipeline_def", PipelineDefinition)

    # If logger def is provided, then we can verify config.
    if logger_def:
        if logger_def.config_field:
            config_evr = validate_config(logger_def.config_field.config_type, logger_config)
            if not config_evr.success:
                raise DagsterInvalidConfigError(
                    "Error in config for logger ", config_evr.errors, logger_config
                )
        mapped_config_evr = logger_def.apply_config_mapping({"config": logger_config})
        if not mapped_config_evr.success:
            raise DagsterInvalidConfigError(
                "Error in config mapping for logger ", mapped_config_evr.errors, logger_config
            )
    logger_config = mapped_config_evr.value.get("config", {})

    return InitLoggerContext(
        logger_config=logger_config, pipeline_def=pipeline_def, logger_def=logger_def, run_id=None
    )
