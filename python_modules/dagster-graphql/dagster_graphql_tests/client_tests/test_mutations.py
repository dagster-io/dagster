from dagster import ExecutionTargetHandle

from dagster_graphql.client.mutations import execute_start_pipeline_execution_query

EXPECTED_EVENTS = {
    ('STEP_INPUT', 'sleeper_1.compute'),
    ('STEP_INPUT', 'sleeper_2.compute'),
    ('STEP_INPUT', 'sleeper_3.compute'),
    ('STEP_INPUT', 'sleeper_4.compute'),
    ('STEP_INPUT', 'total.compute'),
    ('STEP_OUTPUT', 'giver.compute'),
    ('STEP_OUTPUT', 'sleeper_1.compute'),
    ('STEP_OUTPUT', 'sleeper_2.compute'),
    ('STEP_OUTPUT', 'sleeper_3.compute'),
    ('STEP_OUTPUT', 'sleeper_4.compute'),
    ('STEP_OUTPUT', 'total.compute'),
    ('STEP_START', 'giver.compute'),
    ('STEP_START', 'sleeper_1.compute'),
    ('STEP_START', 'sleeper_2.compute'),
    ('STEP_START', 'sleeper_3.compute'),
    ('STEP_START', 'sleeper_4.compute'),
    ('STEP_START', 'total.compute'),
    ('STEP_SUCCESS', 'giver.compute'),
    ('STEP_SUCCESS', 'sleeper_1.compute'),
    ('STEP_SUCCESS', 'sleeper_2.compute'),
    ('STEP_SUCCESS', 'sleeper_3.compute'),
    ('STEP_SUCCESS', 'sleeper_4.compute'),
    ('STEP_SUCCESS', 'total.compute'),
}


def test_execute_start_pipeline_execution_query():
    pipeline_name = 'sleepy_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module(
        'dagster_examples.toys.sleepy', pipeline_name
    )
    variables = {
        'executionParams': {
            'environmentConfigData': {},
            'mode': 'default',
            'selector': {'name': pipeline_name},
            'executionMetadata': {'runId': '12345'},
        }
    }
    result = execute_start_pipeline_execution_query(handle, variables)
    seen_events = set()
    for event in result:
        seen_events.add((event.event_type_value, event.step_key))

    assert seen_events == EXPECTED_EVENTS
