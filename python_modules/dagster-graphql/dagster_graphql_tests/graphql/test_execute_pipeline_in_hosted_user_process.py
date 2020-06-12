from dagster_graphql.test.utils import execute_dagster_graphql

from dagster.core.utils import make_new_run_id

from .execution_queries import EXECUTE_RUN_IN_PROCESS_QUERY
from .graphql_context_test_suite import ExecutingGraphQLContextTestMatrix
from .setup import (
    csv_hello_world,
    csv_hello_world_solids_config,
    main_repo_location_name,
    main_repo_name,
)


class TestStartPipelineForCreatedRunInHostedUserProcess(ExecutingGraphQLContextTestMatrix):
    def test_synchronously_execute_run_within_hosted_user_process(self, graphql_context):
        pipeline_run = graphql_context.instance.create_run_for_pipeline(
            pipeline_def=csv_hello_world, run_config=csv_hello_world_solids_config()
        )

        result = execute_dagster_graphql(
            graphql_context,
            EXECUTE_RUN_IN_PROCESS_QUERY,
            variables={
                'runId': pipeline_run.run_id,
                'repositoryLocationName': main_repo_location_name(),
                'repositoryName': main_repo_name(),
            },
        )
        assert result.data
        assert result.data['executeRunInProcess']['__typename'] == 'ExecuteRunInProcessSuccess'

    def test_synchronously_execute_run_within_hosted_user_process_not_found(self, graphql_context):
        run_id = make_new_run_id()
        result = execute_dagster_graphql(
            graphql_context,
            EXECUTE_RUN_IN_PROCESS_QUERY,
            variables={
                'runId': run_id,
                'repositoryLocationName': main_repo_location_name(),
                'repositoryName': main_repo_name(),
            },
        )

        assert result.data
        assert result.data['executeRunInProcess']['__typename'] == 'PipelineRunNotFoundError'
