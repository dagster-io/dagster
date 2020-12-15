import pytest
from dagster import DagsterInvalidDefinitionError, composite_solid, pipeline, solid
from dagster.experimental import DynamicOutput, DynamicOutputDefinition


@solid(output_defs=[DynamicOutputDefinition()])
def dynamic_numbers(_):
    yield DynamicOutput(1, mapping_key="1")
    yield DynamicOutput(2, mapping_key="2")


@solid
def echo(_, x):
    return x


def test_must_unpack():
    with pytest.raises(
        DagsterInvalidDefinitionError, match="Dynamic output must be unpacked by invoking forEach"
    ):

        @pipeline
        def _should_fail():
            echo(dynamic_numbers())


def test_must_unpack_composite():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Dynamic output must be unpacked by invoking PLACEHOLDER before mapping",
    ):

        @composite_solid(output_defs=[DynamicOutputDefinition()])
        def _should_fail():
            return dynamic_numbers()
