from collections import namedtuple
from typing import Any

from dagster import check
from dagster.core.definitions.logger import LoggerDefinition
from dagster.core.definitions.pipeline import PipelineDefinition


class InitLoggerContext(
    namedtuple("InitLoggerContext", "logger_config pipeline_def logger_def run_id")
):
    """Logger-specific initialization context.

    An instance of this class is made available as the first argument to the ``logger_fn`` decorated
    by :py:func:`@logger <logger>` or set on a :py:class:`LoggerDefinition`.

    Users should not instantiate this class.

    Attributes:
        logger_config (Any): The configuration data provided by the environment config. The
            schema for this data is defined by ``config_schema`` on the :py:class:`LoggerDefinition`
        pipeline_def (PipelineDefinition): The pipeline definition currently being executed.
        logger_def (LoggerDefinition): The logger definition for the logger being constructed.
        run_id (str): The ID for this run of the pipeline.
    """

    def __new__(
        cls,
        logger_config: Any,
        pipeline_def: PipelineDefinition,
        logger_def: LoggerDefinition,
        run_id: str,
    ):
        return super(InitLoggerContext, cls).__new__(
            cls,
            logger_config,
            check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition),
            check.inst_param(logger_def, "logger_def", LoggerDefinition),
            check.str_param(run_id, "run_id"),
        )
