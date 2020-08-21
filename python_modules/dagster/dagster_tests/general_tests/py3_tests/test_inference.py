from typing import Any, Dict, List, Optional, Tuple

from dagster import (
    InputDefinition,
    Int,
    composite_solid,
    execute_solid,
    lambda_solid,
    solid,
    usable_as_dagster_type,
)
from dagster.core.definitions import inference
from dagster.core.types.dagster_type import DagsterTypeKind


def test_single_typed_input():
    @solid
    def add_one_infer(_context, num: int):
        return num + 1

    @solid(input_defs=[InputDefinition("num", Int)])
    def add_one_ex(_context, num):
        return num + 1

    assert len(add_one_infer.input_defs) == 1

    assert add_one_ex.input_defs[0].name == add_one_infer.input_defs[0].name
    assert (
        add_one_ex.input_defs[0].dagster_type.name == add_one_infer.input_defs[0].dagster_type.name
    )


def test_precedence():
    @solid(input_defs=[InputDefinition("num", Int)])
    def add_one(_context, num: Any):
        return num + 1

    assert add_one.input_defs[0].dagster_type.name == "Int"


def test_double_typed_input():
    @solid
    def subtract(_context, num_one: int, num_two: int):
        return num_one + num_two

    assert subtract
    assert len(subtract.input_defs) == 2
    assert subtract.input_defs[0].name == "num_one"
    assert subtract.input_defs[0].dagster_type.name == "Int"

    assert subtract.input_defs[1].name == "num_two"
    assert subtract.input_defs[1].dagster_type.name == "Int"


def test_one_arg_typed_lambda_solid():
    @lambda_solid
    def one_arg(num: int):
        return num

    assert one_arg
    assert len(one_arg.input_defs) == 1
    assert one_arg.input_defs[0].name == "num"
    assert one_arg.input_defs[0].dagster_type.name == "Int"
    assert len(one_arg.output_defs) == 1


def test_single_typed_input_and_output():
    @solid
    def add_one(_context, num: int) -> int:
        return num + 1

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == "num"
    assert add_one.input_defs[0].dagster_type.name == "Int"

    assert len(add_one.output_defs) == 1
    assert add_one.output_defs[0].dagster_type.name == "Int"


def test_single_typed_input_and_output_lambda():
    @lambda_solid
    def add_one(num: int) -> int:
        return num + 1

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == "num"
    assert add_one.input_defs[0].dagster_type.name == "Int"

    assert len(add_one.output_defs) == 1
    assert add_one.output_defs[0].dagster_type.name == "Int"


def test_wrapped_input_and_output_lambda():
    @lambda_solid
    def add_one(nums: List[int]) -> Optional[List[int]]:
        return [num + 1 for num in nums]

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == "nums"
    assert add_one.input_defs[0].dagster_type.kind == DagsterTypeKind.LIST
    assert add_one.input_defs[0].dagster_type.inner_type.name == "Int"

    assert len(add_one.output_defs) == 1
    assert add_one.output_defs[0].dagster_type.kind == DagsterTypeKind.NULLABLE
    assert add_one.output_defs[0].dagster_type.inner_type.kind == DagsterTypeKind.LIST


def test_kitchen_sink():
    @usable_as_dagster_type
    class Custom(object):
        pass

    @lambda_solid
    def sink(
        n: int, f: float, b: bool, s: str, x: Any, o: Optional[str], l: List[str], c: Custom
    ):  # pylint: disable=unused-argument
        pass

    assert sink.input_defs[0].name == "n"
    assert sink.input_defs[0].dagster_type.name == "Int"

    assert sink.input_defs[1].name == "f"
    assert sink.input_defs[1].dagster_type.name == "Float"

    assert sink.input_defs[2].name == "b"
    assert sink.input_defs[2].dagster_type.name == "Bool"

    assert sink.input_defs[3].name == "s"
    assert sink.input_defs[3].dagster_type.name == "String"

    assert sink.input_defs[4].name == "x"
    assert sink.input_defs[4].dagster_type.name == "Any"

    assert sink.input_defs[5].name == "o"
    assert sink.input_defs[5].dagster_type.kind == DagsterTypeKind.NULLABLE

    assert sink.input_defs[6].name == "l"
    assert sink.input_defs[6].dagster_type.kind == DagsterTypeKind.LIST

    assert sink.input_defs[7].name == "c"
    assert sink.input_defs[7].dagster_type.name == "Custom"


def test_composites():
    @lambda_solid
    def emit_one() -> int:
        return 1

    @lambda_solid
    def subtract(n1: int, n2: int) -> int:
        return n1 - n2

    @composite_solid
    def add_one(a: int) -> int:
        return subtract(a, emit_one())

    assert add_one.input_mappings


def test_emit_dict():
    @lambda_solid
    def emit_dict() -> dict:
        return {"foo": "bar"}

    solid_result = execute_solid(emit_dict)

    assert solid_result.output_value() == {"foo": "bar"}


