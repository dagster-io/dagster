import pytest

from dagster import DagsterInvariantViolationError, op
from dagster._utils.test import execute_op_for_test


def test_execute_op():
    @op(required_resource_keys={"foo"}, config_schema=int)
    def the_op(context, x: int) -> int:
        return context.resources.foo + x + context.op_config

    result = execute_op_for_test(
        the_op,
        resources={"foo": 5},
        input_values={"x": 6},
        run_config={"ops": {"the_op": {"config": 7}}},
    )
    assert result.success
    assert result.output_value() == 18

    with pytest.raises(DagsterInvariantViolationError):
        execute_op_for_test(
            the_op,
            resources={"foo": 5},
            input_values={"x": 6, "y": 8},
            run_config={"ops": {"the_op": {"config": 7}}},
        )
