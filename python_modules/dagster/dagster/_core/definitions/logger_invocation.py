from typing import Any, Dict, cast

from dagster._core.errors import DagsterInvalidConfigError

from ..._config import Shape
from ..execution.context.logger import InitLoggerContext, UnboundInitLoggerContext
from .logger_definition import LoggerDefinition


def logger_invocation_result(logger_def: LoggerDefinition, init_context: UnboundInitLoggerContext):
    """Using the provided context, call the underlying `logger_fn` and return created logger."""

    logger_config = _resolve_bound_config(init_context.logger_config, logger_def)

    bound_context = InitLoggerContext(
        logger_config, logger_def, init_context.pipeline_def, init_context.run_id
    )

    return logger_def.logger_fn(bound_context)


def _resolve_bound_config(logger_config: Any, logger_def: "LoggerDefinition") -> Any:
    from dagster._config import process_config

    validated_config = None
    outer_config_shape = Shape({"config": logger_def.get_config_field()})
    config_evr = process_config(
        outer_config_shape, {"config": logger_config} if logger_config else {}
    )
    if not config_evr.success:
        raise DagsterInvalidConfigError(
            "Error in config for logger ",
            config_evr.errors,
            logger_config,
        )
    validated_config = cast(Dict, config_evr.value).get("config")
    mapped_config_evr = logger_def.apply_config_mapping({"config": validated_config})
    if not mapped_config_evr.success:
        raise DagsterInvalidConfigError(
            "Error in config mapping for logger ", mapped_config_evr.errors, validated_config
        )
    validated_config = cast(Dict, mapped_config_evr.value).get("config")
    return validated_config


def _get_default_if_exists(logger_def: LoggerDefinition):
    return (
        logger_def.config_field.default_value
        if logger_def.config_field and logger_def.config_field.default_provided
        else None
    )
