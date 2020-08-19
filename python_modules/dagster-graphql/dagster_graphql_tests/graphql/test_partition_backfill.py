from dagster_graphql.client.query import LAUNCH_PARTITION_BACKFILL_MUTATION
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    execute_dagster_graphql_and_finish_runs,
    infer_repository_selector,
)

from dagster.core.test_utils import environ

from .graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
    GraphQLContextVariant,
    make_graphql_context_test_suite,
)
from .utils import (
    get_all_logs_for_finished_run_via_subscription,
    step_did_fail,
    step_did_not_run,
    step_did_skip,
    step_did_succeed,
)


class TestPartitionBackfill(ExecutingGraphQLContextTestMatrix):
    def test_launch_full_pipeline_backfill(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                'backfillParams': {
                    'selector': {
                        'repositorySelector': repository_selector,
                        'partitionSetName': 'integer_partition',
                    },
                    'partitionNames': ['2', '3'],
                }
            },
        )
        assert not result.errors
        assert result.data
        assert result.data['launchPartitionBackfill']['__typename'] == 'PartitionBackfillSuccess'
        assert len(result.data['launchPartitionBackfill']['launchedRunIds']) == 2

    def test_launch_partial_backfill(self, graphql_context):
        # execute a full pipeline, without the failure environment variable
        repository_selector = infer_repository_selector(graphql_context)
        partition_set_selector = {
            'repositorySelector': repository_selector,
            'partitionSetName': 'chained_integer_partition',
        }
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                'backfillParams': {
                    'selector': partition_set_selector,
                    'partitionNames': ['2', '3'],
                }
            },
        )
        assert not result.errors
        assert result.data
        assert result.data['launchPartitionBackfill']['__typename'] == 'PartitionBackfillSuccess'
        assert len(result.data['launchPartitionBackfill']['launchedRunIds']) == 2
        for run_id in result.data['launchPartitionBackfill']['launchedRunIds']:
            logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
                'pipelineRunLogs'
            ]['messages']
            assert step_did_succeed(logs, 'always_succeed.compute')
            assert step_did_succeed(logs, 'conditionally_fail.compute')
            assert step_did_succeed(logs, 'after_failure.compute')

        # reexecute a partial pipeline
        partial_steps = ['after_failure.compute']
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                'backfillParams': {
                    'selector': partition_set_selector,
                    'partitionNames': ['2', '3'],
                    'reexecutionSteps': partial_steps,
                }
            },
        )
        assert not result.errors
        assert result.data

        assert result.data['launchPartitionBackfill']['__typename'] == 'PartitionBackfillSuccess'
        assert len(result.data['launchPartitionBackfill']['launchedRunIds']) == 2
        for run_id in result.data['launchPartitionBackfill']['launchedRunIds']:
            logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
                'pipelineRunLogs'
            ]['messages']
            assert step_did_not_run(logs, 'always_succeed.compute')
            assert step_did_not_run(logs, 'conditionally_fail.compute')
            assert step_did_succeed(logs, 'after_failure.compute')


class TestLaunchBackfillFromFailure(
    make_graphql_context_test_suite(
        context_variants=[
            GraphQLContextVariant.sqlite_with_default_run_launcher_in_process_env(),
            GraphQLContextVariant.sqlite_with_default_run_launcher_out_of_process_env(),
        ]
    )
):
    def test_launch_from_failure(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        partition_set_selector = {
            'repositorySelector': repository_selector,
            'partitionSetName': 'chained_integer_partition',
        }

        # trigger failure in the conditionally_fail solid
        with environ({'TEST_SOLID_SHOULD_FAIL': 'YES'}):
            result = execute_dagster_graphql_and_finish_runs(
                graphql_context,
                LAUNCH_PARTITION_BACKFILL_MUTATION,
                variables={
                    'backfillParams': {
                        'selector': partition_set_selector,
                        'partitionNames': ['2', '3'],
                    }
                },
            )
        assert not result.errors
        assert result.data
        assert result.data['launchPartitionBackfill']['__typename'] == 'PartitionBackfillSuccess'
        assert len(result.data['launchPartitionBackfill']['launchedRunIds']) == 2
        for run_id in result.data['launchPartitionBackfill']['launchedRunIds']:
            logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
                'pipelineRunLogs'
            ]['messages']
            assert step_did_succeed(logs, 'always_succeed.compute')
            assert step_did_fail(logs, 'conditionally_fail.compute')
            assert step_did_skip(logs, 'after_failure.compute')

        # re-execute from failure (without the failure environment variable)
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                'backfillParams': {
                    'selector': partition_set_selector,
                    'partitionNames': ['2', '3'],
                    'fromFailure': True,
                }
            },
        )
        assert not result.errors
        assert result.data
        assert result.data['launchPartitionBackfill']['__typename'] == 'PartitionBackfillSuccess'
        assert len(result.data['launchPartitionBackfill']['launchedRunIds']) == 2
        for run_id in result.data['launchPartitionBackfill']['launchedRunIds']:
            logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
                'pipelineRunLogs'
            ]['messages']
            assert step_did_not_run(logs, 'always_succeed.compute')
            assert step_did_succeed(logs, 'conditionally_fail.compute')
            assert step_did_succeed(logs, 'after_failure.compute')
