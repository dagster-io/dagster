import os
import typing

import pytest
from dagster import (
    CompositeSolidDefinition,
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    Field,
    InputDefinition,
)
from dagster import List as DagsterList
from dagster import (
    Optional,
    Output,
    OutputDefinition,
    PipelineDefinition,
    String,
    composite_solid,
    execute_pipeline,
    execute_solid,
    lambda_solid,
    pipeline,
    solid,
    usable_as_dagster_type,
)
from dagster.core.test_utils import nesting_composite_pipeline
from dagster.core.utility_solids import (
    create_root_solid,
    create_solid_with_deps,
    define_stub_solid,
    input_set,
)
from dagster.utils.test import get_temp_dir

if typing.TYPE_CHECKING:
    List = typing.List
else:
    List = DagsterList


def test_pipeline_in_pipeline():
    @solid
    def a_solid(_):
        pass

    @pipeline
    def inner():
        a_solid()

    @pipeline
    def outer():
        inner()

    assert execute_pipeline(outer).success


@pytest.mark.parametrize(
    "composition_decorator",
    [pytest.param(composite_solid, id="composite_solid"), pytest.param(pipeline, id="pipeline")],
)
def test_composite_basic_execution(composition_decorator):
    a_source = define_stub_solid("A_source", [input_set("A_input")])
    node_a = create_root_solid("A")
    node_b = create_solid_with_deps("B", node_a)
    node_c = create_solid_with_deps("C", node_a)
    node_d = create_solid_with_deps("D", node_b, node_c)

    @composition_decorator
    def diamond_composite():
        a = node_a(a_source())
        node_d(B=node_b(a), C=node_c(a))

    res = execute_solid(diamond_composite)
    assert res.success

    @pipeline
    def test_pipeline_double():
        diamond_composite.alias("D1")()
        diamond_composite.alias("D2")()

    result = execute_pipeline(test_pipeline_double)
    assert result.success

    @composition_decorator
    def wrapped_composite():
        diamond_composite()

    @pipeline
    def test_pipeline_mixed():
        diamond_composite()
        wrapped_composite()

    result = execute_pipeline(test_pipeline_mixed)
    assert result.success

    @composition_decorator
    def empty():
        pass

    @pipeline
    def test_pipeline_empty():
        empty()

    result = execute_pipeline(test_pipeline_empty)
    assert result.success

    nested_pipeline = nesting_composite_pipeline(6, 2)

    result = execute_pipeline(nested_pipeline)
    assert result.success


@pytest.mark.parametrize(
    "composition_decorator",
    [pytest.param(composite_solid, id="composite_solid"), pytest.param(pipeline, id="pipeline")],
)
def test_composite_config(composition_decorator):
    called = {}

    @solid(config_schema=Field(String))
    def configured(context):
        called["configured"] = True
        assert context.solid_config == "yes"

    @composition_decorator
    def inner():
        configured()

    @composition_decorator
    def outer():
        inner()

    @pipeline
    def composites_pipeline():
        outer()

    result = execute_pipeline(
        composites_pipeline,
        {"solids": {"outer": {"solids": {"inner": {"solids": {"configured": {"config": "yes"}}}}}}},
    )
    assert result.success
    assert called["configured"]


@pytest.mark.parametrize(
    "composition_decorator",
    [pytest.param(composite_solid, id="composite_solid"), pytest.param(pipeline, id="pipeline")],
)
def test_composite_config_input(composition_decorator):
    called = {}

    @solid(input_defs=[InputDefinition("one")])
    def node_a(_context, one):
        called["node_a"] = True
        assert one == 1

    @composition_decorator
    def inner():
        node_a()

    @composition_decorator
    def outer():
        inner()

    @pipeline
    def composites_pipeline():
        outer()

    result = execute_pipeline(
        composites_pipeline,
        {
            "solids": {
                "outer": {
                    "solids": {"inner": {"solids": {"node_a": {"inputs": {"one": {"value": 1}}}}}}
                }
            }
        },
    )
    assert result.success
    assert called["node_a"]


