import dagster as dg
import pytest
from dagster._utils.test import wrap_op_in_graph_and_execute


def test_execute_op():
    @dg.op(required_resource_keys={"foo"}, config_schema=int)
    def the_op(context, x: int) -> int:
        return context.resources.foo + x + context.op_config

    result = wrap_op_in_graph_and_execute(
        the_op,
        resources={"foo": 5},
        input_values={"x": 6},
        run_config={"ops": {"the_op": {"config": 7}}},
    )
    assert result.success
    assert result.output_value() == 18
    with pytest.raises(dg.DagsterInvalidDefinitionError):
        wrap_op_in_graph_and_execute(
            the_op,
            resources={"foo": 5},
            input_values={"x": 6, "y": 8},
            run_config={"ops": {"the_op": {"config": 7}}},
        )
