# ruff: noqa: D416

from typing import Any, Dict, List, Optional, Tuple

import pytest
from dagster import (
    DagsterInvalidDefinitionError,
    DagsterType,
    In,
    Int,
    make_python_type_usable_as_dagster_type,
    op,
    usable_as_dagster_type,
)
from dagster._core.definitions.decorators.graph_decorator import graph
from dagster._core.definitions.inference import infer_input_props, infer_output_props
from dagster._core.types.dagster_type import DagsterTypeKind
from dagster._legacy import execute_pipeline, execute_solid, pipeline


def test_infer_solid_description_from_docstring():
    @op
    def my_solid(_):
        """Here is some docstring."""

    assert my_solid.description == "Here is some docstring."


def test_infer_solid_description_no_docstring():
    @op
    def my_solid(_):
        pass

    assert my_solid.description is None


def test_docstring_does_not_override():
    @op(description="abc")
    def my_solid(_):
        """Here is some docstring."""

    assert my_solid.description == "abc"


def test_single_typed_input():
    @op
    def add_one_infer(_context, num: int):
        return num + 1

    @op(ins={"num": In(Int)})
    def add_one_ex(_context, num):
        return num + 1

    assert len(add_one_infer.input_defs) == 1

    assert add_one_ex.input_defs[0].name == add_one_infer.input_defs[0].name
    assert (
        add_one_ex.input_defs[0].dagster_type.unique_name
        == add_one_infer.input_defs[0].dagster_type.unique_name
    )


def test_precedence():
    @op(ins={"num": In(Int)})
    def add_one(_context, num: Any):
        return num + 1

    assert add_one.input_defs[0].dagster_type.unique_name == "Int"


def test_double_typed_input():
    @op
    def subtract(_context, num_one: int, num_two: int):
        return num_one + num_two

    assert subtract
    assert len(subtract.input_defs) == 2
    assert subtract.input_defs[0].name == "num_one"
    assert subtract.input_defs[0].dagster_type.unique_name == "Int"

    assert subtract.input_defs[1].name == "num_two"
    assert subtract.input_defs[1].dagster_type.unique_name == "Int"


def test_single_typed_input_and_output():
    @op
    def add_one(_context, num: int) -> int:
        return num + 1

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == "num"
    assert add_one.input_defs[0].dagster_type.unique_name == "Int"

    assert len(add_one.output_defs) == 1
    assert add_one.output_defs[0].dagster_type.unique_name == "Int"


def test_single_typed_input_and_output_lambda():
    @op
    def add_one(num: int) -> int:
        return num + 1

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == "num"
    assert add_one.input_defs[0].dagster_type.unique_name == "Int"

    assert len(add_one.output_defs) == 1
    assert add_one.output_defs[0].dagster_type.unique_name == "Int"


def test_wrapped_input_and_output_lambda():
    @op
    def add_one(nums: List[int]) -> Optional[List[int]]:
        return [num + 1 for num in nums]

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == "nums"
    assert add_one.input_defs[0].dagster_type.kind == DagsterTypeKind.LIST
    assert add_one.input_defs[0].dagster_type.inner_type.unique_name == "Int"

    assert len(add_one.output_defs) == 1
    assert add_one.output_defs[0].dagster_type.kind == DagsterTypeKind.NULLABLE
    assert add_one.output_defs[0].dagster_type.inner_type.kind == DagsterTypeKind.LIST


def test_kitchen_sink():
    @usable_as_dagster_type
    class Custom:
        pass

    @op
    def sink(
        n: int,
        f: float,
        b: bool,
        s: str,
        x: Any,
        o: Optional[str],
        m: List[str],
        c: Custom,
    ):  # pylint: disable=unused-argument
        pass

    assert sink.input_defs[0].name == "n"
    assert sink.input_defs[0].dagster_type.unique_name == "Int"

    assert sink.input_defs[1].name == "f"
    assert sink.input_defs[1].dagster_type.unique_name == "Float"

    assert sink.input_defs[2].name == "b"
    assert sink.input_defs[2].dagster_type.unique_name == "Bool"

    assert sink.input_defs[3].name == "s"
    assert sink.input_defs[3].dagster_type.unique_name == "String"

    assert sink.input_defs[4].name == "x"
    assert sink.input_defs[4].dagster_type.unique_name == "Any"

    assert sink.input_defs[5].name == "o"
    assert sink.input_defs[5].dagster_type.kind == DagsterTypeKind.NULLABLE

    assert sink.input_defs[6].name == "m"
    assert sink.input_defs[6].dagster_type.kind == DagsterTypeKind.LIST

    assert sink.input_defs[7].name == "c"
    assert sink.input_defs[7].dagster_type.unique_name == "Custom"