@pytest.mark.parametrize(
    "composition_class",
    [
        pytest.param(CompositeSolidDefinition, id="composite_solid"),
        pytest.param(PipelineDefinition, id="pipeline"),
    ],
)
def test_mapped_composite_config_input(composition_class):
    called = {}

    @solid(input_defs=[InputDefinition("one")])
    def node_a(_context, one):
        called["node_a"] = True
        assert one == 1

    assert not node_a.input_has_default("one")

    @composite_solid
    def inner(inner_one):
        node_a(inner_one)

    assert not inner.has_config_mapping

    outer = composition_class(
        name="outer",
        solid_defs=[inner],
        input_mappings=[InputDefinition("outer_one").mapping_to("inner", "inner_one")],
    )

    assert not outer.input_has_default("outer_one")
    assert not outer.has_config_mapping
    pipe = PipelineDefinition(name="composites_pipeline", solid_defs=[outer])

    result = execute_pipeline(pipe, {"solids": {"outer": {"inputs": {"outer_one": {"value": 1}}}}})
    assert result.success
    assert called["node_a"]


@pytest.mark.parametrize(
    "composition_class",
    [
        pytest.param(CompositeSolidDefinition, id="composite_solid"),
        pytest.param(PipelineDefinition, id="pipeline"),
    ],
)
def test_composite_io_mapping(composition_class):
    a_source = define_stub_solid("A_source", [input_set("A_input")])
    node_a = create_root_solid("A")

    node_b = create_solid_with_deps("B", node_a)
    node_c = create_solid_with_deps("C", node_b)

    comp_a_inner = composition_class(
        name="comp_a_inner",
        solid_defs=[a_source, node_a],
        dependencies={"A": {"A_input": DependencyDefinition("A_source")}},
        output_mappings=[OutputDefinition().mapping_from("A")],
    )

    comp_a_outer = composition_class(
        name="comp_a_outer",
        solid_defs=[comp_a_inner],
        output_mappings=[OutputDefinition().mapping_from("comp_a_inner")],
    )

    comp_bc_inner = composition_class(
        name="comp_bc_inner",
        solid_defs=[node_b, node_c],
        dependencies={"C": {"B": DependencyDefinition("B")}},
        input_mappings=[
            InputDefinition(name="inner_B_in").mapping_to(solid_name="B", input_name="A")
        ],
    )

    comp_bc_outer = composition_class(
        name="comp_bc_outer",
        solid_defs=[comp_bc_inner],
        dependencies={},
        input_mappings=[
            InputDefinition(name="outer_B_in").mapping_to(
                solid_name="comp_bc_inner", input_name="inner_B_in"
            )
        ],
    )

    @pipeline
    def wrapped_io():
        comp_bc_outer(comp_a_outer())

    result = execute_pipeline(wrapped_io)
    assert result.success


@pytest.mark.parametrize(
    "composition_class",
    [
        pytest.param(CompositeSolidDefinition, id="composite_solid"),
        pytest.param(PipelineDefinition, id="pipeline"),
    ],
)
def test_io_error_is_decent(composition_class):
    with pytest.raises(DagsterInvalidDefinitionError, match="mapping_to"):
        composition_class(
            name="comp_a_outer", solid_defs=[], input_mappings=[InputDefinition("should_be_mapped")]
        )

    with pytest.raises(DagsterInvalidDefinitionError, match="mapping_from"):
        composition_class(name="comp_a_outer", solid_defs=[], output_mappings=[OutputDefinition()])


@pytest.mark.parametrize(
    "composition_decorator",
    [pytest.param(composite_solid, id="composite_solid"), pytest.param(pipeline, id="pipeline")],
)
def test_types_descent(composition_decorator):
    @usable_as_dagster_type
    class Foo:
        pass

    @solid(output_defs=[OutputDefinition(Foo)])
    def inner_solid(_context):
        return Foo()

    @composition_decorator
    def middle_solid():
        inner_solid()

    @composition_decorator
    def outer_solid():
        middle_solid()

    @pipeline
    def layered_types():
        outer_solid()

    assert layered_types.has_dagster_type("Foo")


