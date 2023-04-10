# type: ignore

# Turn pyright off due to problems with putting Dagster types in type annotations.
# See: https://github.com/dagster-io/dagster/issues/4209

import os
import pickle
import tempfile
import time

import pytest
from dagster import (
    Any,
    Bool,
    DagsterInvalidConfigError,
    Dict,
    Field,
    Float,
    In,
    Int,
    List,
    Nothing,
    Optional,
    Permissive,
    Selector,
    Set,
    String,
    Tuple,
    _check as check,
    job,
    op,
)
from dagster._utils.test import wrap_op_in_graph_and_execute


@op
def identity(_, x: Any) -> Any:
    return x


@op
def identity_imp(_, x):
    return x


@op
def boolean(_, x: Bool) -> String:
    return "true" if x else "false"


@op
def empty_string(_, x: String) -> bool:
    return len(x) == 0


@op
def add_3(_, x: Int) -> int:
    return x + 3


@op
def div_2(_, x: Float) -> float:
    return x / 2


@op
def concat(_, x: String, y: str) -> str:
    return x + y


@op
def wait(_) -> Nothing:
    time.sleep(0.2)
    return None


@op(ins={"ready": In(Nothing)})
def done(_) -> str:
    return "done"


@job
def nothing_job():
    done(wait())


@op
def wait_int(_) -> Int:
    time.sleep(0.2)
    return 1


@job
def nothing_int_job():
    done(wait_int())


@op
def nullable_concat(_, x: String, y: Optional[String]) -> String:
    return x + (y or "")


@op
def concat_list(_, xs: List[String]) -> String:
    return "".join(xs)


@op
def emit_1(_) -> int:
    return 1


@op
def emit_2(_) -> int:
    return 2


@op
def emit_3(_) -> int:
    return 3


@op
def sum_op(_, xs: List[int]) -> int:
    return sum(xs)


@job
def sum_job():
    sum_op([emit_1(), emit_2(), emit_3()])


@op
def repeat(_, spec: Dict) -> str:
    return spec["word"] * spec["times"]


@op
def set_op(_, set_input: Set[String]) -> List[String]:
    return sorted([x for x in set_input])


@op
def tuple_op(_, tuple_input: Tuple[String, Int, Float]) -> List:
    return [x for x in tuple_input]


@op
def dict_return_op(_) -> Dict[str, str]:
    return {"foo": "bar"}


def test_identity():
    res = wrap_op_in_graph_and_execute(identity, input_values={"x": "foo"})
    assert res.output_value() == "foo"


def test_identity_imp():
    res = wrap_op_in_graph_and_execute(identity_imp, input_values={"x": "foo"})
    assert res.output_value() == "foo"


def test_boolean():
    res = wrap_op_in_graph_and_execute(boolean, input_values={"x": True})
    assert res.output_value() == "true"

    res = wrap_op_in_graph_and_execute(boolean, input_values={"x": False})
    assert res.output_value() == "false"


def test_empty_string():
    res = wrap_op_in_graph_and_execute(empty_string, input_values={"x": ""})
    assert res.output_value() is True

    res = wrap_op_in_graph_and_execute(empty_string, input_values={"x": "foo"})
    assert res.output_value() is False


def test_add_3():
    res = wrap_op_in_graph_and_execute(add_3, input_values={"x": 3})
    assert res.output_value() == 6


def test_div_2():
    res = wrap_op_in_graph_and_execute(div_2, input_values={"x": 7.0})
    assert res.output_value() == 3.5


def test_concat():
    res = wrap_op_in_graph_and_execute(concat, input_values={"x": "foo", "y": "bar"})
    assert res.output_value() == "foobar"


def test_nothing_job():
    res = nothing_job.execute_in_process()
    assert res.output_for_node("wait") is None
    assert res.output_for_node("done") == "done"


def test_nothing_int_job():
    res = nothing_int_job.execute_in_process()
    assert res.output_for_node("wait_int") == 1
    assert res.output_for_node("done") == "done"


def test_nullable_concat():
    res = wrap_op_in_graph_and_execute(nullable_concat, input_values={"x": "foo", "y": None})
    assert res.output_value() == "foo"


def test_concat_list():
    res = wrap_op_in_graph_and_execute(concat_list, input_values={"xs": ["foo", "bar", "baz"]})
    assert res.output_value() == "foobarbaz"


