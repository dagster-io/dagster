import pytest
from dagster import (
    Any,
    DagsterInvalidDefinitionError,
    OutputDefinition,
    composite_solid,
    execute_pipeline,
    pipeline,
    solid,
)
from dagster.experimental import DynamicOutput, DynamicOutputDefinition


@solid(output_defs=[DynamicOutputDefinition()])
def dynamic_numbers(_):
    yield DynamicOutput(1, mapping_key="1")
    yield DynamicOutput(2, mapping_key="2")


@solid
def emit_one(_):
    return 1


@solid
def echo(_, x):
    return x


@solid
def add_one(_, x):
    return x + 1


def test_must_unpack():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Dynamic output must be unpacked by invoking map",
    ):

        @pipeline
        def _should_fail():
            echo(dynamic_numbers())


def test_must_unpack_composite():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Dynamic output must be unpacked by invoking map",
    ):

        @composite_solid(output_defs=[DynamicOutputDefinition()])
        def composed():
            return dynamic_numbers()

        @pipeline
        def _should_fail():
            echo(composed())


def test_mapping():
    @pipeline
    def mapping():
        dynamic_numbers().map(add_one).map(echo)

    result = execute_pipeline(mapping)
    assert result.success


def test_mapping_multi():
    def _multi(item):
        a = add_one(item)
        b = add_one(a)
        c = add_one(b)
        return a, b, c

    @pipeline
    def multi_map():
        a, b, c = dynamic_numbers().map(_multi)
        a.map(echo)
        b.map(echo)
        c.map(echo)

    result = execute_pipeline(multi_map)
    assert result.success


def test_composite_multi_out():
    @composite_solid(
        output_defs=[OutputDefinition(Any, "one"), DynamicOutputDefinition(Any, "numbers")]
    )
    def multi_out():
        one = emit_one()
        numbers = dynamic_numbers()
        return {"one": one, "numbers": numbers}

    @pipeline
    def composite_multi():
        one, numbers = multi_out()
        echo(one)
        numbers.map(echo)

    result = execute_pipeline(composite_multi)
    assert result.success
