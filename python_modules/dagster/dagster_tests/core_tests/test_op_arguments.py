# pylint: disable=unused-argument
import pytest

from dagster import In, op
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._legacy import execute_solid


def test_solid_input_arguments():

    # Solid with no parameters
    @op
    def _no_param():
        pass

    # Solid with an underscore as only parameter; underscore should be treated as context arg
    @op
    def _underscore_param(_):
        pass

    assert "_" not in _underscore_param.input_dict

    # Possible permutations of context arg name
    @op
    def _context_param_underscore(_context):
        pass

    assert "_context" not in _context_param_underscore.input_dict

    @op
    def _context_param_back_underscore(context_):
        pass

    assert "context_" not in _context_param_back_underscore.input_dict

    @op
    def _context_param_regular(context):
        pass

    assert "context" not in _context_param_regular.input_dict

    @op
    def _context_with_inferred_inputs(context, _x, _y):
        pass

    assert "_x" in _context_with_inferred_inputs.input_dict
    assert "_y" in _context_with_inferred_inputs.input_dict
    assert "context" not in _context_with_inferred_inputs.input_dict

    @op
    def _context_with_inferred_invalid_inputs(context, _context, context_):
        pass

    @op
    def _context_with_underscore_arg(context, _):
        pass

    @op(ins={"x": In()})
    def _context_with_input_definitions(context, x):
        pass

    @op
    def _inputs_with_no_context(x, y):
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='"context" is not a valid name in Dagster. It conflicts with a Dagster or python '
        "reserved keyword.",
    ):

        @op
        def _context_after_inputs(x, context):
            pass

    @op(ins={"_": In()})
    def _underscore_after_input_arg(x, _):
        pass

    @op(ins={"_x": In()})
    def _context_partial_inputs(context, _x):
        pass

    @op(ins={"x": In()})
    def _context_partial_inputs(x, y):
        pass

    @op
    def _context_arguments_out_of_order_still_works(_, x, _context):
        pass

    assert "x" in _context_arguments_out_of_order_still_works.input_dict
    assert "_context" in _context_arguments_out_of_order_still_works.input_dict


def test_execution_cases():
    @op
    def underscore_inputs(x, _):
        return x + _

    assert execute_solid(underscore_inputs, input_values={"x": 5, "_": 6}).output_value() == 11

    @op
    def context_underscore_inputs(context, x, _):
        return x + _

    assert (
        execute_solid(context_underscore_inputs, input_values={"x": 5, "_": 6}).output_value() == 11
    )

    @op
    def underscore_context_poorly_named_input(_, x, context_):
        return x + context_

    assert (
        execute_solid(
            underscore_context_poorly_named_input, input_values={"x": 5, "context_": 6}
        ).output_value()
        == 11
    )
