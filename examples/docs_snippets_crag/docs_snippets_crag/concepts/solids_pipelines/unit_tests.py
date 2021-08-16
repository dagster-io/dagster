"""isort:skip_file"""
from dagster import (
    AssetMaterialization,
    DagsterEventType,
    ExpectationResult,
    InputDefinition,
    Output,
    OutputDefinition,
    PipelineExecutionResult,
    SolidExecutionResult,
    execute_pipeline,
    execute_solid,
    pipeline,
    solid,
)


@solid(
    input_defs=[InputDefinition(name="num", dagster_type=int, default_value=1)],
)
def add_one(num: int) -> int:
    return num + 1


@solid(
    input_defs=[InputDefinition(name="num", dagster_type=int, default_value=1)],
)
def add_two(num: int) -> int:
    return num + 2


@solid
def subtract(left: int, right: int) -> int:
    return left - right


@pipeline
def do_math():
    subtract(add_one(), add_two())


@solid(
    input_defs=[InputDefinition(name="input_num", dagster_type=int)],
    output_defs=[OutputDefinition(name="a_num", dagster_type=int)],
)
def emit_events_solid(input_num):
    a_num = input_num + 1
    yield ExpectationResult(
        success=a_num > 0, label="positive", description="A num must be positive"
    )
    yield AssetMaterialization(
        asset_key="persisted_string", description="Let us pretend we persisted the string somewhere"
    )
    yield Output(value=a_num, output_name="a_num")


@pipeline
def emit_events_pipeline():
    emit_events_solid()


# start_test_pipeline_marker
def test_pipeline():
    result = execute_pipeline(do_math)

    # return type is PipelineExecutionResult
    assert isinstance(result, PipelineExecutionResult)
    assert result.success
    # inspect individual solid result
    assert result.output_for_solid("add_one") == 2
    assert result.output_for_solid("add_two") == 3
    assert result.output_for_solid("subtract") == -1


# end_test_pipeline_marker


# start_test_execute_solid_marker
def test_solid():
    result = execute_solid(add_one)

    # return type is SolidExecutionResult
    assert isinstance(result, SolidExecutionResult)
    assert result.success
    # check the solid output value
    assert result.output_value() == 2


# end_test_execute_solid_marker

# start_invocation_solid_marker
@solid
def my_solid_to_test():
    return 5


# end_invocation_solid_marker

# start_test_solid_marker
def test_solid_with_invocation():
    assert my_solid_to_test() == 5


# end_test_solid_marker

# start_invocation_solid_inputs_marker
@solid
def my_solid_with_inputs(x, y):
    return x + y


# end_invocation_solid_inputs_marker

# start_test_solid_with_inputs_marker
def test_inputs_solid_with_invocation():
    assert my_solid_with_inputs(5, 6) == 11


# end_test_solid_with_inputs_marker

# start_solid_requires_foo_marker
@solid(required_resource_keys={"foo"})
def solid_requires_foo(context):
    return f"found {context.resources.foo}"


# end_solid_requires_foo_marker

# start_test_solid_context_marker
from dagster import build_solid_context


def test_solid_with_context():
    context = build_solid_context(resources={"foo": "bar"})
    assert solid_requires_foo(context) == "found bar"


# end_test_solid_context_marker

from dagster import resource

# start_test_resource_def_marker
@resource(config_schema={"my_str": str})
def my_foo_resource(context):
    return context.resource_config["my_str"]


def test_solid_resource_def():
    context = build_solid_context(resources={"foo": my_foo_resource.configured({"my_str": "bar"})})
    assert solid_requires_foo(context) == "found bar"


# end_test_resource_def_marker

# start_test_pipeline_with_config
def test_pipeline_with_config():
    result = execute_pipeline(
        do_math,
        run_config={
            "solids": {"add_one": {"inputs": {"num": 2}}, "add_two": {"inputs": {"num": 3}}}
        },
    )

    assert result.success

    assert result.output_for_solid("add_one") == 3
    assert result.output_for_solid("add_two") == 5
    assert result.output_for_solid("subtract") == -2


# end_test_pipeline_with_config

# start_test_subset_execution


def test_subset_execution():
    result = execute_pipeline(
        do_math,
        solid_selection=["add_one", "add_two"],
    )

    assert result.success
    assert result.output_for_solid("add_one") == 2
    assert result.output_for_solid("add_two") == 3

    # solid_result_list returns List[SolidExecutionResult]
    # this checks to see that only two were executed
    assert {solid_result.solid.name for solid_result in result.solid_result_list} == {
        "add_one",
        "add_two",
    }


# end_test_subset_execution


# start_test_event_stream
def test_event_stream():
    pipeline_result = execute_pipeline(
        emit_events_pipeline, {"solids": {"emit_events_solid": {"inputs": {"input_num": 1}}}}
    )
    assert pipeline_result.success

    solid_result = pipeline_result.result_for_solid("emit_events_solid")

    assert isinstance(solid_result, SolidExecutionResult)

    # when one has multiple outputs, you need to specify output name
    assert solid_result.output_value(output_name="a_num") == 2

    assert [se.event_type for se in solid_result.step_events] == [
        DagsterEventType.STEP_START,
        DagsterEventType.STEP_INPUT,
        DagsterEventType.STEP_EXPECTATION_RESULT,
        DagsterEventType.ASSET_MATERIALIZATION,
        DagsterEventType.STEP_OUTPUT,
        DagsterEventType.HANDLED_OUTPUT,
        DagsterEventType.STEP_SUCCESS,
    ]

    # solids communicate what they did via the event stream, viewable in tools (e.g. dagit)
    (
        _start,
        _input_event,
        expectation_event,
        materialization_event,
        _num_output_event,
        _num_handled_output_operation,
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


# end_test_event_stream
