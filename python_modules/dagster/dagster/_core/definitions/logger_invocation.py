from ..execution.context.logger import InitLoggerContext, UnboundInitLoggerContext
from .logger_definition import LoggerDefinition
from .resource_invocation import resolve_bound_config


def logger_invocation_result(logger_def: LoggerDefinition, init_context: UnboundInitLoggerContext):
    """Using the provided context, call the underlying `logger_fn` and return created logger."""
    logger_config = resolve_bound_config(init_context.logger_config, logger_def)

    bound_context = InitLoggerContext(
        logger_config, logger_def, init_context.job_def, init_context.run_id
    )

    return logger_def.logger_fn(bound_context)
