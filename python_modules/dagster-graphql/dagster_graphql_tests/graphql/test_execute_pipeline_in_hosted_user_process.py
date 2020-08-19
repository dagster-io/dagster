from dagster_graphql.client.query import EXECUTE_RUN_IN_PROCESS_MUTATION
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster import DagsterInstance
from dagster.core.host_representation.handle import IN_PROCESS_NAME
from dagster.core.utils import make_new_run_id

from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite
from .setup import (
    csv_hello_world,
    csv_hello_world_solids_config,
    define_test_out_of_process_context,
    main_repo_location_name,
    main_repo_name,
)


class TestStartPipelineForCreatedRunInHostedUserProcess(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.sqlite_with_default_run_launcher_in_process_env()]
    )
):
    def test_synchronously_execute_run_within_hosted_user_process(self, graphql_context):
        pipeline_run = graphql_context.instance.create_run_for_pipeline(
            pipeline_def=csv_hello_world, run_config=csv_hello_world_solids_config()
        )

        result = execute_dagster_graphql(
            graphql_context,
            EXECUTE_RUN_IN_PROCESS_MUTATION,
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
            EXECUTE_RUN_IN_PROCESS_MUTATION,
            variables={
                'runId': run_id,
                'repositoryLocationName': main_repo_location_name(),
                'repositoryName': main_repo_name(),
            },
        )

        assert result.data
        assert result.data['executeRunInProcess']['__typename'] == 'PipelineRunNotFoundError'


# should be removed as https://github.com/dagster-io/dagster/issues/2608 is completed
def test_shameful_workaround():
    graphql_context = define_test_out_of_process_context(DagsterInstance.ephemeral())

    pipeline_run = graphql_context.instance.create_run_for_pipeline(
        pipeline_def=csv_hello_world, run_config=csv_hello_world_solids_config()
    )

    result = execute_dagster_graphql(
        graphql_context,
        EXECUTE_RUN_IN_PROCESS_MUTATION,
        variables={
            'runId': pipeline_run.run_id,
            # in corect in process name represents launching from user process
            'repositoryLocationName': IN_PROCESS_NAME,
            'repositoryName': main_repo_name(),
        },
    )
    assert result.data
    assert result.data['executeRunInProcess']['__typename'] == 'ExecuteRunInProcessSuccess'

    result = execute_dagster_graphql(
        graphql_context,
        EXECUTE_RUN_IN_PROCESS_MUTATION,
        variables={
            'runId': pipeline_run.run_id,
            # but we don't apply workaround to other names
            'repositoryLocationName': 'some_other_name',
            'repositoryName': main_repo_name(),
        },
    )
    assert result.data
    assert result.data['executeRunInProcess']['__typename'] == 'PipelineNotFoundError'
