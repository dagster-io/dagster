import pytest
from dagster import (
    ConfigMapping,
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    Enum,
    EnumValue,
    Field,
    In,
    Output,
    String,
    configured,
    graph,
    job,
    mem_io_manager,
    op,
)
from dagster._core.definitions.input import GraphIn
from dagster._core.system_config.composite_descent import composite_descent


def test_single_level_job():
    @op(config_schema=int)
    def return_int(context):
        return context.op_config

    @job
    def return_int_job():
        return_int()

    result = return_int_job.execute_in_process({"ops": {"return_int": {"config": 2}}})

    assert result.success
    assert result.output_for_node("return_int") == 2


def test_single_op_job_composite_descent():
    @op(config_schema=int)
    def return_int(context):
        return context.op_config

    @job
    def return_int_job():
        return_int()

    op_config_dict = composite_descent(
        return_int_job,
        {"return_int": {"config": 3}},
        resource_defs={"io_manager": mem_io_manager},
    )

    assert op_config_dict["return_int"].config == 3

    result = return_int_job.execute_in_process({"ops": {"return_int": {"config": 3}}})

    assert result.success
    assert result.output_for_node("return_int") == 3


def test_single_layer_job_composite_descent():
    @op(config_schema=int)
    def return_int(context):
        return context.op_config

    @graph
    def return_int_passthrough():
        return_int()

    @job
    def return_int_job_passthrough():
        return_int_passthrough()

    op_config_dict = composite_descent(
        return_int_job_passthrough,
        {"return_int_passthrough": {"ops": {"return_int": {"config": 34}}}},
        resource_defs={"io_manager": mem_io_manager},
    )

    handle = "return_int_passthrough.return_int"
    assert op_config_dict[handle].config == 34

    result = return_int_job_passthrough.execute_in_process(
        {
            "ops": {"return_int_passthrough": {"ops": {"return_int": {"config": 34}}}},
        },
    )

    assert result.success
    assert result.output_for_node(handle) == 34


def test_single_layer_job_hardcoded_config_mapping():
    @op(config_schema=int)
    def return_int(context):
        return context.op_config

    @graph(
        config=ConfigMapping(
            config_schema={}, config_fn=lambda _cfg: {"return_int": {"config": 35}}
        )
    )
    def return_int_hardcode_wrap():
        return_int()

    @job
    def return_int_hardcode_wrap_job():
        return_int_hardcode_wrap()

    op_config_dict = composite_descent(
        return_int_hardcode_wrap_job,
        {},
        resource_defs={"io_manager": mem_io_manager},
    )

    assert op_config_dict["return_int_hardcode_wrap.return_int"].config == 35


def test_single_layer_job_computed_config_mapping():
    @op(config_schema=int)
    def return_int(context):
        return context.op_config

    def _config_fn(cfg):
        return {"return_int": {"config": cfg["number"] + 1}}

    @graph(config=ConfigMapping(config_schema={"number": int}, config_fn=_config_fn))
    def return_int_plus_one():
        return_int()

    @job
    def return_int_hardcode_wrap_job():
        return_int_plus_one()

    op_config_dict = composite_descent(
        return_int_hardcode_wrap_job,
        {"return_int_plus_one": {"config": {"number": 23}}},
        resource_defs={"io_manager": mem_io_manager},
    )

    assert op_config_dict["return_int_plus_one.return_int"].config == 24