def test_composites():
    @op
    def emit_one() -> int:
        return 1

    @op
    def subtract(n1: int, n2: int) -> int:
        return n1 - n2

    @graph
    def add_one(a: int) -> int:
        return subtract(a, emit_one())

    assert add_one.input_mappings


def test_emit_dict():
    @op
    def emit_dict() -> dict:
        return {"foo": "bar"}

    solid_result = execute_solid(emit_dict)

    assert solid_result.output_value() == {"foo": "bar"}


def test_dict_input():
    @op
    def intake_dict(inp: dict) -> str:
        return inp["foo"]

    solid_result = execute_solid(intake_dict, input_values={"inp": {"foo": "bar"}})
    assert solid_result.output_value() == "bar"


def test_emit_dagster_dict():
    @op
    def emit_dagster_dict() -> Dict:
        return {"foo": "bar"}

    solid_result = execute_solid(emit_dagster_dict)

    assert solid_result.output_value() == {"foo": "bar"}


def test_dict_dagster_input():
    @op
    def intake_dagster_dict(inp: Dict) -> str:
        return inp["foo"]

    solid_result = execute_solid(intake_dagster_dict, input_values={"inp": {"foo": "bar"}})
    assert solid_result.output_value() == "bar"


def test_python_tuple_input():
    @op
    def intake_tuple(inp: tuple) -> int:
        return inp[1]

    assert execute_solid(intake_tuple, input_values={"inp": (3, 4)}).output_value() == 4


def test_python_tuple_output():
    @op
    def emit_tuple() -> tuple:
        return (4, 5)

    assert execute_solid(emit_tuple).output_value() == (4, 5)


def test_nested_kitchen_sink():
    @op
    def no_execute() -> Optional[List[Tuple[List[int], str, Dict[str, Optional[List[str]]]]]]:
        pass

    assert (
        no_execute.output_defs[0].dagster_type.display_name
        == "[Tuple[[Int],String,Dict[String,[String]?]]]?"
    )

    assert (
        no_execute.output_defs[0].dagster_type.typing_type
        == Optional[List[Tuple[List[int], str, Dict[str, Optional[List[str]]]]]]
    )


def test_infer_input_description_from_docstring_failure():
    # docstring is invalid because has a dash instead of a colon to delimit the argument type and
    # description
    @op
    def my_solid(_arg1):
        """
        Args:
            _arg1 - description of arg.
        """

    assert my_solid


def test_infer_input_description_from_docstring_rest():
    @op
    def rest(_context, hello: str, optional: int = 5):
        """
        :param str hello: hello world param
        :param int optional: optional param, defaults to 5.
        """
        return hello + str(optional)

    defs = infer_input_props(rest.compute_fn.decorated_fn, context_arg_provided=True)
    assert len(defs) == 2

    hello_param = defs[0]
    assert hello_param.name == "hello"
    assert hello_param.annotation == str

    optional_param = defs[1]
    assert optional_param.name == "optional"
    assert optional_param.annotation == int
    assert optional_param.default_value == 5


def test_infer_descriptions_from_docstring_numpy():
    @op
    def good_numpy(_context, hello: str, optional: int = 5):
        """
        Test.

        Parameters
        ----------
        hello:
            hello world param
        optional:
            optional param, default 5
        """
        return hello + str(optional)

    defs = infer_input_props(good_numpy.compute_fn.decorated_fn, context_arg_provided=True)
    assert len(defs) == 2

    hello_param = defs[0]
    assert hello_param.name == "hello"
    assert hello_param.annotation == str
    assert hello_param.description == "hello world param"

    optional_param = defs[1]
    assert optional_param.name == "optional"
    assert optional_param.annotation == int
    assert optional_param.default_value == 5
    assert optional_param.description == "optional param, default 5"


def test_infer_descriptions_from_docstring_google():
    @op
    def good_google(_context, hello: str, optional: int = 5):
        """
        Test.

        Args:
            hello       (str): hello world param
            optional    (int, optional): optional param. Defaults to 5.
        """
        return hello + str(optional)

    defs = infer_input_props(good_google.compute_fn.decorated_fn, context_arg_provided=True)
    assert len(defs) == 2

    hello_param = defs[0]
    assert hello_param.name == "hello"
    assert hello_param.annotation == str
    assert hello_param.description == "hello world param"

    optional_param = defs[1]
    assert optional_param.name == "optional"
    assert optional_param.annotation == int
    assert optional_param.default_value == 5
    assert optional_param.description == "optional param. Defaults to 5."