def test_dict_input():
    @lambda_solid
    def intake_dict(inp: dict) -> str:
        return inp["foo"]

    solid_result = execute_solid(intake_dict, input_values={"inp": {"foo": "bar"}})
    assert solid_result.output_value() == "bar"


def test_emit_dagster_dict():
    @lambda_solid
    def emit_dagster_dict() -> Dict:
        return {"foo": "bar"}

    solid_result = execute_solid(emit_dagster_dict)

    assert solid_result.output_value() == {"foo": "bar"}


def test_dict_dagster_input():
    @lambda_solid
    def intake_dagster_dict(inp: Dict) -> str:
        return inp["foo"]

    solid_result = execute_solid(intake_dagster_dict, input_values={"inp": {"foo": "bar"}})
    assert solid_result.output_value() == "bar"


def test_python_tuple_input():
    @lambda_solid
    def intake_tuple(inp: tuple) -> int:
        return inp[1]

    assert execute_solid(intake_tuple, input_values={"inp": (3, 4)}).output_value() == 4


def test_python_tuple_output():
    @lambda_solid
    def emit_tuple() -> tuple:
        return (4, 5)

    assert execute_solid(emit_tuple).output_value() == (4, 5)


def test_nested_kitchen_sink():
    @lambda_solid
    def no_execute() -> Optional[List[Tuple[List[int], str, Dict[str, Optional[List[str]]]]]]:
        pass

    assert (
        no_execute.output_defs[0].dagster_type.display_name
        == "[Tuple[[Int],String,Dict[String,[String]?]]]?"
    )


def test_infer_input_description_from_docstring_rest():
    @solid
    def rest(_context, hello: str, optional: int = 5):
        """
        :param str hello: hello world param
        :param int optional: optional param, defaults to 5
        """
        return hello + str(optional)

    defs = inference.infer_input_definitions_for_solid(rest.name, rest.compute_fn)
    assert len(defs) == 2

    hello_param = defs[0]
    assert hello_param.name == "hello"
    assert hello_param.dagster_type.name == "String"

    optional_param = defs[1]
    assert optional_param.name == "optional"
    assert optional_param.dagster_type.name == "Int"
    assert optional_param.default_value == 5


def test_infer_descriptions_from_docstring_numpy():
    @solid
    def good_numpy(_context, hello: str, optional: int = 5):
        """
        Test

        Parameters
        ----------
        hello:
            hello world param
        optional:
            optional param, default 5
        """
        return hello + str(optional)

    defs = inference.infer_input_definitions_for_solid(good_numpy.name, good_numpy.compute_fn)
    assert len(defs) == 2

    hello_param = defs[0]
    assert hello_param.name == "hello"
    assert hello_param.dagster_type.name == "String"
    assert hello_param.description == "hello world param"

    optional_param = defs[1]
    assert optional_param.name == "optional"
    assert optional_param.dagster_type.name == "Int"
    assert optional_param.default_value == 5
    assert optional_param.description == "optional param, default 5"


def test_infer_descriptions_from_docstring_google():
    @solid
    def good_google(_context, hello: str, optional: int = 5):
        """
        Test

        Args:
            hello       (str): hello world param
            optional    (int, optional): optional param. Defaults to 5.
        """
        return hello + str(optional)

    defs = inference.infer_input_definitions_for_solid(good_google.name, good_google.compute_fn)
    assert len(defs) == 2

    hello_param = defs[0]
    assert hello_param.name == "hello"
    assert hello_param.dagster_type.name == "String"
    assert hello_param.description == "hello world param"

    optional_param = defs[1]
    assert optional_param.name == "optional"
    assert optional_param.dagster_type.name == "Int"
    assert optional_param.default_value == 5
    assert optional_param.description == "optional param. Defaults to 5."


def test_infer_output_description_from_docstring_numpy():
    @solid
    def numpy(_context) -> int:
        """

        Returns
        -------
        int
            a number
        """

    defs = inference.infer_output_definitions("@solid", numpy.name, numpy.compute_fn)
    assert len(defs) == 1
    assert defs[0].name == "result"
    assert defs[0].description == "a number"
    assert defs[0].dagster_type.name == "Int"


def test_infer_output_description_from_docstring_rest():
    @solid
    def rest(_context) -> int:
        """
        :return int: a number
        """

    defs = inference.infer_output_definitions("@solid", rest.name, rest.compute_fn)
    assert len(defs) == 1
    assert defs[0].description == "a number"
    assert defs[0].dagster_type.name == "Int"


def test_infer_output_description_from_docstring_google():
    @solid
    def google(_context) -> int:
        """
        Returns:
            int: a number
        """

    defs = inference.infer_output_definitions("@solid", google.name, google.compute_fn)
    assert len(defs) == 1
    assert defs[0].description == "a number"
    assert defs[0].dagster_type.name == "Int"