def test_mix_layer_computed_mapping():
    @op(config_schema=int)
    def return_int(context):
        return context.op_config

    @graph(
        config=ConfigMapping(
            config_schema={"number": int},
            config_fn=lambda cfg: {"return_int": {"config": cfg["number"] + 1}},
        )
    )
    def layer_three_wrap():
        return_int()

    def _layer_two_double_wrap_cfg_fn(cfg):
        if cfg["inject_error"]:
            return {"layer_three_wrap": {"config": {"number": "a_string"}}}
        else:
            return {"layer_three_wrap": {"config": {"number": cfg["number"] + 1}}}

    @graph(
        config=ConfigMapping(
            config_schema={"number": int, "inject_error": bool},
            config_fn=_layer_two_double_wrap_cfg_fn,
        )
    )
    def layer_two_double_wrap():
        layer_three_wrap()

    @graph
    def layer_two_passthrough():
        return_int()

    @graph
    def layer_one():
        layer_two_passthrough()
        layer_two_double_wrap()

    @job
    def layered_config():
        layer_one()

    op_config_dict = composite_descent(
        layered_config,
        {
            "layer_one": {
                "ops": {
                    "layer_two_passthrough": {"ops": {"return_int": {"config": 234}}},
                    "layer_two_double_wrap": {"config": {"number": 5, "inject_error": False}},
                }
            }
        },
        resource_defs={"io_manager": mem_io_manager},
    )

    assert op_config_dict["layer_one.layer_two_passthrough.return_int"].config == 234
    # this passed through both config fns which each added one
    assert op_config_dict["layer_one.layer_two_double_wrap.layer_three_wrap.return_int"].config == 7

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        composite_descent(
            layered_config,
            {
                "layer_one": {
                    "ops": {
                        "layer_two_passthrough": {"ops": {"return_int": {"config": 234}}},
                        "layer_two_double_wrap": {"config": {"number": 234, "inject_error": True}},
                    }
                }
            },
            resource_defs={"io_manager": mem_io_manager},
        )

    assert 'Op "layer_two_double_wrap" with definition "layer_two_double_wrap"' in str(
        exc_info.value
    )
    assert (
        'Error 1: Invalid scalar at path root:layer_three_wrap:config:number. Value "a_string"'
        in str(exc_info.value)
    )

    result = layered_config.execute_in_process(
        {
            "ops": {
                "layer_one": {
                    "ops": {
                        "layer_two_passthrough": {"ops": {"return_int": {"config": 55}}},
                        "layer_two_double_wrap": {"config": {"number": 7, "inject_error": False}},
                    }
                }
            },
        },
    )

    assert result.output_for_node("layer_one.layer_two_passthrough.return_int") == 55
    assert (
        result.output_for_node("layer_one.layer_two_double_wrap.layer_three_wrap.return_int") == 9
    )


def test_nested_input_via_config_mapping():
    @op
    def add_one(_, num):
        return num + 1

    @graph(
        config=ConfigMapping(
            config_schema={},
            config_fn=lambda _cfg: {"add_one": {"inputs": {"num": {"value": 2}}}},
        )
    )
    def wrap_add_one():
        add_one()

    @job
    def wrap_add_one_job():
        wrap_add_one()

    op_config_dict = composite_descent(
        wrap_add_one_job, {}, resource_defs={"io_manager": mem_io_manager}
    )
    assert op_config_dict["wrap_add_one.add_one"].inputs == {"num": {"value": 2}}

    result = wrap_add_one_job.execute_in_process()
    assert result.success
    assert result.output_for_node("wrap_add_one.add_one") == 3


def test_double_nested_input_via_config_mapping():
    @op
    def number(num):
        return num

    @graph(
        config=ConfigMapping(
            config_schema={},
            config_fn=lambda _: {"number": {"inputs": {"num": {"value": 4}}}},
        )
    )
    def wrap_graph():
        return number()

    @graph
    def double_wrap(num):
        number(num)
        return wrap_graph()

    @job
    def wrap_job_double_nested_input():
        double_wrap()

    node_handle_dict = composite_descent(
        wrap_job_double_nested_input,
        {"double_wrap": {"inputs": {"num": {"value": 2}}}},
        resource_defs={"io_manager": mem_io_manager},
    )
    assert node_handle_dict["double_wrap.wrap_graph.number"].inputs == {"num": {"value": 4}}
    assert node_handle_dict["double_wrap"].inputs == {"num": {"value": 2}}

    result = wrap_job_double_nested_input.execute_in_process(
        {"ops": {"double_wrap": {"inputs": {"num": {"value": 2}}}}},
    )
    assert result.success


def test_provide_one_of_two_inputs_via_config():
    @op(
        config_schema={
            "config_field_a": Field(String),
            "config_field_b": Field(String),
        },
        ins={
            "input_a": In(String),
            "input_b": In(String),
        },
    )
    def basic(context, input_a, input_b):
        res = ".".join(
            [
                context.op_config["config_field_a"],
                context.op_config["config_field_b"],
                input_a,
                input_b,
            ]
        )
        yield Output(res)

    @graph(
        config=ConfigMapping(
            config_fn=lambda cfg: {
                "basic": {
                    "config": {
                        "config_field_a": cfg["config_field_a"],
                        "config_field_b": cfg["config_field_b"],
                    },
                    "inputs": {"input_b": {"value": "set_input_b"}},
                }
            },
            config_schema={
                "config_field_a": Field(String),
                "config_field_b": Field(String),
            },
        )
    )
    def wrap_all_config_one_input(input_a):
        return basic(input_a)

    @job(name="config_mapping")
    def config_mapping_job():
        wrap_all_config_one_input()

    ops_config_dict = {
        "wrap_all_config_one_input": {
            "config": {"config_field_a": "override_a", "config_field_b": "override_b"},
            "inputs": {"input_a": {"value": "set_input_a"}},
        }
    }

    result = config_mapping_job.execute_in_process({"ops": ops_config_dict})
    assert result.success

    assert result.success
    assert (
        result.output_for_node("wrap_all_config_one_input")
        == "override_a.override_b.set_input_a.set_input_b"
    )


