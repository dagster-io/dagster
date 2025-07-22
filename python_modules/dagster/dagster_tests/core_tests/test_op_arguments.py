import dagster as dg
import pytest
from dagster._utils.test import wrap_op_in_graph_and_execute


def test_op_input_arguments():
    # Solid with no parameters
    @dg.op
    def _no_param():
        pass

    # Solid with an underscore as only parameter; underscore should be treated as context arg
    @dg.op
    def _underscore_param(_):
        pass

    assert "_" not in _underscore_param.input_dict

    # Possible permutations of context arg name
    @dg.op
    def _context_param_underscore(_context):
        pass

    assert "_context" not in _context_param_underscore.input_dict

    @dg.op
    def _context_param_back_underscore(context_):
        pass

    assert "context_" not in _context_param_back_underscore.input_dict

    @dg.op
    def _context_param_regular(context):
        pass

    assert "context" not in _context_param_regular.input_dict

    @dg.op
    def _context_with_inferred_inputs(context, _x, _y):
        pass

    assert "_x" in _context_with_inferred_inputs.input_dict
    assert "_y" in _context_with_inferred_inputs.input_dict
    assert "context" not in _context_with_inferred_inputs.input_dict

    @dg.op
    def _context_with_inferred_invalid_inputs(context, _context, context_):
        pass

    @dg.op
    def _context_with_underscore_arg(context, _):
        pass

    @dg.op(ins={"x": dg.In()})
    def _context_with_input_definitions(context, x):
        pass

    @dg.op
    def _inputs_with_no_context(x, y):
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            '"context" is not a valid name in Dagster. It conflicts with a Dagster or python '
            "reserved keyword."
        ),
    ):

        @dg.op
        def _context_after_inputs(x, context):
            pass

    @dg.op(ins={"_": dg.In()})
    def _underscore_after_input_arg(x, _):
        pass

    @dg.op(ins={"_x": dg.In()})
    def _context_partial_inputs(context, _x):
        pass

    @dg.op(ins={"x": dg.In()})
    def _context_partial_inputs_2(x, y):
        pass

    @dg.op
    def _context_arguments_out_of_order_still_works(_, x, _context):
        pass

    assert "x" in _context_arguments_out_of_order_still_works.input_dict
    assert "_context" in _context_arguments_out_of_order_still_works.input_dict


def test_execution_cases():
    @dg.op
    def underscore_inputs(x, _):
        return x + _

    assert (
        wrap_op_in_graph_and_execute(
            underscore_inputs, input_values={"x": 5, "_": 6}
        ).output_value()
        == 11
    )

    @dg.op
    def context_underscore_inputs(context, x, _):
        return x + _

    assert (
        wrap_op_in_graph_and_execute(
            context_underscore_inputs, input_values={"x": 5, "_": 6}
        ).output_value()
        == 11
    )

    @dg.op
    def underscore_context_poorly_named_input(_, x, context_):
        return x + context_

    assert (
        wrap_op_in_graph_and_execute(
            underscore_context_poorly_named_input, input_values={"x": 5, "context_": 6}
        ).output_value()
        == 11
    )