def test_sum_job():
    res = sum_job.execute_in_process()
    assert res.output_for_node("sum_op") == 6


def test_repeat():
    res = wrap_op_in_graph_and_execute(repeat, input_values={"spec": {"word": "foo", "times": 3}})
    assert res.output_value() == "foofoofoo"


def test_set_op():
    res = wrap_op_in_graph_and_execute(set_op, input_values={"set_input": {"foo", "bar", "baz"}})
    assert res.output_value() == sorted(["foo", "bar", "baz"])


def test_set_op_configable_input():
    res = wrap_op_in_graph_and_execute(
        set_op,
        run_config={
            "ops": {
                "set_op": {
                    "inputs": {
                        "set_input": [
                            {"value": "foo"},
                            {"value": "bar"},
                            {"value": "baz"},
                        ]
                    }
                }
            }
        },
        do_input_mapping=False,
    )
    assert res.output_value() == sorted(["foo", "bar", "baz"])


def test_set_op_configable_input_bad():
    with pytest.raises(
        DagsterInvalidConfigError,
    ) as exc_info:
        wrap_op_in_graph_and_execute(
            set_op,
            run_config={"ops": {"set_op": {"inputs": {"set_input": {"foo", "bar", "baz"}}}}},
            do_input_mapping=False,
        )

    expected = "Value at path root:ops:set_op:inputs:set_input must be list."

    assert expected in str(exc_info.value)


def test_tuple_op():
    res = wrap_op_in_graph_and_execute(tuple_op, input_values={"tuple_input": ("foo", 1, 3.1)})
    assert res.output_value() == ["foo", 1, 3.1]


def test_tuple_op_configable_input():
    res = wrap_op_in_graph_and_execute(
        tuple_op,
        run_config={
            "ops": {
                "tuple_op": {
                    "inputs": {"tuple_input": [{"value": "foo"}, {"value": 1}, {"value": 3.1}]}
                }
            }
        },
        do_input_mapping=False,
    )
    assert res.output_value() == ["foo", 1, 3.1]


def test_dict_return_op():
    res = wrap_op_in_graph_and_execute(dict_return_op)
    assert res.output_value() == {"foo": "bar"}


######


@op(config_schema=Field(Any))
def any_config(context):
    return context.op_config


@op(config_schema=Field(Bool))
def bool_config(context):
    return "true" if context.op_config else "false"


@op(config_schema=Int)
def add_n(context, x: Int) -> int:
    return x + context.op_config


@op(config_schema=Field(Float))
def div_y(context, x: Float) -> float:
    return x / context.op_config


@op(config_schema=Field(float))
def div_y_var(context, x: Float) -> float:
    return x / context.op_config


@op(config_schema=Field(String))
def hello(context) -> str:
    return f"Hello, {context.op_config}!"


@op(config_schema=Field(String))
def unpickle(context) -> Any:
    with open(context.op_config, "rb") as fd:
        return pickle.load(fd)


@op(config_schema=Field(list))
def concat_typeless_list_config(context) -> String:
    return "".join(context.op_config)


@op(config_schema=Field([str]))
def concat_config(context) -> String:
    return "".join(context.op_config)


@op(config_schema={"word": String, "times": Int})
def repeat_config(context) -> str:
    return context.op_config["word"] * context.op_config["times"]


@op(config_schema=Field(Selector({"haw": {}, "cn": {}, "en": {}})))
def hello_world(context) -> str:
    if "haw" in context.op_config:
        return "Aloha honua!"
    if "cn" in context.op_config:
        return "你好,世界!"
    return "Hello, world!"


@op(
    config_schema=Field(
        Selector(
            {
                "haw": {"whom": Field(String, default_value="honua", is_required=False)},
                "cn": {"whom": Field(String, default_value="世界", is_required=False)},
                "en": {"whom": Field(String, default_value="world", is_required=False)},
            }
        ),
        is_required=False,
        default_value={"en": {"whom": "world"}},
    )
)
def hello_world_default(context) -> str:
    if "haw" in context.op_config:
        return "Aloha {whom}!".format(whom=context.op_config["haw"]["whom"])
    if "cn" in context.op_config:
        return "你好,{whom}!".format(whom=context.op_config["cn"]["whom"])
    if "en" in context.op_config:
        return "Hello, {whom}!".format(whom=context.op_config["en"]["whom"])
    assert False, "invalid op_config"


