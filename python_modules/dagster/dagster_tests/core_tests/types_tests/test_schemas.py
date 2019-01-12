import pytest

from dagster import (
    DagsterInvariantViolationError,
    Int,
    SelectorInputSchema,
    SelectorOutputSchema,
    check,
)


def test_selector_input_schema_error():
    class SomeInputSchema(SelectorInputSchema):
        @property
        def schema_cls(self):
            return Int

        def construct_from_selector_value(self, _selector_key, _selector_value):
            check.failed('should not call')

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        SomeInputSchema()

    assert 'You must use a Selector' in str(exc_info.value)


def test_selector_output_schema_error():
    class SomeOutputSchema(SelectorOutputSchema):
        @property
        def schema_cls(self):
            return Int

        def materialize_selector_runtime_value(
            self, _selector_key, _selector_value, _runtime_value
        ):
            check.failed('should not call')

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        SomeOutputSchema()

    assert 'You must use a Selector' in str(exc_info.value)