@pytest.mark.parametrize(
    "composition_decorator",
    [pytest.param(composite_solid, id="composite_solid"), pytest.param(pipeline, id="pipeline")],
)
def test_deep_mapping(composition_decorator):
    @lambda_solid(output_def=OutputDefinition(String))
    def echo(blah):
        return blah

    @lambda_solid(output_def=OutputDefinition(String))
    def emit_foo():
        return "foo"

    @composition_decorator(output_defs=[OutputDefinition(String, "z")])
    def az(a):
        return echo(a)

    @composition_decorator(output_defs=[OutputDefinition(String, "y")])
    def by(b):
        return az(b)

    @composition_decorator(output_defs=[OutputDefinition(String, "x")])
    def cx(c):
        return by(c)

    @pipeline
    def nested():
        echo(cx(emit_foo()))

    result = execute_pipeline(nested)
    assert result.result_for_solid("echo").output_value() == "foo"


@pytest.mark.parametrize(
    "composition_decorator",
    [pytest.param(composite_solid, id="composite_solid"), pytest.param(pipeline, id="pipeline")],
)
def test_mapping_parallel_composite(composition_decorator):
    @lambda_solid(output_def=OutputDefinition(int))
    def one():
        return 1

    @lambda_solid(output_def=OutputDefinition(int))
    def two():
        return 2

    @lambda_solid(
        input_defs=[
            InputDefinition(dagster_type=int, name="a"),
            InputDefinition(dagster_type=int, name="b"),
        ],
        output_def=OutputDefinition(int),
    )
    def adder(a, b):
        return a + b

    @composition_decorator(
        output_defs=[
            OutputDefinition(dagster_type=int, name="two"),
            OutputDefinition(dagster_type=int, name="four"),
        ]
    )
    def composite_adder():
        result_one = one()
        result_two = two()

        calc_two = adder.alias("calc_two")
        calc_four = adder.alias("calc_four")

        calc_result_two = calc_two(result_one, result_one)
        calc_result_four = calc_four(result_two, result_two)

        return {"two": calc_result_two, "four": calc_result_four}

    @lambda_solid
    def assert_four(val):
        assert val == 4

    @lambda_solid
    def assert_two(val):
        assert val == 2

    @pipeline
    def recreate_issue_pipeline():
        result = composite_adder()

        assert_two(result.two)  # pylint: disable=no-member
        assert_four(result.four)  # pylint: disable=no-member

    assert execute_pipeline(recreate_issue_pipeline).success


@pytest.mark.parametrize(
    "composition_decorator",
    [pytest.param(composite_solid, id="composite_solid"), pytest.param(pipeline, id="pipeline")],
)
def test_composite_config_driven_materialization(composition_decorator):
    @lambda_solid
    def one():
        return 1

    @composition_decorator(output_defs=[OutputDefinition()])
    def wrap_one():
        return one()

    @pipeline
    def composite_config_driven_materialization_pipeline():
        wrap_one()

    with get_temp_dir() as write_directory:
        write_location = os.path.join(write_directory, "wrap_one.json")
        execute_pipeline(
            composite_config_driven_materialization_pipeline,
            run_config={
                "solids": {
                    "wrap_one": {"outputs": [{"result": {"json": {"path": write_location}}}]}
                }
            },
        )

        assert os.path.exists(write_location)


