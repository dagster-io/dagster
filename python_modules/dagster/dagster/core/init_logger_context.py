from collections import namedtuple

from dagster import check

from .definitions.pipeline import PipelineDefinition
from .definitions.logger import LoggerDefinition


class InitLoggerContext(
    namedtuple('InitLoggerContext', 'context_config logger_config pipeline_def logger_def run_id')
):
    '''
    Similar to InitContext, but is logger-specific. It includes all the properties
    in the InitContext, plus the logger config and the logger definition.


    Attributes:
        context_config (Any): The configuration data provided by the environment config. The
            schema for this data is defined by ``config_field`` on the
            :py:class:`PipelineContextDefinition`
        logger_config (Any): The configuration data provided by the environment config. The
            schema for this data is defined by ``config_field`` on the :py:class:`LoggerDefinition`
        pipeline_def (PipelineDefinition): The pipeline definition currently being executed.
        logger_def (LoggerDefinition): The logger definition for the logger being constructed.
        run_id (str): The ID for this run of the pipeline.
    '''

    def __new__(cls, context_config, logger_config, pipeline_def, logger_def, run_id):
        return super(InitLoggerContext, cls).__new__(
            cls,
            context_config,
            logger_config,
            check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            check.inst_param(logger_def, 'logger_def', LoggerDefinition),
            check.str_param(run_id, 'run_id'),
        )
