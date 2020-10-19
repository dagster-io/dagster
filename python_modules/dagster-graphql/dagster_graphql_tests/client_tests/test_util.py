from dagster_graphql.client.util import HANDLED_EVENTS

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
from dagster.core.events import STEP_EVENTS, DagsterEventType


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
