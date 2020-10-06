from collections import defaultdict

from dagster_graphql.cli import execute_query
from dagster_graphql.client.query import EXECUTE_PLAN_MUTATION
from dagster_graphql.client.util import HANDLED_EVENTS, dagster_event_from_dict, parse_raw_log_lines

from dagster import (
    AssetMaterialization,
    Bool,
    DependencyDefinition,
    EventMetadataEntry,
    ExpectationResult,
    InputDefinition,
    Output,
    OutputDefinition,
    PipelineDefinition,
    RetryRequested,
    execute_pipeline,
    lambda_solid,
    solid,
)
from dagster.core.code_pointer import CodePointer
from dagster.core.definitions.reconstructable import get_ephemeral_repository_name
from dagster.core.events import STEP_EVENTS, DagsterEventType
from dagster.core.execution.api import create_execution_plan
from dagster.core.host_representation.handle import IN_PROCESS_NAME
from dagster.core.instance import DagsterInstance
from dagster.utils.hosted_user_process import create_in_process_ephemeral_workspace


def test_can_handle_all_step_events():
    """This test is designed to ensure we catch the case when new step events are added, as they
    must be handled by the event parsing, but this does not check that the event parsing works
    correctly.
    """
    handled = set(HANDLED_EVENTS.values())
    # The distinction between "step events" and "pipeline events" needs to be reexamined
    assert handled == STEP_EVENTS.union(set([DagsterEventType.ENGINE_EVENT]))


def define_test_events_pipeline():
    @solid(output_defs=[OutputDefinition(Bool)])
    def materialization_and_expectation(_context):
        yield AssetMaterialization(
            asset_key="all_types",
            description="a materialization with all metadata types",
            metadata_entries=[
                EventMetadataEntry.text("text is cool", "text"),
                EventMetadataEntry.url("https://bigty.pe/neato", "url"),
                EventMetadataEntry.fspath("/tmp/awesome", "path"),
                EventMetadataEntry.json({"is_dope": True}, "json"),
            ],
        )
        yield ExpectationResult(success=True, label="row_count", description="passed")
        yield ExpectationResult(True)
        yield Output(True)

    @solid(
        output_defs=[
            OutputDefinition(name="output_one"),
            OutputDefinition(name="output_two", is_required=False),
        ]
    )
    def optional_only_one(_context):  # pylint: disable=unused-argument
        yield Output(output_name="output_one", value=1)

    @solid(input_defs=[InputDefinition("some_input")])
    def should_fail(_context, some_input):  # pylint: disable=unused-argument
        raise Exception("should fail")

    @solid(input_defs=[InputDefinition("some_input")])
    def should_be_skipped(_context, some_input):  # pylint: disable=unused-argument
        pass

    @lambda_solid
    def retries():
        raise RetryRequested()

    return PipelineDefinition(
        name="test_events",
        solid_defs=[
            materialization_and_expectation,
            optional_only_one,
            should_fail,
            should_be_skipped,
            retries,
        ],
        dependencies={
            "optional_only_one": {},
            "should_fail": {
                "some_input": DependencyDefinition(optional_only_one.name, "output_one")
            },
            "should_be_skipped": {
                "some_input": DependencyDefinition(optional_only_one.name, "output_two")
            },
        },
    )


def test_pipeline():
    """just a sanity check to ensure the above pipeline works without layering on graphql"""
    result = execute_pipeline(define_test_events_pipeline(), raise_on_error=False)
    assert result.result_for_solid("materialization_and_expectation").success
    assert not result.result_for_solid("should_fail").success
    assert result.result_for_solid("should_be_skipped").skipped


def test_all_step_events():  # pylint: disable=too-many-locals
    instance = DagsterInstance.ephemeral()

    pipeline_def = define_test_events_pipeline()

    workspace = create_in_process_ephemeral_workspace(
        pointer=CodePointer.from_python_file(
            __file__, define_test_events_pipeline.__name__, working_directory=None
        )
    )

    mode = pipeline_def.get_default_mode_name()
    execution_plan = create_execution_plan(pipeline_def, mode=mode)
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline_def, execution_plan=execution_plan, mode=mode
    )
    step_levels = execution_plan.topological_step_levels()

    unhandled_events = STEP_EVENTS.copy()

    # Exclude types that are not step events
    ignored_events = {
        "LogMessageEvent",
        "PipelineStartEvent",
        "PipelineSuccessEvent",
        "PipelineInitFailureEvent",
        "PipelineFailureEvent",
    }

    event_counts = defaultdict(int)

    for step_level in step_levels:
        for step in step_level:

            variables = {
                "executionParams": {
                    "selector": {
                        "repositoryLocationName": IN_PROCESS_NAME,
                        "repositoryName": get_ephemeral_repository_name(pipeline_def.name),
                        "pipelineName": pipeline_def.name,
                    },
                    "runConfigData": {"storage": {"filesystem": {}}},
                    "mode": mode,
                    "executionMetadata": {"runId": pipeline_run.run_id},
                    "stepKeys": [step.key],
                },
            }
            res = execute_query(workspace, EXECUTE_PLAN_MUTATION, variables, instance=instance,)

            # go through the same dict, decrement all the event records we've seen from the GraphQL
            # response
            if not res.get("errors"):
                assert "data" in res, res
                assert "executePlan" in res["data"], res
                assert "stepEvents" in res["data"]["executePlan"], res
                step_events = res["data"]["executePlan"]["stepEvents"]

                events = [
                    dagster_event_from_dict(e, pipeline_def.name)
                    for e in step_events
                    if e["__typename"] not in ignored_events
                ]

                for event in events:
                    if event.step_key:
                        key = event.step_key + "." + event.event_type_value
                    else:
                        key = event.event_type_value
                    event_counts[key] -= 1
                unhandled_events -= {DagsterEventType(e.event_type_value) for e in events}
            else:
                raise Exception(res["errors"])

    # build up a dict, incrementing all the event records we've produced in the run storage
    logs = instance.all_logs(pipeline_run.run_id)
    for log in logs:
        if not log.dagster_event or (
            DagsterEventType(log.dagster_event.event_type_value)
            not in STEP_EVENTS.union(set([DagsterEventType.ENGINE_EVENT]))
        ):
            continue
        if log.dagster_event.step_key:
            key = log.dagster_event.step_key + "." + log.dagster_event.event_type_value
        else:
            key = log.dagster_event.event_type_value
        event_counts[key] += 1

    # Ensure we've processed all the events that were generated in the run storage
    assert sum(event_counts.values()) == 0

    # Ensure we've handled the universe of event types
    # Why are these retry events not handled? Because right now there is no way to configure retries
    # on executePlan -- this needs to change, and we should separate the ExecutionParams that get
    # sent to executePlan fromm those that get sent to startPipelineExecution and friends
    assert unhandled_events == {DagsterEventType.STEP_UP_FOR_RETRY, DagsterEventType.STEP_RESTARTED}


def test_parse_raw_log_lines():
    raw_log_lines = [
        "Some extraneous log line",
        "Another extraneous log line, JSON data is on the next line",
        '{"data": {"executePlan": {"__typename": "ExecutePlanSuccess"}}}',
    ]

    result = {"data": {"executePlan": {"__typename": "ExecutePlanSuccess"}}}
    assert parse_raw_log_lines(raw_log_lines) == result
