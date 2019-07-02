from collections import defaultdict

from dagster import (
    execute_pipeline,
    solid,
    Bool,
    DependencyDefinition,
    ExecutionTargetHandle,
    ExpectationResult,
    InputDefinition,
    Materialization,
    OutputDefinition,
    PipelineDefinition,
    Output,
    RunConfig,
)
from dagster.core.events import STEP_EVENTS, DagsterEventType
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.config import InProcessExecutorConfig
from dagster_graphql.cli import execute_query
from dagster_graphql.implementation.pipeline_run_storage import PipelineRunStorage
from dagster_graphql.util import (
    _handled_events,
    dagster_event_from_dict,
    get_log_message_event_fragment,
    get_step_event_fragment,
)


def test_can_handle_all_step_events():
    '''This test is designed to ensure we catch the case when new step events are added, as they
    must be handled by the event parsing, but this does not check that the event parsing works
    correctly.
    '''
    handled = set(_handled_events().values())
    assert handled == STEP_EVENTS


def define_test_events_pipeline():
    @solid(output_defs=[OutputDefinition(Bool)])
    def materialization_and_expectation(_context):
        yield Materialization.file(path='/path/to/foo', description='This is a table.')
        yield Materialization.file(path='/path/to/bar')
        yield ExpectationResult(success=True, label='row_count', description='passed')
        yield ExpectationResult(True)
        yield Output(True)

    @solid(
        output_defs=[
            OutputDefinition(name='output_one'),
            OutputDefinition(name='output_two', is_optional=True),
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

    return PipelineDefinition(
        name='test_events',
        solid_defs=[
            materialization_and_expectation,
            optional_only_one,
            should_fail,
            should_be_skipped,
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
    result = execute_pipeline(
        define_test_events_pipeline(), run_config=RunConfig.nonthrowing_in_process()
    )
    assert result.result_for_solid('materialization_and_expectation').success
    assert not result.result_for_solid('should_fail').success
    assert result.result_for_solid('should_be_skipped').skipped


PIPELINE_EXECUTION_QUERY_TEMPLATE = '''
mutation(
  $executionParams: ExecutionParams!
) {{
  startPipelineExecution(
    executionParams: $executionParams,
  ) {{
    __typename
    ... on PipelineConfigValidationInvalid {{
      pipeline {{
        name
      }}
      errors {{
        __typename
        message
        path
        reason
      }}
    }}
    ... on PipelineNotFoundError {{
        message
        pipelineName
    }}
    ... on StartPipelineExecutionSuccess {{
      run {{
        runId
        status
        pipeline {{
          name
        }}
        logs {{
          nodes {{
            __typename
            {step_event_fragment}
            {log_message_event_fragment}
          }}
          pageInfo {{
            lastCursor
            hasNextPage
            hasPreviousPage
            count
            totalCount
          }}
        }}
        environmentConfigYaml
        mode
      }}
    }}
  }}
}}
'''.strip(
    '\n'
)


def test_all_step_events():  # pylint: disable=too-many-locals
    handle = ExecutionTargetHandle.for_pipeline_fn(define_test_events_pipeline)
    pipeline = handle.build_pipeline_definition()
    mode = pipeline.get_default_mode_name()
    run_config = RunConfig(executor_config=InProcessExecutorConfig(raise_on_error=False), mode=mode)
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

    step_event_fragment = get_step_event_fragment()
    log_message_event_fragment = get_log_message_event_fragment()
    query = '\n'.join(
        (
            PIPELINE_EXECUTION_QUERY_TEMPLATE.format(
                step_event_fragment=step_event_fragment.include_key,
                log_message_event_fragment=log_message_event_fragment.include_key,
            ),
            step_event_fragment.fragment,
            log_message_event_fragment.fragment,
        )
    )

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

            pipeline_run_storage = PipelineRunStorage()

            res = execute_query(handle, query, variables, pipeline_run_storage=pipeline_run_storage)

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
                    key = event.step_key + '.' + event.event_type_value
                    event_counts[key] -= 1
                unhandled_events -= {DagsterEventType(e.event_type_value) for e in events}
            else:
                raise Exception(res['errors'])

            # build up a dict, incrementing all the event records we've produced in the run storage
            logs = pipeline_run_storage.get_run_by_id(run_config.run_id).all_logs()
            for log in logs:
                if not log.dagster_event or (
                    DagsterEventType(log.dagster_event.event_type_value) not in STEP_EVENTS
                ):
                    continue
                key = log.dagster_event.step_key + '.' + log.dagster_event.event_type_value
                event_counts[key] += 1

    # Ensure we've processed all the events that were generated in the run storage
    assert sum(event_counts.values()) == 0

    # Ensure we've handled the universe of event types
    assert not unhandled_events
