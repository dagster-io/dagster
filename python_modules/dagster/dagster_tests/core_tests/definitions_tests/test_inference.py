import pytest

from dagster import lambda_solid, solid
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.definitions import inference


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


def test_infer_inputs_from_docstring_numpy_good():
    @solid
    def good_numpy(context, hello, optional=5):
        """
        Test

        Parameters
        ----------
        hello: str
            hello world param
        optional: int, optional
            optional param, default 5
        """
        pass

    defs = inference._infer_input_definitions_from_docstring(good_numpy.name, good_numpy.compute_fn)
    assert len(defs) == 2

    hello_param = defs[0]
    assert hello_param.name == "hello"
    assert hello_param.dagster_type.name == "String"

    optional_param = defs[1]
    assert optional_param.name == "optional"
    assert optional_param.dagster_type.name == "Int"
    assert optional_param.default_value == 5

    @solid
    def nodoc(context):
        pass

    defs2 = inference._infer_input_definitions_from_docstring(nodoc.name, nodoc.compute_fn)
    assert len(defs2) == 0


def test_infer_inputs_from_docstring_numpy_type_dont_exist():
    @solid
    def numpybad(context, hello, invalid, optional=5):
        """
        Test

        Parameters
        ----------
        hello: str
            hello world param
        optional: int, optional
            optional param, default 5
        invalid: DontExist
            tuuti fruitty
        """
        pass

    with pytest.raises(DagsterInvalidDefinitionError) as err:
        inference._infer_input_definitions_from_docstring(numpybad.name, numpybad.compute_fn)

    err_message = str(err.value)
    expected_err = 'Error infering dagster type from docstring param invalid typed as DontExist '
    assert expected_err in err_message


def test_infer_inputs_from_docstring_numpy_invalid_default():
    with pytest.raises(DagsterInvalidDefinitionError) as err:

        @solid
        def numpybad2(context):
            """
            Test

            Parameters
            ----------
            baddefault: int, optional
                optional param, default gfhfg
            """
            pass

        inference._infer_input_definitions_from_docstring(numpybad2.name, numpybad2.compute_fn)

    err_message = str(err.value)
    expected_err = 'Error infering dagster type from docstring param baddefault typed as int '
    assert expected_err in err_message


def test_infer_inputs_from_docstring_google_good():
    @solid
    def good_google(context, hello, optional=5):
        """
        Test

        Args:
            hello       (str): hello world param
            optional    (int, optional): optional param. Defaults to 5.
            optional2   (int, optional): optional param. Defaults to None.
        """
        pass

    defs = inference._infer_input_definitions_from_docstring(
        good_google.name, good_google.compute_fn
    )
    assert len(defs) == 3

    hello_param = defs[0]
    assert hello_param.name == "hello"
    assert hello_param.dagster_type.name == "String"

    optional_param = defs[1]
    assert optional_param.name == "optional"
    assert optional_param.dagster_type.name == "Int"
    assert optional_param.default_value == 5

    optional_param2 = defs[2]
    assert optional_param2.name == "optional2"
    assert optional_param2.dagster_type.name == "Int"

    @solid
    def nodoc(context):
        pass

    defs2 = inference._infer_input_definitions_from_docstring(nodoc.name, nodoc.compute_fn)
    assert len(defs2) == 0


def test_infer_inputs_from_docstring_google_invalid_type():
    @solid
    def bad_google(context, hello, optional=5):
        """
        Test

        Args:
            optional    (int, optional): optional param. Defaults to sdffdsf.
        """
        pass

    with pytest.raises(DagsterInvalidDefinitionError) as err:
        inference._infer_input_definitions_from_docstring(bad_google.name, bad_google.compute_fn)

    err_message = str(err.value)
    expected_err = 'Error infering dagster type from docstring param optional typed as int'
    assert expected_err in err_message


def test_infer_inputs_from_docstring_google_invalid_type():
    @solid
    def bad_google(context, hello, optional=5):
        """
        Test

        Args:
            optional    (typedontexist, optional): optional param. Defaults to 5.
        """
        pass

    with pytest.raises(DagsterInvalidDefinitionError) as err:
        inference._infer_input_definitions_from_docstring(bad_google.name, bad_google.compute_fn)

    err_message = str(err.value)
    expected_err = (
        'Error infering dagster type from docstring param optional typed as typedontexist'
    )
    assert expected_err in err_message


def test_infer_outputs_from_docstring_numpy():
    @solid
    def numpy(context):
        """

        Returns
        -------
        int
            a number
        """
        pass

    defs = inference._infer_output_definitions_from_docstring(numpy.name, numpy.compute_fn)
    assert len(defs) == 1
    assert defs[0].name == "result"
    assert defs[0].description == "a number"
    assert defs[0].dagster_type.name == "Int"


def test_infer_outputs_from_docstring_invalid_type():
    @solid
    def numpy(context):
        """

        Returns
        -------
        typedontexist
            a number
        """
        pass

    with pytest.raises(DagsterInvalidDefinitionError) as err:
        defs = inference._infer_output_definitions_from_docstring(numpy.name, numpy.compute_fn)

    err_message = str(err.value)
    expected_err = (
        'Error inferring Dagster type for return type "typedontexist" from @solid "numpy"'
    )
    assert expected_err in err_message