@op(config_schema=Field(Permissive({"required": Field(String)})))
def partially_specified_config(context) -> List:
    return sorted(list(context.op_config.items()))


def test_any_config():
    res = wrap_op_in_graph_and_execute(
        any_config, run_config={"ops": {"any_config": {"config": "foo"}}}
    )
    assert res.output_value() == "foo"

    res = wrap_op_in_graph_and_execute(
        any_config, run_config={"ops": {"any_config": {"config": {"zip": "zowie"}}}}
    )
    assert res.output_value() == {"zip": "zowie"}


def test_bool_config():
    res = wrap_op_in_graph_and_execute(
        bool_config, run_config={"ops": {"bool_config": {"config": True}}}
    )
    assert res.output_value() == "true"

    res = wrap_op_in_graph_and_execute(
        bool_config, run_config={"ops": {"bool_config": {"config": False}}}
    )
    assert res.output_value() == "false"


def test_add_n():
    res = wrap_op_in_graph_and_execute(
        add_n, input_values={"x": 3}, run_config={"ops": {"add_n": {"config": 7}}}
    )
    assert res.output_value() == 10


def test_div_y():
    res = wrap_op_in_graph_and_execute(
        div_y,
        input_values={"x": 3.0},
        run_config={"ops": {"div_y": {"config": 2.0}}},
    )
    assert res.output_value() == 1.5


def test_div_y_var():
    res = wrap_op_in_graph_and_execute(
        div_y_var,
        input_values={"x": 3.0},
        run_config={"ops": {"div_y_var": {"config": 2.0}}},
    )
    assert res.output_value() == 1.5


def test_hello():
    res = wrap_op_in_graph_and_execute(hello, run_config={"ops": {"hello": {"config": "Max"}}})
    assert res.output_value() == "Hello, Max!"


def test_unpickle():
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = os.path.join(tmpdir, "foo.pickle")
        with open(filename, "wb") as f:
            pickle.dump("foo", f)
        res = wrap_op_in_graph_and_execute(
            unpickle, run_config={"ops": {"unpickle": {"config": filename}}}
        )
        assert res.output_value() == "foo"


def test_concat_config():
    res = wrap_op_in_graph_and_execute(
        concat_config,
        run_config={"ops": {"concat_config": {"config": ["foo", "bar", "baz"]}}},
    )
    assert res.output_value() == "foobarbaz"


def test_concat_typeless_config():
    res = wrap_op_in_graph_and_execute(
        concat_typeless_list_config,
        run_config={"ops": {"concat_typeless_list_config": {"config": ["foo", "bar", "baz"]}}},
    )
    assert res.output_value() == "foobarbaz"


def test_repeat_config():
    res = wrap_op_in_graph_and_execute(
        repeat_config,
        run_config={"ops": {"repeat_config": {"config": {"word": "foo", "times": 3}}}},
    )
    assert res.output_value() == "foofoofoo"


def test_tuple_none_config():
    with pytest.raises(check.CheckError, match="Param tuple_types cannot be none"):

        @op(config_schema=Field(Tuple[None]))
        def _tuple_none_config(context) -> str:
            return ":".join([str(x) for x in context.op_config])


def test_selector_config():
    res = wrap_op_in_graph_and_execute(
        hello_world, run_config={"ops": {"hello_world": {"config": {"haw": {}}}}}
    )
    assert res.output_value() == "Aloha honua!"


def test_selector_config_default():
    res = wrap_op_in_graph_and_execute(hello_world_default)
    assert res.output_value() == "Hello, world!"

    res = wrap_op_in_graph_and_execute(
        hello_world_default,
        run_config={"ops": {"hello_world_default": {"config": {"haw": {}}}}},
    )
    assert res.output_value() == "Aloha honua!"

    res = wrap_op_in_graph_and_execute(
        hello_world_default,
        run_config={"ops": {"hello_world_default": {"config": {"haw": {"whom": "Max"}}}}},
    )
    assert res.output_value() == "Aloha Max!"


def test_permissive_config():
    res = wrap_op_in_graph_and_execute(
        partially_specified_config,
        run_config={
            "ops": {"partially_specified_config": {"config": {"required": "yes", "also": "this"}}}
        },
    )
    assert res.output_value() == sorted([("required", "yes"), ("also", "this")])
