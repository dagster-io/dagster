import sys
import unittest

import pytest

from dagster import lambda_solid, solid
from dagster.core.definitions import inference
from dagster.core.errors import DagsterInvalidDefinitionError


def test_single_input():
    @solid
    def add_one(_context, num):
        return num + 1

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == 'num'
    assert add_one.input_defs[0].dagster_type.name == 'Any'


def test_double_input():
    @solid
    def subtract(_context, num_one, num_two):
        return num_one + num_two

    assert subtract
    assert len(subtract.input_defs) == 2
    assert subtract.input_defs[0].name == 'num_one'
    assert subtract.input_defs[0].dagster_type.name == 'Any'

    assert subtract.input_defs[1].name == 'num_two'
    assert subtract.input_defs[1].dagster_type.name == 'Any'


def test_solid_arg_fails():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Solid functions should only have keyword arguments that match input names and a first positional parameter named 'context'",
    ):

        @solid
        def _other_fails(_other):
            pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Solid functions should only have keyword arguments that match input names and a first positional parameter named 'context'",
    ):

        @solid
        def _empty_fails():
            pass


def test_noop_lambda_solid():
    @lambda_solid
    def noop():
        pass

    assert noop
    assert len(noop.input_defs) == 0
    assert len(noop.output_defs) == 1


def test_one_arg_lambda_solid():
    @lambda_solid
    def one_arg(num):
        return num

    assert one_arg
    assert len(one_arg.input_defs) == 1
    assert one_arg.input_defs[0].name == 'num'
    assert one_arg.input_defs[0].dagster_type.name == 'Any'
    assert len(one_arg.output_defs) == 1


@pytest.mark.skipif(sys.version_info < (3, 6), reason='docstring_parser requires python >= 3.6')
class DefinitionDescriptionFromDocstringTestCase(unittest.TestCase):
    """Class style to avoid having same decorator in all these functions"""

    def test_infer_input_description_from_docstring_rest(self):
        @solid
        def rest(context, hello: str, optional: int = 5):
            """
            :param str hello: hello world param
            :param int optional: optional param, defaults to 5
            """
            pass

        defs = inference.infer_input_definitions_for_solid(rest.name, rest.compute_fn)
        assert len(defs) == 2

        hello_param = defs[0]
        assert hello_param.name == "hello"
        assert hello_param.dagster_type.name == "String"

        optional_param = defs[1]
        assert optional_param.name == "optional"
        assert optional_param.dagster_type.name == "Int"
        assert optional_param.default_value == 5

    def test_infer_descriptions_from_docstring_numpy(self):
        @solid
        def good_numpy(context, hello: str, optional: int = 5):
            """
            Test

            Parameters
            ----------
            hello:
                hello world param
            optional:
                optional param, default 5
            """
            pass

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

    def test_infer_descriptions_from_docstring_google(self):
        @solid
        def good_google(context, hello: str, optional: int = 5):
            """
            Test

            Args:
                hello       (str): hello world param
                optional    (int, optional): optional param. Defaults to 5.
            """
            pass

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

    def test_infer_output_description_from_docstring_numpy(self):
        @solid
        def numpy(context) -> int:
            """

            Returns
            -------
            int
                a number
            """
            pass

        defs = inference.infer_output_definitions("@solid", numpy.name, numpy.compute_fn)
        assert len(defs) == 1
        assert defs[0].name == "result"
        assert defs[0].description == "a number"
        assert defs[0].dagster_type.name == "Int"

    def test_infer_output_description_from_docstring_rest(self):
        @solid
        def rest(context) -> int:
            """
            :return int: a number
            """
            pass

        defs = inference.infer_output_definitions("@solid", rest.name, rest.compute_fn)
        assert len(defs) == 1
        assert defs[0].description == "a number"
        assert defs[0].dagster_type.name == "Int"

    def test_infer_output_description_from_docstring_google(self):
        @solid
        def google(context) -> int:
            """
            Returns:
                int: a number
            """
            pass

        defs = inference.infer_output_definitions("@solid", google.name, google.compute_fn)
        assert len(defs) == 1
        assert defs[0].description == "a number"
        assert defs[0].dagster_type.name == "Int"
