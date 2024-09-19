from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.resource_invocation import resolve_bound_config
from dagster._core.execution.context.logger import InitLoggerContext, UnboundInitLoggerContext


def logger_invocation_result(logger_def: LoggerDefinition, init_context: UnboundInitLoggerContext):
    """Using the provided context, call the underlying `logger_fn` and return created logger."""
    logger_config = resolve_bound_config(init_context.logger_config, logger_def)

    bound_context = InitLoggerContext(
        logger_config, logger_def, init_context.job_def, init_context.run_id
    )

    return logger_def.logger_fn(bound_context)
