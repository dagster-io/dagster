from collections import namedtuple

from dagster import check

from dagster.core.definitions.logger import LoggerDefinition
from dagster.core.definitions.pipeline import PipelineDefinition


class InitLoggerContext(
    namedtuple('InitLoggerContext', 'logger_config pipeline_def logger_def run_id')
):
    '''
    Logger-specific initialization context.

    Attributes:
        logger_config (Any): The configuration data provided by the environment config. The
            schema for this data is defined by ``config_field`` on the :py:class:`LoggerDefinition`
        pipeline_def (PipelineDefinition): The pipeline definition currently being executed.
        logger_def (LoggerDefinition): The logger definition for the logger being constructed.
        run_id (str): The ID for this run of the pipeline.
    '''

    def __new__(cls, logger_config, pipeline_def, logger_def, run_id):
        return super(InitLoggerContext, cls).__new__(
            cls,
            logger_config,
            check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            check.inst_param(logger_def, 'logger_def', LoggerDefinition),
            check.str_param(run_id, 'run_id'),
        )
