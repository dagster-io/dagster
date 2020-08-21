from dagster import (
    AssetMaterialization,
    DagsterEventType,
    ExpectationResult,
    PipelineExecutionResult,
    SolidExecutionResult,
    execute_pipeline,
)

from ..repo import do_math, emit_events_pipeline


def test_full_execution():
    result = execute_pipeline(
        do_math, {"solids": {"add_one": {"inputs": {"num": 2}}, "add_two": {"inputs": {"num": 3}}}}
    )

    # return type is PipelineExecutionResult
    assert isinstance(result, PipelineExecutionResult)

    assert result.success

    assert result.output_for_solid("add_one") == 3
    assert result.output_for_solid("add_two") == 5
    assert result.output_for_solid("subtract") == -2


def test_subset_execution():
    result = execute_pipeline(
        do_math,
        {"solids": {"add_one": {"inputs": {"num": 2}}, "add_two": {"inputs": {"num": 3}}}},
        solid_selection=["add_one", "add_two"],
    )

    assert result.success
    assert result.output_for_solid("add_one") == 3
    assert result.output_for_solid("add_two") == 5

    # solid_result_list returns List[SolidExecutionResult]
    # this checks to see that only two were executed
    assert {solid_result.solid.name for solid_result in result.solid_result_list} == {
        "add_one",
        "add_two",
    }


def test_event_stream():
    pipeline_result = execute_pipeline(
        emit_events_pipeline, {"solids": {"emit_events_solid": {"inputs": {"input_num": 1}}}}
    )
    assert pipeline_result.success

    solid_result = pipeline_result.result_for_solid("emit_events_solid")

    assert isinstance(solid_result, SolidExecutionResult)

    # when one has multiple outputs, you need to specify output name
    assert solid_result.output_value(output_name="a_num") == 2
    assert solid_result.output_value(output_name="a_string") == "foo"

    assert [se.event_type for se in solid_result.step_events] == [
        DagsterEventType.STEP_START,
        DagsterEventType.STEP_INPUT,
        DagsterEventType.STEP_EXPECTATION_RESULT,
        DagsterEventType.STEP_MATERIALIZATION,
        DagsterEventType.STEP_OUTPUT,
        DagsterEventType.STEP_OUTPUT,
        DagsterEventType.STEP_SUCCESS,
    ]

    # solids communicate what they did via the event stream, viewable in tools (e.g. dagit)
    (
        _start,
        _input_event,
        expectation_event,
        materialization_event,
        _num_output_event,
        _str_output_event,
        _success,
    ) = solid_result.step_events

    # apologies for verboseness here! we can do better.
    expectation_result = expectation_event.event_specific_data.expectation_result
    assert isinstance(expectation_result, ExpectationResult)
    assert expectation_result.success
    assert expectation_result.label == "positive"

    materialization = materialization_event.event_specific_data.materialization
    assert isinstance(materialization, AssetMaterialization)
    assert materialization.label == "persisted_string"