@op(config_schema=Field(String, is_required=False))
def scalar_config_op(context):
    yield Output(context.op_config)


@op(config_schema=Field(String, is_required=True))
def required_scalar_config_op(context):
    yield Output(context.op_config)


@graph(
    config=ConfigMapping(
        config_schema={"override_str": Field(String)},
        config_fn=lambda cfg: {"layer2": {"config": cfg["override_str"]}},
    )
)
def wrap():
    return scalar_config_op.alias("layer2")()


@graph(
    config=ConfigMapping(
        config_schema={"nesting_override": Field(String)},
        config_fn=lambda cfg: {"layer1": {"config": {"override_str": cfg["nesting_override"]}}},
    )
)
def nesting_wrap():
    return wrap.alias("layer1")()


@job
def wrap_job():
    nesting_wrap.alias("layer0")()


@graph
def wrap_no_mapping():
    return required_scalar_config_op.alias("layer2")()


@graph
def nesting_wrap_no_mapping():
    return wrap_no_mapping.alias("layer1")()


@job
def no_wrap_job():
    nesting_wrap_no_mapping.alias("layer0")()


def get_fully_unwrapped_config():
    return {"ops": {"layer0": {"ops": {"layer1": {"ops": {"layer2": {"config": "blah"}}}}}}}


def test_direct_composite_descent_with_error():
    @graph(
        config=ConfigMapping(
            config_schema={"override_str": Field(int)},
            config_fn=lambda cfg: {"layer2": {"config": cfg["override_str"]}},
        )
    )
    def wrap_coerce_to_wrong_type():
        return scalar_config_op.alias("layer2")()

    @graph(
        config=ConfigMapping(
            config_schema={"nesting_override": Field(int)},
            config_fn=lambda cfg: {"layer1": {"config": {"override_str": cfg["nesting_override"]}}},
        )
    )
    def nesting_wrap_wrong_type_at_leaf():
        return wrap_coerce_to_wrong_type.alias("layer1")()

    @job
    def wrap_job_with_error():
        nesting_wrap_wrong_type_at_leaf.alias("layer0")()

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        composite_descent(
            wrap_job_with_error,
            {"layer0": {"config": {"nesting_override": 214}}},
            resource_defs={"io_manager": mem_io_manager},
        )

    assert "In job wrap_job_with_error at stack layer0:layer1:" in str(exc_info.value)

    assert (
        'Op "layer1" with definition "wrap_coerce_to_wrong_type" has a configuration error.'
        in str(exc_info.value)
    )
    assert 'Error 1: Invalid scalar at path root:layer2:config. Value "214"' in str(exc_info.value)


def test_new_nested_ops_no_mapping():
    result = no_wrap_job.execute_in_process(get_fully_unwrapped_config())

    assert result.success
    assert result.output_for_node("layer0.layer1.layer2") == "blah"


def test_new_multiple_overrides_job():
    result = wrap_job.execute_in_process(
        {
            "ops": {"layer0": {"config": {"nesting_override": "blah"}}},
            "loggers": {"console": {"config": {"log_level": "ERROR"}}},
        },
    )

    assert result.success
    assert result.output_for_node("layer0.layer1.layer2") == "blah"


