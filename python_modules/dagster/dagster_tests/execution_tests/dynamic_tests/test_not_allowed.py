import pytest

from dagster import DagsterInvalidDefinitionError, DynamicOut, DynamicOutput, op
from dagster._legacy import DynamicOutputDefinition, OutputDefinition, composite_solid, pipeline


@op(out=DynamicOut())
def dynamic_op():
    yield DynamicOutput(1, mapping_key="1")
    yield DynamicOutput(2, mapping_key="2")


@op(out=DynamicOut())
def dynamic_echo(x):
    yield DynamicOutput(x, mapping_key="echo")


@op
def echo(x):
    return x


@op
def add(x, y):
    return x + y


def test_composite():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Definition types must align",
    ):

        @composite_solid(output_defs=[OutputDefinition()])
        def _should_fail():
            return dynamic_op()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="must be a DynamicOutputDefinition since it is downstream of dynamic output",
    ):

        @composite_solid(output_defs=[OutputDefinition()])
        def _should_fail():
            return dynamic_op().map(echo)


def test_fan_in():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Problematic dependency on dynamic output "dynamic_op:result"',
    ):

        @pipeline
        def _should_fail():
            numbers = []
            dynamic_op().map(numbers.append)
            echo(numbers)


def test_multi_direct():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be downstream of more than one dynamic output",
    ):

        @pipeline
        def _should_fail():
            def _add(x):
                dynamic_op().map(lambda y: add(x, y))

            dynamic_op().map(_add)


def test_multi_indirect():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be downstream of more than one dynamic output",
    ):

        @pipeline
        def _should_fail():
            def _add(x):
                dynamic_op().map(lambda y: add(x, y))

            dynamic_op().map(lambda z: _add(echo(z)))


def test_multi_composite_out():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be downstream of more than one dynamic output",
    ):

        @composite_solid(output_defs=[DynamicOutputDefinition()])
        def composed_echo():
            return dynamic_op().map(echo)

        @pipeline
        def _should_fail():
            def _complex(item):
                composed_echo().map(lambda y: add(y, item))

            dynamic_op().map(_complex)


def test_multi_composite_in():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='cannot be downstream of dynamic output "dynamic_op:result" since input "a" maps to a node that is already downstream of another dynamic output',
    ):

        @composite_solid
        def composed_add(a):
            dynamic_op().map(lambda b: add(a, b))

        @pipeline
        def _should_fail():
            dynamic_op().map(lambda x: composed_add(echo(x)))


def test_multi_composite_in_2():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='cannot be downstream of dynamic output "dynamic_op:result" since input "a" maps to a node that is already downstream of another dynamic output',
    ):

        @composite_solid
        def composed_add(a):
            dynamic_op().map(lambda b: add(a, b))

        @composite_solid
        def indirect(a):
            composed_add(a)

        @pipeline
        def _should_fail():
            dynamic_op().map(lambda x: indirect(echo(x)))


def test_multi_composite_in_3():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='cannot be downstream of dynamic output "dynamic_op:result" since input "a" maps to a node that is already downstream of another dynamic output',
    ):

        @composite_solid
        def composed(a):
            dynamic_echo(a).map(echo)

        @pipeline
        def _should_fail():
            dynamic_op().map(composed)


def test_multi_composite_in_4():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='cannot be downstream of dynamic output "dynamic_op:result" since input "a" maps to a node that is already downstream of another dynamic output',
    ):

        @composite_solid
        def composed(a):
            dynamic_echo(a).map(echo)

        @composite_solid
        def indirect(a):
            composed(a)

        @pipeline
        def _should_fail():
            dynamic_op().map(indirect)


def test_direct_dep():
    @op(out=DynamicOut())
    def dynamic_add(_, x):
        yield DynamicOutput(x + 1, mapping_key="1")
        yield DynamicOutput(x + 2, mapping_key="2")

    @pipeline
    def _is_fine():
        def _add(item):
            dynamic_add(item)

        dynamic_op().map(_add)

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be downstream of more than one dynamic output",
    ):

        @pipeline
        def _should_fail():
            def _add_echo(item):
                dynamic_add(item).map(echo)

            dynamic_op().map(_add_echo)

    @pipeline
    def _is_fine():
        dynamic_op().map(dynamic_add)

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be downstream of more than one dynamic output",
    ):

        @pipeline
        def _should_fail():
            echo(dynamic_op().map(dynamic_add).collect())


def test_collect_and_dep():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot both collect over dynamic output",
    ):

        @pipeline
        def _bad():
            x = dynamic_op()
            x.map(lambda y: add(y, x.collect()))

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="cannot be both downstream of dynamic output",
    ):

        @pipeline
        def _bad_other():
            x = dynamic_op()
            x.map(lambda y: add(x.collect(), y))
