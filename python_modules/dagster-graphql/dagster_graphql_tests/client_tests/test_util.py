from collections import defaultdict

from dagster_graphql.cli import execute_query
from dagster_graphql.client.query import START_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.client.util import HANDLED_EVENTS, dagster_event_from_dict

from dagster import (
    Bool,
    DependencyDefinition,
    EventMetadataEntry,
    ExecutionTargetHandle,
    ExpectationResult,
    InputDefinition,
    Materialization,
    Output,
    OutputDefinition,
    PipelineDefinition,
    RetryRequested,
    RunConfig,
    execute_pipeline,
    lambda_solid,
    solid,
)
from dagster.core.events import STEP_EVENTS, DagsterEventType
from dagster.core.execution.api import create_execution_plan
from dagster.core.instance import DagsterInstance


def test_can_handle_all_step_events():
    '''This test is designed to ensure we catch the case when new step events are added, as they
    must be handled by the event parsing, but this does not check that the event parsing works
    correctly.
    '''
    handled = set(HANDLED_EVENTS.values())
    # The distinction between "step events" and "pipeline events" needs to be reexamined
    assert handled == STEP_EVENTS.union(set([DagsterEventType.ENGINE_EVENT]))


def define_test_events_pipeline():
    @solid(output_defs=[OutputDefinition(Bool)])
    def materialization_and_expectation(_context):
        yield Materialization(
            label='all_types',
            description='a materialization with all metadata types',
            metadata_entries=[
                EventMetadataEntry.text('text is cool', 'text'),
                EventMetadataEntry.url('https://bigty.pe/neato', 'url'),
                EventMetadataEntry.fspath('/tmp/awesome', 'path'),
                EventMetadataEntry.json({'is_dope': True}, 'json'),
            ],
        )
        yield ExpectationResult(success=True, label='row_count', description='passed')
        yield ExpectationResult(True)
        yield Output(True)

    @solid(
        output_defs=[
            OutputDefinition(name='output_one'),
            OutputDefinition(name='output_two', is_required=False),
        ]
    )
    def optional_only_one(_context):  # pylint: disable=unused-argument
        yield Output(output_name='output_one', value=1)

    @solid(input_defs=[InputDefinition('some_input')])
    def should_fail(_context, some_input):  # pylint: disable=unused-argument
        raise Exception('should fail')

    @solid(input_defs=[InputDefinition('some_input')])
    def should_be_skipped(_context, some_input):  # pylint: disable=unused-argument
        pass

    @lambda_solid
    def retries():
        raise RetryRequested()

    return PipelineDefinition(
        name='test_events',
        solid_defs=[
            materialization_and_expectation,
            optional_only_one,
            should_fail,
            should_be_skipped,
            retries,
        ],
        dependencies={
            'optional_only_one': {},
            'should_fail': {
                'some_input': DependencyDefinition(optional_only_one.name, 'output_one')
            },
            'should_be_skipped': {
                'some_input': DependencyDefinition(optional_only_one.name, 'output_two')
            },
        },
    )


def test_pipeline():
    '''just a sanity check to ensure the above pipeline works without layering on graphql'''
    result = execute_pipeline(define_test_events_pipeline(), raise_on_error=False)
    assert result.result_for_solid('materialization_and_expectation').success
    assert not result.result_for_solid('should_fail').success
    assert result.result_for_solid('should_be_skipped').skipped


def test_all_step_events():  # pylint: disable=too-many-locals
    handle = ExecutionTargetHandle.for_pipeline_fn(define_test_events_pipeline)
    pipeline = handle.build_pipeline_definition()
    mode = pipeline.get_default_mode_name()
    run_config = RunConfig(mode=mode)
    execution_plan = create_execution_plan(pipeline, {}, run_config=run_config)
    step_levels = execution_plan.topological_step_levels()

    unhandled_events = STEP_EVENTS.copy()

    # Exclude types that are not step events
    ignored_events = {
        'LogMessageEvent',
        'PipelineStartEvent',
        'PipelineSuccessEvent',
        'PipelineInitFailureEvent',
        'PipelineFailureEvent',
    }

    event_counts = defaultdict(int)

    for step_level in step_levels:
        for step in step_level:

            variables = {
                'executionParams': {
                    'selector': {'name': pipeline.name},
                    'environmentConfigData': {'storage': {'filesystem': {}}},
                    'mode': mode,
                    'executionMetadata': {'runId': run_config.run_id},
                    'stepKeys': [step.key],
                }
            }
            instance = DagsterInstance.ephemeral()
            res = execute_query(
                handle, START_PIPELINE_EXECUTION_MUTATION, variables, instance=instance
            )

            # go through the same dict, decrement all the event records we've seen from the GraphQL
            # response
            if not res.get('errors'):
                run_logs = res['data']['startPipelineExecution']['run']['logs']['nodes']

                events = [
                    dagster_event_from_dict(e, pipeline.name)
                    for e in run_logs
                    if e['__typename'] not in ignored_events
                ]

                for event in events:
                    if event.step_key:
                        key = event.step_key + '.' + event.event_type_value
                    else:
                        key = event.event_type_value
                    event_counts[key] -= 1
                unhandled_events -= {DagsterEventType(e.event_type_value) for e in events}
            else:
                raise Exception(res['errors'])

            # build up a dict, incrementing all the event records we've produced in the run storage
            logs = instance.all_logs(run_config.run_id)
            for log in logs:
                if not log.dagster_event or (
                    DagsterEventType(log.dagster_event.event_type_value)
                    not in STEP_EVENTS.union(set([DagsterEventType.ENGINE_EVENT]))
                ):
                    continue
                if log.dagster_event.step_key:
                    key = log.dagster_event.step_key + '.' + log.dagster_event.event_type_value
                else:
                    key = log.dagster_event.event_type_value
                event_counts[key] += 1

    # Ensure we've processed all the events that were generated in the run storage
    assert sum(event_counts.values()) == 0

    # Ensure we've handled the universe of event types
    assert not unhandled_events
