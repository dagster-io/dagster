from collections import namedtuple

from dagster import check
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.definitions.resource import ResourceDefinition
from dagster.core.log_manager import DagsterLogManager


class InitResourceContext(
    namedtuple(
        'InitResourceContext', 'resource_config pipeline_def resource_def run_id log_manager'
    )
):
    '''Resource-specific initialization context.

    Attributes:
        resource_config (Any): The configuration data provided by the environment config. The schema
            for this data is defined by the ``config_field`` argument to
            :py:class:`ResourceDefinition`.
        pipeline_def (PipelineDefinition): The definition of the pipeline currently being executed.
        resource_def (ResourceDefinition): The definition of the resource currently being
            constructed.
        run_id (str): The id for this run of the pipeline.
        log_manager (DagsterLogManager): The log manager for this run of the pipeline
    '''

    def __new__(cls, resource_config, pipeline_def, resource_def, run_id, log_manager=None):
        return super(InitResourceContext, cls).__new__(
            cls,
            resource_config,
            check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            check.inst_param(resource_def, 'resource_def', ResourceDefinition),
            check.str_param(run_id, 'run_id'),
            check.opt_inst_param(log_manager, 'log_manager', DagsterLogManager),
        )

    @property
    def log(self):
        return self.log_manager
