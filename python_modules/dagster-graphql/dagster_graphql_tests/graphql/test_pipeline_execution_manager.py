from dagster_graphql.test.utils import execute_dagster_graphql
from dagster_graphql_tests.graphql.setup import define_test_subprocess_context
from dagster_graphql_tests.test_cli import START_PIPELINE_EXECUTION_QUERY

from dagster.core.instance import DagsterInstance
from dagster.seven.abc import Iterable
from dagster.utils import file_relative_path


def is_clear_execution_manager(manager):
    manager_process_state = [
        getattr(manager, field)
        for field in vars(manager)
        if isinstance(getattr(manager, field), Iterable)
    ]
    # Ensure no memory growth over time in long living dagits
    assert all([len(iterable) == 0 for iterable in manager_process_state])


def test_term_event_lifecycle():
    context = define_test_subprocess_context(DagsterInstance.local_temp())
    execution_manager = context.execution_manager
    is_clear_execution_manager(execution_manager)
    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'mode': 'default',
                'environmentConfigData': {
                    'execution': {'multiprocess': {'config': {'max_concurrent': 4}}},
                    'solids': {
                        'sum_solid': {
                            'inputs': {'num': file_relative_path(__file__, '../data/num.csv')}
                        }
                    },
                },
            }
        },
    )

    # Make sure pipeline ran successfully
    assert not result.errors
    assert result.data
    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'

    # Clean up
    execution_manager.join()
    execution_manager.check()
    is_clear_execution_manager(execution_manager)
