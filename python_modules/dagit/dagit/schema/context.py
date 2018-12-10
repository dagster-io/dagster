from dagster import check
from dagit.pipeline_run_storage import PipelineRunStorage
from dagit.pipeline_execution_manager import PipelineExecutionManager


class DagsterGraphQLContext(object):
    def __init__(self, repository_container, pipeline_runs, execution_manager):
        from dagit.app import RepositoryContainer
        self.repository_container = check.inst_param(
            repository_container,
            'repository_container',
            RepositoryContainer,
        )
        self.pipeline_runs = check.inst_param(
            pipeline_runs,
            'pipeline_runs',
            PipelineRunStorage,
        )
        self.execution_manager = check.inst_param(
            execution_manager, 'pipeline_execution_manager', PipelineExecutionManager
        )