def test_infer_output_description_from_docstring_failure():
    # docstring is invalid because has a dash instead of a colon to delimit the return type and
    # description
    @op
    def google() -> int:
        """
        Returns:
            int - a number.
        """
        return 1

    assert google


def test_infer_output_description_from_docstring_numpy():
    @op
    def numpy(_context) -> int:
        """

        Returns
        -------
        int
            a number.
        """
        return 1

    props = infer_output_props(numpy.compute_fn.decorated_fn)
    assert props.description == "a number."
    assert props.annotation == int


def test_infer_output_description_from_docstring_rest():
    @op
    def rest(_context) -> int:
        """
        :return int: a number.
        """
        return 1

    props = infer_output_props(rest.compute_fn.decorated_fn)
    assert props.description == "a number."
    assert props.annotation == int


def test_infer_output_description_from_docstring_google():
    @op
    def google(_context) -> int:
        """
        Returns:
            int: a number.
        """
        return 1

    props = infer_output_props(google.compute_fn.decorated_fn)

    assert props.description == "a number."
    assert props.annotation == int


def test_pipeline_api_stability():
    @pipeline
    def empty() -> None:
        pass

    # assert definition does not error
    assert empty


def test_unregistered_type_annotation_output():
    class MyClass:
        pass

    @op
    def my_solid(_) -> MyClass:
        return MyClass()

    assert my_solid.output_defs[0].dagster_type.display_name == "MyClass"
    assert my_solid.output_defs[0].dagster_type.typing_type == MyClass

    @pipeline
    def my_pipeline():
        my_solid()

    execute_pipeline(my_pipeline)


def test_unregistered_type_annotation_input():
    class MyClass:
        pass

    @op
    def solid1(_):
        return MyClass()

    @op
    def solid2(_, _input1: MyClass):
        pass

    @pipeline
    def my_pipeline():
        solid2(solid1())

    assert solid2.input_defs[0].dagster_type.display_name == "MyClass"
    execute_pipeline(my_pipeline)


def test_unregistered_type_annotation_input_op():
    class MyClass:
        pass

    @op
    def op2(_, _input1: MyClass):
        pass

    assert op2.input_defs[0].dagster_type.display_name == "MyClass"


def test_unregistered_type_annotation_input_op_merge():
    class MyClass:
        pass

    @op(ins={"_input1": In()})
    def op2(_input1: MyClass):
        pass

    assert op2.input_defs[0].dagster_type.display_name == "MyClass"


def test_use_auto_type_twice():
    class MyClass:
        pass

    @op
    def my_solid(_) -> MyClass:
        return MyClass()

    @op
    def my_solid_2(_) -> MyClass:
        return MyClass()

    @pipeline
    def my_pipeline():
        my_solid()
        my_solid_2()

    execute_pipeline(my_pipeline)


def test_register_after_solid_definition():
    class MyClass:
        pass

    @op
    def _my_solid(_) -> MyClass:
        return MyClass()

    my_dagster_type = DagsterType(name="aaaa", type_check_fn=lambda _, _a: True)

    with pytest.raises(DagsterInvalidDefinitionError):
        make_python_type_usable_as_dagster_type(MyClass, my_dagster_type)


def test_same_name_different_modules():
    class MyClass:
        pass

    from dagster_tests.general_tests.py3_tests.other_module import MyClass as OtherModuleMyClass

    @op
    def my_solid(_) -> MyClass:
        return MyClass()

    @op
    def my_solid_2(_) -> OtherModuleMyClass:
        return OtherModuleMyClass()

    @pipeline
    def my_pipeline():
        my_solid()
        my_solid_2()

    execute_pipeline(my_pipeline)


def test_fan_in():
    class MyClass:
        pass

    @op
    def upstream_solid(_):
        return MyClass()

    @op
    def downstream_solid(_, _input: List[MyClass]):
        pass

    @pipeline
    def my_pipeline():
        downstream_solid([upstream_solid.alias("a")(), upstream_solid.alias("b")()])

    assert downstream_solid.input_defs[0].dagster_type.display_name == "[MyClass]"
    assert downstream_solid.input_defs[0].dagster_type.typing_type == List[MyClass]

    execute_pipeline(my_pipeline)


def test_composites_user_defined_type():
    class MyClass:
        pass

    @op
    def emit_one() -> MyClass:
        return MyClass()

    @op
    def subtract(_n1: MyClass, _n2: MyClass) -> MyClass:
        return MyClass()

    @graph
    def add_one(a: MyClass) -> MyClass:
        return subtract(a, emit_one())

    assert add_one.input_mappings
