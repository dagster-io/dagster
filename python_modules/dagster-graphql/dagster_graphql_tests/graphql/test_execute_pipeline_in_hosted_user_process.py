from dagster_graphql.test.utils import execute_dagster_graphql

from dagster.core.utils import make_new_run_id

from .execution_queries import START_PIPELINE_EXECUTION_FOR_CREATED_RUN_QUERY
from .graphql_context_test_suite import ExecutingGraphQLContextTestMatrix
from .setup import csv_hello_world, csv_hello_world_solids_config


class TestStartPipelineForCreatedRunInHostedUserProcess(ExecutingGraphQLContextTestMatrix):
    def test_synchronously_execute_run_within_hosted_user_process(self, graphql_context):
        pipeline_run = graphql_context.instance.create_run_for_pipeline(
            pipeline_def=csv_hello_world, environment_dict=csv_hello_world_solids_config()
        )

        result = execute_dagster_graphql(
            graphql_context,
            START_PIPELINE_EXECUTION_FOR_CREATED_RUN_QUERY,
            variables={'runId': pipeline_run.run_id},
        )
        assert result.data
        assert (
            result.data['startPipelineExecutionForCreatedRun']['__typename']
            == 'StartPipelineRunSuccess'
        )

    def test_synchronously_execute_run_within_hosted_user_process_not_found(self, graphql_context):
        run_id = make_new_run_id()
        result = execute_dagster_graphql(
            graphql_context,
            START_PIPELINE_EXECUTION_FOR_CREATED_RUN_QUERY,
            variables={'runId': run_id},
        )

        assert result.data
        assert (
            result.data['startPipelineExecutionForCreatedRun']['__typename']
            == 'PipelineRunNotFoundError'
        )