def test_config_mapped_enum():
    from enum import Enum as PythonEnum

    class TestPythonEnum(PythonEnum):
        VALUE_ONE = 0
        OTHER = 1

    DagsterEnumType = Enum(
        "MappedTestEnum",
        [
            EnumValue("VALUE_ONE", TestPythonEnum.VALUE_ONE),
            EnumValue("OTHER", TestPythonEnum.OTHER),
        ],
    )

    @op(config_schema={"enum": DagsterEnumType})
    def return_enum(context):
        return context.op_config["enum"]

    @graph(
        config=ConfigMapping(
            config_schema={"num": int},
            config_fn=lambda cfg: {
                "return_enum": {"config": {"enum": "VALUE_ONE" if cfg["num"] == 1 else "OTHER"}}
            },
        )
    )
    def wrapping_return_enum():
        return return_enum()

    @job
    def wrapping_return_enum_job():
        wrapping_return_enum()

    assert (
        wrapping_return_enum_job.execute_in_process(
            {"ops": {"wrapping_return_enum": {"config": {"num": 1}}}},
        ).output_for_node("wrapping_return_enum")
        == TestPythonEnum.VALUE_ONE
    )

    assert (
        wrapping_return_enum_job.execute_in_process(
            {"ops": {"wrapping_return_enum": {"config": {"num": -11}}}},
        ).output_for_node("wrapping_return_enum")
        == TestPythonEnum.OTHER
    )

    @op(config_schema={"num": int})
    def return_int(context):
        return context.op_config["num"]

    @graph(
        config=ConfigMapping(
            config_schema={"enum": DagsterEnumType},
            config_fn=lambda cfg: {
                "return_int": {
                    "config": {"num": 1 if cfg["enum"] == TestPythonEnum.VALUE_ONE else 2}
                }
            },
        )
    )
    def wrap_return_int():
        return return_int()

    @job
    def wrap_return_int_job():
        wrap_return_int()

    assert (
        wrap_return_int_job.execute_in_process(
            {"ops": {"wrap_return_int": {"config": {"enum": "VALUE_ONE"}}}},
        ).output_for_node("wrap_return_int")
        == 1
    )

    assert (
        wrap_return_int_job.execute_in_process(
            {"ops": {"wrap_return_int": {"config": {"enum": "OTHER"}}}},
        ).output_for_node("wrap_return_int")
        == 2
    )


def test_single_level_job_with_configured_op():
    @op(config_schema=int)
    def return_int(context):
        return context.op_config

    return_int_5 = configured(return_int, name="return_int_5")(5)

    @job
    def return_int_job():
        return_int_5()

    result = return_int_job.execute_in_process()

    assert result.success
    assert result.output_for_node("return_int_5") == 5


def test_configured_op_with_inputs():
    @op(config_schema=str, ins={"x": In(int)})
    def return_int(context, x):
        assert context.op_config == "config sentinel"
        return x

    return_int_configured = configured(return_int, name="return_int_configured")("config sentinel")

    @job
    def return_int_job():
        return_int_configured()

    result = return_int_job.execute_in_process(
        {"ops": {"return_int_configured": {"inputs": {"x": 6}}}}
    )

    assert result.success
    assert result.output_for_node("return_int_configured") == 6


def test_single_level_job_with_complex_configured_op_within_composite():
    @op(config_schema={"age": int, "name": str})
    def introduce(context):
        return "{name} is {age} years old".format(**context.op_config)

    @configured(introduce, {"age": int})
    def introduce_aj(config):
        return {"name": "AJ", "age": config["age"]}

    assert introduce_aj.name == "introduce_aj"

    @graph(
        config=ConfigMapping(
            config_schema={"num_as_str": str},
            config_fn=lambda cfg: {"introduce_aj": {"config": {"age": int(cfg["num_as_str"])}}},
        )
    )
    def introduce_wrapper():
        return introduce_aj()

    @job
    def introduce_job():
        introduce_wrapper()

    result = introduce_job.execute_in_process(
        {"ops": {"introduce_wrapper": {"config": {"num_as_str": "20"}}}},
    )

    assert result.success
    assert result.output_for_node("introduce_wrapper") == "AJ is 20 years old"


def test_single_level_job_with_complex_configured_op():
    @op(config_schema={"age": int, "name": str})
    def introduce(context):
        return "{name} is {age} years old".format(**context.op_config)

    introduce_aj = configured(introduce, name="introduce_aj")({"age": 20, "name": "AJ"})

    @job
    def introduce_job():
        introduce_aj()

    result = introduce_job.execute_in_process()

    assert result.success
    assert result.output_for_node("introduce_aj") == "AJ is 20 years old"


def test_single_level_job_with_complex_configured_op_nested():
    @op(config_schema={"age": int, "name": str})
    def introduce(context):
        return "{name} is {age} years old".format(**context.op_config)

    @configured(introduce, {"age": int})
    def introduce_aj(config):
        return {"name": "AJ", "age": config["age"]}

    introduce_aj_20 = configured(introduce_aj, name="introduce_aj_20")({"age": 20})

    @job
    def introduce_job():
        introduce_aj_20()

    result = introduce_job.execute_in_process()

    assert result.success
    assert result.output_for_node("introduce_aj_20") == "AJ is 20 years old"


