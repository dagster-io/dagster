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
        DagsterInvalidDefinitionError, match="Definition types must align",
    ):

        @composite_solid(output_defs=[OutputDefinition()])
        def _should_fail():
            return dynamic_solid()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=" must be a DynamicOutputDefinition since it is downstream of dynamic output",
    ):

        @composite_solid(output_defs=[OutputDefinition()])
        def _should_fail():
            return echo(dynamic_solid())


def test_fan_in():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Problematic dependency on dynamic output "dynamic_solid:result"',
    ):

        @pipeline
        def _should_fail():
            echo([dynamic_solid()])


def test_multi_direct():
    with pytest.raises(
        DagsterInvalidDefinitionError, match="cannot be downstream of more than one dynamic output",
    ):

        @pipeline
        def _should_fail():
            add(dynamic_solid(), dynamic_solid())


def test_multi_indirect():
    with pytest.raises(
        DagsterInvalidDefinitionError, match="cannot be downstream of more than one dynamic output",
    ):

        @pipeline
        def _should_fail():
            x = echo(dynamic_solid())
            add(dynamic_solid(), x)


def test_multi_composite_out():
    with pytest.raises(
        DagsterInvalidDefinitionError, match="cannot be downstream of more than one dynamic output",
    ):

        @composite_solid(output_defs=[DynamicOutputDefinition()])
        def composed_echo():
            return echo(dynamic_solid())

        @pipeline
        def _should_fail():
            add(composed_echo(), dynamic_solid())


def test_multi_composite_in():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='cannot be downstream of dynamic output "dynamic_solid:result" since input "a" maps to a solid that is already downstream of another dynamic output',
    ):

        @composite_solid
        def composed_add(a):
            add(a, dynamic_solid())

        @pipeline
        def _should_fail():
            y = echo(dynamic_solid())
            composed_add(y)


def test_direct_dep():
    @solid(output_defs=[DynamicOutputDefinition()])
    def dynamic_add(_, x):
        yield DynamicOutput(x + 1, mapping_key="1")
        yield DynamicOutput(x + 2, mapping_key="2")

    @pipeline
    def _is_fine():
        dynamic_add(dynamic_solid())

    with pytest.raises(
        DagsterInvalidDefinitionError, match="cannot be downstream of more than one dynamic output",
    ):

        @pipeline
        def _should_fail():
            echo(dynamic_add(dynamic_solid()))