@pytest.mark.parametrize(
    "composition_class",
    [
        pytest.param(CompositeSolidDefinition, id="composite_solid"),
        pytest.param(PipelineDefinition, id="pipeline"),
    ],
)
def test_mapping_errors(composition_class):
    @lambda_solid
    def echo(foo):
        return foo

    with pytest.raises(
        DagsterInvalidDefinitionError, match="references solid 'inner' which it does not contain"
    ):
        composition_class(
            name="bad",
            solid_defs=[echo],
            input_mappings=[InputDefinition("mismatch").mapping_to("inner", "foo")],
        )

    with pytest.raises(DagsterInvalidDefinitionError, match="no input named 'bar'"):
        composition_class(
            name="bad",
            solid_defs=[echo],
            input_mappings=[InputDefinition("mismatch").mapping_to("echo", "bar")],
        )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="InputMapping source and destination must have the same type",
    ):
        composition_class(
            name="bad",
            solid_defs=[echo],
            input_mappings=[InputDefinition("mismatch", str).mapping_to("echo", "foo")],
        )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="mappings with same definition name but different definitions",
    ):
        composition_class(
            name="bad",
            solid_defs=[echo],
            input_mappings=[
                InputDefinition("mismatch").mapping_to("echo", "foo"),
                InputDefinition("mismatch").mapping_to("echo_2", "foo"),
            ],
        )

    with pytest.raises(
        DagsterInvalidDefinitionError, match="references solid 'inner' which it does not contain"
    ):
        composition_class(
            name="bad",
            solid_defs=[echo],
            output_mappings=[OutputDefinition().mapping_from("inner", "result")],
        )

    with pytest.raises(DagsterInvalidDefinitionError, match="no output named 'return'"):
        composition_class(
            name="bad",
            solid_defs=[echo],
            output_mappings=[OutputDefinition().mapping_from("echo", "return")],
        )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="OutputMapping source and destination must have the same type",
    ):
        composition_class(
            name="bad",
            solid_defs=[echo],
            output_mappings=[OutputDefinition(str).mapping_from("echo", "result")],
        )


@pytest.mark.parametrize(
    "composition_decorator",
    [pytest.param(composite_solid, id="composite_solid"), pytest.param(pipeline, id="pipeline")],
)
def test_composite_skippable_output_result(composition_decorator):
    @lambda_solid(output_def=OutputDefinition(int))
    def emit_one():
        return 1

    @lambda_solid(output_def=OutputDefinition(Optional[float]))
    def echo(x):
        return x

    @solid(output_defs=[OutputDefinition(Optional[float], name="foo_output", is_required=False)])
    def foo_solid(_, condition=False):
        if condition:
            yield Output(1.0, "foo_output")

    @composition_decorator(
        output_defs=[
            OutputDefinition(Optional[float], name="foo_output", is_required=False),
            OutputDefinition(int, name="one_output"),
        ]
    )
    def foo_composite():
        return {"foo_output": foo_solid(), "one_output": emit_one()}

    @composition_decorator(
        output_defs=[
            OutputDefinition(Optional[float], name="foo_output", is_required=False),
        ]
    )
    def baz_composite():
        return {"foo_output": echo(foo_solid())}

    result = execute_solid(foo_composite)
    assert result.output_values == {"one_output": 1}

    result = execute_solid(baz_composite)
    assert result.output_values == {}


def test_input_mapping_fan_in():
    @solid
    def operate_two_nums(_context, nums: List[float]):
        return nums[1] / nums[0]

    @solid
    def combine(_context, num1: float, num2: float):
        result = num2 + num1
        return result

    @composite_solid
    def example_computation(num1: float = 1.0, num2: float = 1.0):
        res1 = operate_two_nums.alias("res1")
        res2 = operate_two_nums.alias("res2")
        return combine(res1([num1, num2]), res2([num1, num2]))

    @pipeline
    def example_computation_pipeline():
        example_computation()

    # from config
    result = execute_pipeline(
        example_computation_pipeline,
        run_config={"solids": {"example_computation": {"inputs": {"num1": 1, "num2": 5}}}},
    )
    assert result.success
    assert result.output_for_solid("example_computation") == 10.0

    # from default
    result = execute_pipeline(example_computation_pipeline)
    assert result.success
    assert result.output_for_solid("example_computation") == 2.0


@pytest.mark.parametrize(
    "composition_decorator",
    [pytest.param(composite_solid, id="composite_solid"), pytest.param(pipeline, id="pipeline")],
)
def test_convertable_config_schema(composition_decorator):
    @solid(config_schema=int)
    def add_one(context) -> int:
        return context.solid_config + 1

    @composition_decorator(
        config_schema=int,
        config_fn=lambda cfg: {"add_one": {"config": 3}},
        # need to do this because pipeline still requires explicit output
        # defintion with return value
        # TODO ensure issue is filed
        output_defs=[OutputDefinition(int)],
    )
    def comp() -> int:
        return add_one()

    result = execute_solid(comp, run_config={"solids": {"comp": {"config": 3}}})
    assert result.success

    assert result.output_value() == 4