def test_single_level_job_with_configured_graph():
    @op(config_schema={"inner": int})
    def multiply_by_two(context):
        return context.op_config["inner"] * 2

    @op
    def add(_context, lhs, rhs):
        return lhs + rhs

    @graph(
        config=ConfigMapping(
            config_schema={"outer": int},
            config_fn=lambda c: {
                "multiply_by_two": {"config": {"inner": c["outer"]}},
                "multiply_by_two_again": {"config": {"inner": c["outer"]}},
            },
        )
    )
    def multiply_by_four():
        return add(multiply_by_two(), multiply_by_two.alias("multiply_by_two_again")())

    multiply_three_by_four = configured(multiply_by_four, name="multiply_three_by_four")(
        {"outer": 3}
    )

    @job
    def test_job():
        multiply_three_by_four()

    result = test_job.execute_in_process()

    assert result.success
    assert result.output_for_node("multiply_three_by_four") == 12


def test_single_level_job_with_configured_decorated_graph():
    @op(config_schema={"inner": int})
    def multiply_by_two(context):
        return context.op_config["inner"] * 2

    @op
    def add(_context, lhs, rhs):
        return lhs + rhs

    @graph(
        config=ConfigMapping(
            config_schema={"outer": int},
            config_fn=lambda c: {
                "multiply_by_two": {"config": {"inner": c["outer"]}},
                "multiply_by_two_again": {"config": {"inner": c["outer"]}},
            },
        )
    )
    def multiply_by_four():
        return add(multiply_by_two(), multiply_by_two.alias("multiply_by_two_again")())

    @configured(
        multiply_by_four, config_schema={}
    )  # test that with config_schema={} we can omit config
    def multiply_three_by_four(_config):
        return {"outer": 3}

    assert multiply_three_by_four.name == "multiply_three_by_four"

    @job
    def test_job():
        multiply_three_by_four()

    result = test_job.execute_in_process()

    assert result.success
    assert result.output_for_node("multiply_three_by_four") == 12


def test_configured_graph_with_inputs():
    @op(config_schema=str, ins={"x": In(int)})
    def return_int(context, x):
        assert context.op_config == "inner config sentinel"
        return x

    return_int_x = configured(return_int, name="return_int_x")("inner config sentinel")

    @op(config_schema=str)
    def add(context, lhs, rhs):
        assert context.op_config == "outer config sentinel"
        return lhs + rhs

    @graph(
        ins={"x": GraphIn(), "y": GraphIn()},
        config=ConfigMapping(
            config_schema={"outer": str},
            config_fn=lambda cfg: {"add": {"config": cfg["outer"]}},
        ),
    )
    def return_int_graph(x, y):
        return add(return_int_x(x), return_int_x.alias("return_int_again")(y))

    return_int_composite_x = configured(return_int_graph, name="return_int_graph")(
        {"outer": "outer config sentinel"}
    )

    @job
    def test_job():
        return_int_composite_x()

    result = test_job.execute_in_process(
        {"ops": {"return_int_graph": {"inputs": {"x": 6, "y": 4}}}},
    )

    assert result.success
    assert result.output_for_node("return_int_graph") == 10


def test_configured_graph_cannot_stub_inner_ops_config():
    @op(config_schema=int)
    def return_int(context, x):
        return context.op_config + x

    @graph(
        config=ConfigMapping(
            config_schema={"num": int},
            config_fn=lambda config: {"return_int": {"config": config["num"]}},
        )
    )
    def return_int_graph():
        return return_int()

    @job
    def return_int_job():
        return_int_graph()

    with pytest.raises(
        DagsterInvalidConfigError,
        match='Received unexpected config entry "ops" at path root:ops:return_int_graph.',
    ):
        return_int_job.execute_in_process(
            {
                "ops": {
                    "return_int_graph": {
                        "config": {"num": 4},
                        "ops": {"return_int": {"config": 3, "inputs": {"x": 1}}},
                    }
                }
            },
        )


def test_configuring_graph_with_no_config_mapping():
    @op
    def return_run_id(context):
        return context.run_id

    @graph
    def graph_without_config_fn():
        return return_run_id()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "Only graphs utilizing config mapping can be pre-configured. The graph "
            '"graph_without_config_fn"'
        ),
    ):
        configured(graph_without_config_fn, name="configured_composite")({})
