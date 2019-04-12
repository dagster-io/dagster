from dagster import check
from dagster.cli.dynamic_loader import RepositoryContainer
from .pipeline_run_storage import PipelineRunStorage
from .pipeline_execution_manager import PipelineExecutionManager


class DagsterGraphQLContext(object):
    def __init__(
        self,
        repository_container,
        pipeline_runs,
        execution_manager,
        raise_on_error=False,
        version=None,
    ):

        self.repository_container = check.inst_param(
            repository_container, 'repository_container', RepositoryContainer
        )
        self.pipeline_runs = check.inst_param(pipeline_runs, 'pipeline_runs', PipelineRunStorage)
        self.execution_manager = check.inst_param(
            execution_manager, 'pipeline_execution_manager', PipelineExecutionManager
        )
        self.raise_on_error = check.bool_param(raise_on_error, 'raise_on_error')
        self.version = version
