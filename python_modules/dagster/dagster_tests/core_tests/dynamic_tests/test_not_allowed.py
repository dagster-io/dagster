import pytest
from dagster import (
    DagsterInvalidDefinitionError,
    OutputDefinition,
    composite_solid,
    pipeline,
    solid,
)
from dagster.experimental import DynamicOutput, DynamicOutputDefinition


@solid(output_defs=[DynamicOutputDefinition()])
def dynamic_solid(_):
    yield DynamicOutput(1, mapping_key="1")
    yield DynamicOutput(2, mapping_key="2")


@solid
def echo(_, x):
    return x


@solid
def add(_, x, y):
    return x + y


def test_composite():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Definition types must align",
    ):

        @composite_solid(output_defs=[OutputDefinition()])
        def _should_fail():
            return dynamic_solid()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="must be a DynamicOutputDefinition since it is downstream of dynamic output",
    ):

        @composite_solid(output_defs=[OutputDefinition()])
        def _should_fail():
            return dynamic_solid().map(echo)


def test_fan_in():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Problematic dependency on dynamic output "dynamic_solid:result"',
    ):

        @pipeline
        def _should_fail():
            numbers = []
            dynamic_solid().map(numbers.append)
            echo(numbers)


def test_multi_direct():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be downstream of more than one dynamic output",
    ):

        @pipeline
        def _should_fail():
            def _add(x):
                dynamic_solid().map(lambda y: add(x, y))

            dynamic_solid().map(_add)


def test_multi_indirect():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be downstream of more than one dynamic output",
    ):

        @pipeline
        def _should_fail():
            def _add(x):
                dynamic_solid().map(lambda y: add(x, y))

            dynamic_solid().map(lambda z: _add(echo(z)))


def test_multi_composite_out():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be downstream of more than one dynamic output",
    ):

        @composite_solid(output_defs=[DynamicOutputDefinition()])
        def composed_echo():
            return dynamic_solid().map(echo)

        @pipeline
        def _should_fail():
            def _complex(item):
                composed_echo().map(lambda y: add(y, item))

            dynamic_solid().map(_complex)


def test_multi_composite_in():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='cannot be downstream of dynamic output "dynamic_solid:result" since input "a" maps to a solid that is already downstream of another dynamic output',
    ):

        @composite_solid
        def composed_add(a):
            dynamic_solid().map(lambda b: add(a, b))

        @pipeline
        def _should_fail():
            dynamic_solid().map(lambda x: composed_add(echo(x)))


def test_direct_dep():
    @solid(output_defs=[DynamicOutputDefinition()])
    def dynamic_add(_, x):
        yield DynamicOutput(x + 1, mapping_key="1")
        yield DynamicOutput(x + 2, mapping_key="2")

    @pipeline
    def _is_fine():
        def _add(item):
            dynamic_add(item)

        dynamic_solid().map(_add)

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be downstream of more than one dynamic output",
    ):

        @pipeline
        def _should_fail():
            def _add_echo(item):
                dynamic_add(item).map(echo)

            dynamic_solid().map(_add_echo)
