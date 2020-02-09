from dagster_graphql.client.mutations import (
    execute_execute_plan_mutation,
    execute_execute_plan_mutation_raw,
)

from dagster import ExecutionTargetHandle
from dagster.core.instance import DagsterInstance
from dagster.core.utils import make_new_run_id

EXPECTED_EVENTS = {
    ('ENGINE_EVENT', None),
    ('STEP_INPUT', 'sleeper.compute'),
    ('STEP_INPUT', 'sleeper_2.compute'),
    ('STEP_INPUT', 'sleeper_3.compute'),
    ('STEP_INPUT', 'sleeper_4.compute'),
    ('STEP_INPUT', 'total.compute'),
    ('STEP_OUTPUT', 'giver.compute'),
    ('STEP_OUTPUT', 'sleeper.compute'),
    ('STEP_OUTPUT', 'sleeper_2.compute'),
    ('STEP_OUTPUT', 'sleeper_3.compute'),
    ('STEP_OUTPUT', 'sleeper_4.compute'),
    ('STEP_OUTPUT', 'total.compute'),
    ('STEP_START', 'giver.compute'),
    ('STEP_START', 'sleeper.compute'),
    ('STEP_START', 'sleeper_2.compute'),
    ('STEP_START', 'sleeper_3.compute'),
    ('STEP_START', 'sleeper_4.compute'),
    ('STEP_START', 'total.compute'),
    ('STEP_SUCCESS', 'giver.compute'),
    ('STEP_SUCCESS', 'sleeper.compute'),
    ('STEP_SUCCESS', 'sleeper_2.compute'),
    ('STEP_SUCCESS', 'sleeper_3.compute'),
    ('STEP_SUCCESS', 'sleeper_4.compute'),
    ('STEP_SUCCESS', 'total.compute'),
}


def test_execute_execute_plan_mutation():
    pipeline_name = 'sleepy_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module(
        'dagster_examples.toys.sleepy', pipeline_name
    )
    run_id = make_new_run_id()
    instance = DagsterInstance.local_temp()
    instance.create_empty_run(run_id, pipeline_name)

    variables = {
        'executionParams': {
            'environmentConfigData': {},
            'mode': 'default',
            'selector': {'name': pipeline_name},
            'executionMetadata': {'runId': run_id},
        }
    }
    result = execute_execute_plan_mutation(handle, variables, instance_ref=instance.get_ref())
    seen_events = set()
    for event in result:
        seen_events.add((event.event_type_value, event.step_key))

    assert seen_events == EXPECTED_EVENTS


def test_execute_execute_plan_mutation_raw():
    pipeline_name = 'sleepy_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module(
        'dagster_examples.toys.sleepy', pipeline_name
    )
    run_id = make_new_run_id()
    instance = DagsterInstance.local_temp()
    instance.create_empty_run(run_id, pipeline_name)
    variables = {
        'executionParams': {
            'environmentConfigData': {},
            'mode': 'default',
            'selector': {'name': pipeline_name},
            'executionMetadata': {'runId': run_id},
        }
    }
    result = execute_execute_plan_mutation_raw(handle, variables, instance_ref=instance.get_ref())
    seen_events = set()
    for event in result:
        seen_events.add((event.dagster_event.event_type_value, event.step_key))

    assert seen_events == EXPECTED_EVENTS


# TODO: uncomment when resolving https://github.com/dagster-io/dagster/issues/1876
# def test_execute_plan_for_unknown_run():
#     pipeline_name = 'sleepy_pipeline'
#     handle = ExecutionTargetHandle.for_pipeline_module(
#         'dagster_examples.toys.sleepy', pipeline_name
#     )
#     unknown_run_id = '12345'
#     variables = {
#         'executionParams': {
#             'environmentConfigData': {},
#             'mode': 'default',
#             'selector': {'name': pipeline_name},
#             'executionMetadata': {'runId': unknown_run_id},
#         }
#     }
#     with pytest.raises(DagsterGraphQLClientError) as exc_info:
#         execute_execute_plan_mutation_raw(handle, variables)
#     assert str(exc_info.value) == 'Pipeline run {run_id} could not be found.'.format(
#         run_id=unknown_run_id
#     )
