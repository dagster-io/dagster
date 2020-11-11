import re

import pytest
from dagster import (
    DagsterInvariantViolationError,
    DagsterTypeCheckDidNotPass,
    Field,
    InputDefinition,
    Int,
    ModeDefinition,
    OutputDefinition,
    composite_solid,
    lambda_solid,
    resource,
    solid,
)
from dagster.core.test_utils import nesting_composite_pipeline
from dagster.core.utility_solids import (
    create_root_solid,
    create_solid_with_deps,
    define_stub_solid,
    input_set,
)
from dagster.utils.test import execute_solid


def test_single_solid_in_isolation():
    @lambda_solid
    def solid_one():
        return 1

    result = execute_solid(solid_one)
    assert result.success
    assert result.output_value() == 1


def test_single_solid_with_single():
    @lambda_solid(input_defs=[InputDefinition(name="num")])
    def add_one_solid(num):
        return num + 1

    result = execute_solid(add_one_solid, input_values={"num": 2})

    assert result.success
    assert result.output_value() == 3


def test_single_solid_with_multiple_inputs():
    @lambda_solid(input_defs=[InputDefinition(name="num_one"), InputDefinition("num_two")])
    def add_solid(num_one, num_two):
        return num_one + num_two

    result = execute_solid(
        add_solid,
        input_values={"num_one": 2, "num_two": 3},
        run_config={"loggers": {"console": {"config": {"log_level": "DEBUG"}}}},
    )

    assert result.success
    assert result.output_value() == 5


def test_single_solid_with_config():
    ran = {}

    @solid(config_schema=Int)
    def check_config_for_two(context):
        assert context.solid_config == 2
        ran["check_config_for_two"] = True

    result = execute_solid(
        check_config_for_two, run_config={"solids": {"check_config_for_two": {"config": 2}}}
    )

    assert result.success
    assert ran["check_config_for_two"]


def test_single_solid_with_context_config():
    @resource(config_schema=Field(Int, is_required=False, default_value=2))
    def num_resource(init_context):
        return init_context.resource_config

    ran = {"count": 0}

    @solid(required_resource_keys={"num"})
    def check_context_config_for_two(context):
        assert context.resources.num == 2
        ran["count"] += 1

    result = execute_solid(
        check_context_config_for_two,
        run_config={"resources": {"num": {"config": 2}}},
        mode_def=ModeDefinition(resource_defs={"num": num_resource}),
    )

    assert result.success
    assert ran["count"] == 1

    result = execute_solid(
        check_context_config_for_two, mode_def=ModeDefinition(resource_defs={"num": num_resource})
    )

    assert result.success
    assert ran["count"] == 2


def test_single_solid_error():
    class SomeError(Exception):
        pass

    @lambda_solid
    def throw_error():
        raise SomeError()

    with pytest.raises(SomeError) as e_info:
        execute_solid(throw_error)

    assert isinstance(e_info.value, SomeError)


def test_single_solid_type_checking_output_error():
    @lambda_solid(output_def=OutputDefinition(Int))
    def return_string():
        return "ksjdfkjd"

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(return_string)


def test_failing_solid_in_isolation():
    class ThisException(Exception):
        pass

    @lambda_solid
    def throw_an_error():
        raise ThisException("nope")

    with pytest.raises(ThisException) as e_info:
        execute_solid(throw_an_error)

    assert isinstance(e_info.value, ThisException)


def test_composites():
    @lambda_solid
    def hello():
        return "hello"

    @composite_solid
    def hello_composite():
        return hello()

    result = execute_solid(hello)
    assert result.success
    assert result.output_value() == "hello"
    assert result.output_values == {"result": "hello"}

    result = execute_solid(hello_composite)
    assert result.success
    assert result.output_value() == "hello"
    assert result.output_values == {"result": "hello"}
    assert result.output_values_for_solid("hello") == {"result": "hello"}
    assert result.output_value_for_handle("hello") == "hello"

    nested_result = result.result_for_solid("hello")
    assert nested_result.success
    assert nested_result.output_value() == "hello"
    assert len(result.solid_result_list) == 1
    assert nested_result.output_values == {"result": "hello"}

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "Tried to get result for solid 'goodbye' in 'hello_composite'. No such top level "
            "solid"
        ),
    ):
        _ = result.result_for_solid("goodbye")


def test_composite_with_no_output_mappings():
    a_source = define_stub_solid("A_source", [input_set("A_input")])
    node_a = create_root_solid("A")
    node_b = create_solid_with_deps("B", node_a)
    node_c = create_solid_with_deps("C", node_a)
    node_d = create_solid_with_deps("D", node_b, node_c)

    @composite_solid
    def diamond_composite():
        a = node_a(a_source())
        node_d(B=node_b(a), C=node_c(a))

    res = execute_solid(diamond_composite)

    assert res.success

    assert res.output_values == {}

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "Output 'result' not defined in composite solid 'diamond_composite': no output "
            "mappings were defined. If you were expecting this output to be present, you may be "
            "missing an output_mapping from an inner solid to its enclosing composite solid."
        ),
    ):
        _ = res.output_value()

    assert len(res.solid_result_list) == 5


def test_execute_nested_composite_solids():
    nested_composite_pipeline = nesting_composite_pipeline(2, 2)
    nested_composite_solid = nested_composite_pipeline.solids[0].definition

    res = execute_solid(nested_composite_solid)

    assert res.success
    assert res.solid.name == "layer_0"

    assert res.output_values == {}

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "Output 'result' not defined in composite solid 'layer_0': no output mappings were "
            "defined. If you were expecting this output to be present, you may be missing an "
            "output_mapping from an inner solid to its enclosing composite solid."
        ),
    ):
        _ = res.output_value()

    assert len(res.solid_result_list) == 2


def test_single_solid_with_bad_inputs():
    @lambda_solid(input_defs=[InputDefinition("num_one", int), InputDefinition("num_two", int)])
    def add_solid(num_one, num_two):
        return num_one + num_two

    result = execute_solid(
        add_solid,
        input_values={"num_one": 2, "num_two": "three"},
        run_config={"loggers": {"console": {"config": {"log_level": "DEBUG"}}}},
        raise_on_error=False,
    )

    assert not result.success
    assert result.failure_data.error.cls_name == "DagsterTypeCheckDidNotPass"
    assert (
        'Type check failed for step input "num_two" - expected type "Int"'
        in result.failure_data.error.message
    )
